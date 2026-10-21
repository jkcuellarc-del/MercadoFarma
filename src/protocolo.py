"""Protocolo experimental riguroso: Pipeline, validacion cruzada, prueba consultada una vez.

PROTOCOLO DECLARADO ANTES DE EJECUTAR (no se modifica despues de ver resultados)
--------------------------------------------------------------------------------
Particion (por mes t de la ventana de 12 meses moviles, antes de cualquier transformacion):
  entrenamiento : mercado 2021-12..2025-12 | laboratorio 2023-12..2025-12
  prueba        : 2026-01..2026-06 (ventanas con datos 100% observados)
  excluido      : 2026-07..2026-12 (incluyen meses completados con un modelo estacional)
Flujo: Pipeline(ColumnTransformer[StandardScaler en continuas, one-hot de especie sin escalar]
       -> modelo). El escalador se ajusta dentro de cada pliegue, solo con su entrenamiento.
Validacion cruzada: K-fold por bloques de 6 meses con purga (embargo) de meses a cada lado del
  bloque, porque las ventanas de 12 meses se solapan. Embargo: 6 meses (mercado), 3 (laboratorio,
  historia mas corta). Todos los modelos usan exactamente los mismos pliegues.
Desbalance: las clases de escenario (regular <8%, estable 8-15%, optimista >15%) estan
  desbalanceadas. Se prueba ponderar las muestras por la frecuencia inversa de su clase,
  calculada dentro de cada pliegue de entrenamiento (hiperparametro balance en {falso, verdadero}).
Lineas base: (B1) crecimiento observado 12 meses antes; (B2) promedio historico de la especie.
Familias: lineal regularizada (Ridge por especie, Ridge comun, Elastic Net), bagging
  (Random Forest), boosting (Gradient Boosting). Hiperparametros: GridSearch con la CV anterior,
  metrica MAE.
Criterio de seleccion final (declarado): (1) el mejor de cada familia se define por MAE medio de CV;
  (2) son elegibles los que quedan a menos de 1 error estandar del mejor; (3) entre ellos se elige
  el de menor complejidad (Ridge por especie < Ridge/Elastic Net comun < Random Forest < Gradient
  Boosting; el simulador necesita efectos propios por especie y respuesta suave); (4) debe superar
  ambas lineas base en CV; si no, se declara que el modelo no agrega valor.
Umbral de decision: el escenario se asigna con las reglas 8% y 15% tras restar un descuento de
  prudencia m a la prediccion. m se elige con las predicciones fuera de pliegue (OOF) para minimizar
  el costo esperado. Costo (supuesto a validar con el negocio): pronosticar un escenario por encima
  del real cuesta 2 por nivel de diferencia; por debajo, 1 por nivel.
Prueba: se evalua UNA sola vez (`python src/protocolo.py prueba`), y queda un candado en
  reports/protocolo/prueba_consultada.lock.

Uso:  python src/protocolo.py dev      # CV, seleccion, umbral, diagnosticos (sin tocar la prueba)
      python src/protocolo.py prueba   # evaluacion unica en prueba y reajuste final
"""
import json
import sys
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
PROC, MODELS, OUT = ROOT / "data" / "processed", ROOT / "models", ROOT / "reports" / "protocolo"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 0
ESPS = ["CA", "Cattle", "Poultry", "Swine"]
ONEHOT = [f"esp_{e}" for e in ESPS]
CONT_M = ["ipc_yoy", "ipc_yoy_CA", "pib", "pib_agro", "smmlv", "var_leche", "var_res", "var_cerdo", "var_huevo", "var_pollo"]
TASKS = {
    "mercado": dict(y="y_mercado", cont=CONT_M, ini="2021-12-01", emb=6, holdout=12, sizes=[6, 12, 18, 24, 30, 36]),
    "lab": dict(y="y_lab", cont=CONT_M + ["y_mercado"], ini="2023-12-01", emb=3, holdout=6, sizes=[4, 8, 12, 16]),
}
TRAIN_END, TEST_INI, TEST_END = "2025-12-01", "2026-01-01", "2026-06-01"
BLOCK = 6
COMPLEJIDAD = {"ridge_esp": 0, "ridge": 1, "enet": 1, "rf": 2, "gbm": 3}
NOMBRES = {"ridge_esp": "Ridge por especie", "ridge": "Ridge común", "enet": "Elastic Net", "rf": "Random Forest",
           "gbm": "Gradient Boosting"}


# ---------------------------------------------------------------- utilidades
def clase(y):
    return np.digitize(np.asarray(y, dtype=float), [0.08, 0.15])  # 0 regular, 1 estable, 2 optimista


def costo(real, pred):
    d = np.asarray(pred) - np.asarray(real)
    return np.where(d > 0, 2.0 * d, -1.0 * d)


def mes_idx(f):
    f = pd.to_datetime(f)
    return (f.dt.year * 12 + f.dt.month).to_numpy()


def cargar(task, parte):
    t = TASKS[task]
    d = pd.read_csv(PROC / f"model_{task}.csv", parse_dates=["Fecha"])
    # crecimiento observado 12 meses antes (solo pasado de t): se calcula antes de filtrar la particion
    k = d[["Especie", "Fecha", t["y"]]].assign(Fecha=lambda x: x.Fecha + pd.DateOffset(years=1))
    d = d.merge(k.rename(columns={t["y"]: "lag12"}), on=["Especie", "Fecha"], how="left")
    if parte == "train":
        d = d[(d.Fecha >= t["ini"]) & (d.Fecha <= TRAIN_END)]
    elif parte == "prueba":
        d = d[(d.Fecha >= TEST_INI) & (d.Fecha <= TEST_END)]
    else:
        raise ValueError(parte)
    d = d.sort_values(["Fecha", "Especie"]).reset_index(drop=True)
    return d


class PerEspecie(BaseEstimator, RegressorMixin):
    """Un Ridge por especie; la especie se lee de las 4 ultimas columnas (one-hot)."""

    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, y, sample_weight=None):
        X, y = np.asarray(X), np.asarray(y, dtype=float)
        w = None if sample_weight is None else np.asarray(sample_weight)
        sp = X[:, -4:].argmax(1)
        self.models_ = {k: Ridge(alpha=self.alpha).fit(X[sp == k][:, :-4], y[sp == k],
                                                       sample_weight=None if w is None else w[sp == k])
                        for k in np.unique(sp)}
        self.mean_ = np.average(y, weights=w)
        return self

    def predict(self, X):
        X = np.asarray(X)
        sp = X[:, -4:].argmax(1)
        p = np.full(len(X), self.mean_)
        for k, m in self.models_.items():
            p[sp == k] = m.predict(X[sp == k][:, :-4])
        return p


class Balanceado(BaseEstimator, RegressorMixin):
    """Pondera cada muestra por la frecuencia inversa de su clase de escenario. Los pesos se
    calculan dentro de fit, es decir solo con el entrenamiento del pliegue."""

    def __init__(self, est=None, balance=False):
        self.est = est
        self.balance = balance

    def fit(self, X, y):
        self.est_ = clone(self.est)
        y = np.asarray(y, dtype=float)
        if self.balance:
            c = clase(y)
            n = np.bincount(c, minlength=3).astype(float)
            self.est_.fit(X, y, sample_weight=len(y) / (3.0 * n[c]))
        else:
            self.est_.fit(X, y)
        return self

    def predict(self, X):
        return self.est_.predict(X)


EST = {
    "ridge_esp": lambda: PerEspecie(),
    "ridge": lambda: Ridge(),
    "enet": lambda: ElasticNet(max_iter=50000),
    "rf": lambda: RandomForestRegressor(n_estimators=300, random_state=SEED, n_jobs=1),
    "gbm": lambda: GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, subsample=0.8, random_state=SEED),
}
GRID = {
    "ridge_esp": {"alpha": [0.1, 1, 10, 100, 1000]},
    "ridge": {"alpha": [0.1, 1, 10, 100, 1000]},
    "enet": {"alpha": [0.001, 0.01, 0.1], "l1_ratio": [0.2, 0.5, 0.8]},
    "rf": {"max_depth": [2, 3, 5], "min_samples_leaf": [3, 5, 10]},
    "gbm": {"max_depth": [1, 2, 3], "min_samples_leaf": [3, 8]},
}


def pipeline(kind, task, balance=False, **params):
    cont = TASKS[task]["cont"]
    pre = ColumnTransformer([("num", StandardScaler(), cont), ("esp", "passthrough", ONEHOT)])
    p = Pipeline([("pre", pre), ("model", Balanceado(EST[kind](), balance))])
    p.set_params(**{f"model__est__{k}": v for k, v in params.items()})
    return p


def columnas(task):
    return TASKS[task]["cont"] + ONEHOT


def splits(meses, emb, block=BLOCK):
    """K-fold por bloques de `block` meses con purga de `emb` meses a cada lado."""
    um = np.unique(meses)
    out = []
    for b in np.array_split(um, int(np.ceil(len(um) / block))):
        te = np.where(np.isin(meses, b))[0]
        tr = np.where((meses < b.min() - emb) | (meses > b.max() + emb))[0]
        if len(tr) >= 24:
            out.append((tr, te))
    return out


def met(y, p):
    e = np.asarray(p) - np.asarray(y)
    return {"MAE_pp": float(np.abs(e).mean() * 100), "RMSE_pp": float(np.sqrt((e ** 2).mean()) * 100),
            "sesgo_pp": float(e.mean() * 100)}


def met_clase(y, p, m=0.0):
    cy, cp = clase(y), clase(np.asarray(p) - m)
    cm = confusion_matrix(cy, cp, labels=[0, 1, 2])
    rec = cm.diagonal() / np.maximum(cm.sum(1), 1)
    return {"acierto": float((cy == cp).mean()), "F1_macro": float(f1_score(cy, cp, average="macro", labels=[0, 1, 2], zero_division=0)),
            "recall_regular": float(rec[0]) if cm[0].sum() else None, "recall_estable": float(rec[1]) if cm[1].sum() else None,
            "recall_optimista": float(rec[2]) if cm[2].sum() else None,
            "costo_medio": float(costo(cy, cp).mean()), "matriz": cm.tolist()}


def oof(pipe, d, task, cv):
    y = d[TASKS[task]["y"]].to_numpy()
    X = d[columnas(task)]
    p = np.full(len(d), np.nan)
    fold = np.full(len(d), -1)
    for i, (tr, te) in enumerate(cv):
        m = clone(pipe).fit(X.iloc[tr], y[tr])
        p[te] = m.predict(X.iloc[te])
        fold[te] = i
    return p, fold


def mae_pliegues(y, p, fold, mask=None):
    out = []
    for i in sorted(set(fold[fold >= 0])):
        s = (fold == i) if mask is None else (fold == i) & mask
        if s.sum():
            out.append(float(np.abs(p[s] - y[s]).mean() * 100))
    return out


# ---------------------------------------------------------------- etapa dev
def dev(task):
    t = TASKS[task]
    d = cargar(task, "train")
    y = d[t["y"]].to_numpy()
    X = d[columnas(task)]
    meses = mes_idx(d["Fecha"])
    cv = splits(meses, t["emb"])
    print(f"\n=== {task}: {len(d)} filas de entrenamiento, {len(cv)} pliegues, embargo {t['emb']} meses")
    desb = pd.DataFrame({"clase": ["regular", "estable", "optimista"], "n": np.bincount(clase(y), minlength=3)})
    desb["pct"] = desb.n / desb.n.sum() * 100
    desb.to_csv(OUT / f"desbalance_{task}.csv", index=False)
    print(desb.round(1).to_string(index=False))
    pd.DataFrame([{"pliegue": i, "n_train": len(tr), "n_test": len(te),
                   "regular": int((clase(y[te]) == 0).sum()), "estable": int((clase(y[te]) == 1).sum()),
                   "optimista": int((clase(y[te]) == 2).sum()),
                   "periodo": f"{d.Fecha.iloc[te].min():%Y-%m} a {d.Fecha.iloc[te].max():%Y-%m}"} for i, (tr, te) in enumerate(cv)]
                 ).to_csv(OUT / f"pliegues_{task}.csv", index=False)

    # --- lineas base (mismos pliegues)
    base = {}
    pb2 = np.full(len(d), np.nan)
    fold = np.full(len(d), -1)
    for i, (tr, te) in enumerate(cv):
        mu = d.iloc[tr].groupby("Especie")[t["y"]].mean()
        pb2[te] = d.Especie.iloc[te].map(mu).to_numpy()
        fold[te] = i
    has_lag = d.lag12.notna().to_numpy()
    base["B2_media_especie"] = dict(p=pb2, folds=mae_pliegues(y, pb2, fold))
    pb1 = d.lag12.to_numpy()
    base["B1_crecimiento_hace_12m"] = dict(p=pb1, folds=mae_pliegues(y, np.nan_to_num(pb1), fold, mask=has_lag))

    # --- busqueda de hiperparametros (misma CV) para cada familia, con y sin balance
    rows, mejores, oofs = [], {}, {}
    for kind in EST:
        grid = {f"model__est__{k}": v for k, v in GRID[kind].items()}
        grid["model__balance"] = [False, True]
        gs = GridSearchCV(pipeline(kind, task), grid, cv=cv, scoring="neg_mean_absolute_error", refit=False, n_jobs=1)
        gs.fit(X, y)
        r = gs.cv_results_
        for j in range(len(r["params"])):
            sc = -np.array([r[f"split{i}_test_score"][j] for i in range(len(cv))]) * 100
            rows.append({"modelo": kind, "params": json.dumps({k.replace("model__", ""): v for k, v in r["params"][j].items()}),
                         "balance": r["params"][j]["model__balance"], "MAE_cv": sc.mean(), "sd": sc.std(ddof=1)})
        j = int(np.argmax(r["mean_test_score"]))
        bp = r["params"][j]
        sc = -np.array([r[f"split{i}_test_score"][j] for i in range(len(cv))]) * 100
        mejores[kind] = dict(params={k.replace("model__est__", ""): v for k, v in bp.items() if k.startswith("model__est__")},
                             balance=bool(bp["model__balance"]), folds=sc.tolist(), MAE_cv=float(sc.mean()),
                             sd=float(sc.std(ddof=1)), se=float(sc.std(ddof=1) / np.sqrt(len(sc))))
        pipe = pipeline(kind, task, mejores[kind]["balance"], **mejores[kind]["params"])
        oofs[kind], _ = oof(pipe, d, task, cv)
        print(f"  {kind:10s} MAE_cv={sc.mean():5.2f} ± {sc.std(ddof=1):4.2f}  {mejores[kind]['params']} balance={mejores[kind]['balance']}")
    pd.DataFrame(rows).sort_values(["modelo", "MAE_cv"]).to_csv(OUT / f"cv_grid_{task}.csv", index=False)

    # --- comparacion en subconjunto con lag12 disponible (justo para B1)
    comp = []
    for k, v in mejores.items():
        comp.append({"modelo": k, "MAE_cv": v["MAE_cv"], "sd": v["sd"], "MAE_oof_global": float(np.abs(oofs[k] - y).mean() * 100),
                     "MAE_oof_subconjunto_lag": float(np.abs(oofs[k] - y)[has_lag].mean() * 100)})
    for k, v in base.items():
        sub = has_lag if k.startswith("B1") else np.ones(len(d), bool)
        comp.append({"modelo": k, "MAE_cv": float(np.mean(v["folds"])), "sd": float(np.std(v["folds"], ddof=1)),
                     "MAE_oof_global": float(np.abs(np.nan_to_num(v["p"]) - y)[sub].mean() * 100),
                     "MAE_oof_subconjunto_lag": float(np.abs(np.nan_to_num(v["p"]) - y)[has_lag].mean() * 100)})
    comp = pd.DataFrame(comp)
    comp.to_csv(OUT / f"comparacion_cv_{task}.csv", index=False)
    print(comp.round(2).to_string(index=False))

    # --- seleccion segun el criterio declarado
    mejor = min(mejores.values(), key=lambda v: v["MAE_cv"])
    elegibles = [k for k, v in mejores.items() if v["MAE_cv"] <= mejor["MAE_cv"] + mejor["se"]]
    final = sorted(elegibles, key=lambda k: (COMPLEJIDAD[k], mejores[k]["MAE_cv"]))[0]
    b1 = float(np.abs(pb1 - y)[has_lag].mean() * 100)
    b2 = float(np.abs(pb2 - y).mean() * 100)
    mf = mejores[final]
    sub_final = float(np.abs(oofs[final] - y)[has_lag].mean() * 100)
    supera = bool(mf["MAE_cv"] < b2 and sub_final < b1)
    print(f"  elegibles (<=1 SE del mejor): {elegibles} -> FINAL: {final}; supera B1/B2: {supera} (B1={b1:.2f}, B2={b2:.2f})")

    # --- umbral de decision (descuento de prudencia m) con OOF del modelo final
    ms = np.round(np.arange(-0.02, 0.0601, 0.005), 4)
    cur = [{"m_pp": m * 100, **{k: v for k, v in met_clase(y, oofs[final], m).items() if k != "matriz"}} for m in ms]
    pd.DataFrame(cur).to_csv(OUT / f"umbral_{task}.csv", index=False)
    cdf = pd.DataFrame(cur)
    m_star = float(cdf.assign(a=cdf.m_pp.abs()).sort_values(["costo_medio", "a"]).m_pp.iloc[0]) / 100

    # --- efecto de la ponderacion (balance) sobre el modelo final
    efecto = []
    for bal in (False, True):
        pipe = pipeline(final, task, bal, **mf["params"])
        po, fo = oof(pipe, d, task, cv)
        efecto.append({"balance": bal, **met(y, po), **{k: v for k, v in met_clase(y, po, 0.0).items() if k != "matriz"}})
    pd.DataFrame(efecto).to_csv(OUT / f"efecto_balance_{task}.csv", index=False)

    # --- sensibilidad al embargo y CV estratificada (optimismo de la CV)
    sens = []
    pipe = pipeline(final, task, mf["balance"], **mf["params"])
    for emb in (0, 3, 6, 11):
        cv2 = splits(meses, emb)
        po, fo = oof(pipe, d, task, cv2)
        sens.append({"validacion": f"por bloques, embargo {emb} m", "MAE_pp": float(np.abs(po - y).mean() * 100),
                     "n_train_medio": float(np.mean([len(a) for a, _ in cv2]))})
    try:
        sgk = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
        cv3 = list(sgk.split(X, clase(y), groups=d.Fecha.dt.year.to_numpy()))
        po, _ = oof(pipe, d, task, cv3)
        sens.append({"validacion": "estratificada por clase, grupos por año (sin purga)", "MAE_pp": float(np.abs(po - y).mean() * 100),
                     "n_train_medio": float(np.mean([len(a) for a, _ in cv3]))})
    except Exception as ex:  # clase rara que no cabe en todos los grupos
        sens.append({"validacion": f"estratificada no viable: {ex}", "MAE_pp": None, "n_train_medio": None})
    pd.DataFrame(sens).to_csv(OUT / f"sensibilidad_validacion_{task}.csv", index=False)

    # --- curva de aprendizaje (sesgo / varianza)
    um = np.sort(np.unique(meses))
    ho = um[-t["holdout"]:]
    pool = um[: len(um) - t["holdout"]]
    lc = []
    for n in t["sizes"]:
        if n > len(pool):
            continue
        tr = np.where(np.isin(meses, pool[:n]))[0]
        te = np.where(np.isin(meses, ho))[0]
        m = clone(pipe).fit(X.iloc[tr], y[tr])
        lc.append({"meses_entrenamiento": n, "filas": len(tr), "MAE_entrenamiento": float(np.abs(m.predict(X.iloc[tr]) - y[tr]).mean() * 100),
                   "MAE_retenido": float(np.abs(m.predict(X.iloc[te]) - y[te]).mean() * 100)})
    pd.DataFrame(lc).to_csv(OUT / f"curva_aprendizaje_{task}.csv", index=False)
    print(pd.DataFrame(lc).round(2).to_string(index=False))

    # --- curva de regularizacion del modelo final (si tiene alpha)
    if "alpha" in mf["params"]:
        cr = []
        for a in GRID[final]["alpha"] if "alpha" in GRID[final] else []:
            pr = {**mf["params"], "alpha": a}
            po, fo = oof(pipeline(final, task, mf["balance"], **pr), d, task, cv)
            m_tr = clone(pipeline(final, task, mf["balance"], **pr)).fit(X, y)
            cr.append({"alpha": a, "MAE_cv": float(np.abs(po - y).mean() * 100), "MAE_entrenamiento": float(np.abs(m_tr.predict(X) - y).mean() * 100)})
        pd.DataFrame(cr).to_csv(OUT / f"curva_regularizacion_{task}.csv", index=False)

    # --- errores por especie en OOF (estabilidad)
    pe = pd.DataFrame({"Especie": d.Especie, "err": np.abs(oofs[final] - y) * 100}).groupby("Especie").err.agg(["mean", "std"]).reset_index()
    pe.to_csv(OUT / f"oof_por_especie_{task}.csv", index=False)
    pd.DataFrame({"Fecha": d.Fecha, "Especie": d.Especie, "real": y, "oof": oofs[final], "pliegue": fold}).to_csv(OUT / f"oof_{task}.csv", index=False)

    sel = dict(task=task, final=final, nombre=NOMBRES[final], params=mf["params"], balance=mf["balance"], elegibles=elegibles,
               mejores=mejores, MAE_cv_final=mf["MAE_cv"], sd_cv_final=mf["sd"], base_B1=b1, base_B2=b2, supera_lineas_base=supera,
               m_umbral=m_star, n_pliegues=len(cv), embargo=t["emb"], n_train=len(d))
    (OUT / f"seleccion_{task}.json").write_text(json.dumps(sel, indent=1, default=float))
    print(f"  umbral recomendado: restar m = {m_star * 100:+.1f} pp antes de clasificar")
    return sel


# ---------------------------------------------------------------- etapa prueba (una sola vez)
def prueba():
    lock = OUT / "prueba_consultada.lock"
    if lock.exists() and "--force" not in sys.argv:
        sys.exit(f"La prueba ya fue consultada ({lock.read_text().strip()}). Protocolo: una sola consulta.")
    sels = {k: json.loads((OUT / f"seleccion_{k}.json").read_text()) for k in TASKS}
    res, preds, fit_m = {}, [], {}
    for task in ("mercado", "lab"):
        sel, t = sels[task], TASKS[task]
        tr, te = cargar(task, "train"), cargar(task, "prueba")
        pipe = pipeline(sel["final"], task, sel["balance"], **sel["params"]).fit(tr[columnas(task)], tr[t["y"]])
        if task == "mercado":
            fit_m = pipe
        Xte = te[columnas(task)].copy()
        y = te[t["y"]].to_numpy()
        p = pipe.predict(Xte)
        r = {"modelo_final": sel["nombre"], "n": len(te), **met(y, p), **{k: v for k, v in met_clase(y, p, sel["m_umbral"]).items() if k != "matriz"},
             "matriz_con_umbral": met_clase(y, p, sel["m_umbral"])["matriz"],
             "sin_umbral": {k: v for k, v in met_clase(y, p, 0.0).items() if k != "matriz"}}
        mu = tr.groupby("Especie")[t["y"]].mean()
        pb2 = te.Especie.map(mu).to_numpy()
        r["B2_media_especie"] = {**met(y, pb2), **{k: v for k, v in met_clase(y, pb2, 0.0).items() if k != "matriz"}}
        ok = te.lag12.notna().to_numpy()
        r["B1_crecimiento_hace_12m"] = {**met(y[ok], te.lag12.to_numpy()[ok]), "n": int(ok.sum())}
        r["modelo_final_en_subconjunto_lag"] = {**met(y[ok], p[ok]), "n": int(ok.sum())}
        r["por_especie"] = {e: met(y[(te.Especie == e).to_numpy()], p[(te.Especie == e).to_numpy()]) for e in ESPS}
        if task == "lab":  # cadena realista: el mercado entra como proyeccion del modelo de mercado
            tm = cargar("mercado", "prueba")
            ph = pd.Series(fit_m.predict(tm[columnas("mercado")]), index=pd.MultiIndex.from_frame(tm[["Fecha", "Especie"]]))
            Xr = te[columnas(task)].copy()
            Xr["y_mercado"] = ph.reindex(pd.MultiIndex.from_frame(te[["Fecha", "Especie"]])).to_numpy()
            pr = pipe.predict(Xr)
            r["con_mercado_proyectado"] = {**met(y, pr), **{k: v for k, v in met_clase(y, pr, sel["m_umbral"]).items() if k != "matriz"}}
            p = pr
        res[task] = r
        preds.append(pd.DataFrame({"tarea": task, "Fecha": te.Fecha, "Especie": te.Especie, "real": y, "pred": p,
                                   "B2": pb2, "B1": te.lag12.to_numpy()}))
    (OUT / "prueba_resultados.json").write_text(json.dumps(res, indent=1, default=float))
    pd.concat(preds).to_csv(OUT / "prueba_predicciones.csv", index=False)
    lock.write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ("modelo_final", "n", "MAE_pp", "sesgo_pp", "acierto", "F1_macro", "costo_medio", "B2_media_especie", "B1_crecimiento_hace_12m", "con_mercado_proyectado")} for k, v in res.items()}, indent=1, default=float))

    # reajuste final para despliegue: entrenamiento + prueba (todo lo observado hasta junio 2026)
    for task in ("mercado", "lab"):
        sel, t = sels[task], TASKS[task]
        d = pd.concat([cargar(task, "train"), cargar(task, "prueba")])
        pipe = pipeline(sel["final"], task, sel["balance"], **sel["params"]).fit(d[columnas(task)], d[t["y"]])
        joblib.dump({"pipeline": pipe, "columnas": columnas(task), "seleccion": sel}, MODELS / f"pipeline_final_{task}.joblib")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "dev"
    if modo == "dev":
        for k in TASKS:
            dev(k)
    elif modo == "prueba":
        prueba()
