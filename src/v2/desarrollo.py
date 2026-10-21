"""Etapa de DESARROLLO: validacion cruzada, seleccion de modelo, umbral y diagnosticos.

Solo lee data/v2/features_desarrollo_*.csv (meses t <= 2025-12). No tiene ninguna ruta de acceso a
datos posteriores: verificar_sello.py comprueba que este modulo no referencia la puerta de la prueba.
Criterio de seleccion declarado en docs/protocolo (ver docstring de src/protocolo.py): menor MAE
medio de CV, regla de 1 error estandar, desempate por menor complejidad, y debe superar las bases.
"""
import json

import numpy as np
import pandas as pd

from . import config as C
from .nucleo import *  # noqa: F401,F403


def cargar(task):
    d = pd.read_csv(C.DATA / f"features_desarrollo_{task}.csv", parse_dates=["Fecha"])
    return d.sort_values(["Fecha", "Especie"]).reset_index(drop=True)


def dev(task):
    t = TASKS[task]
    d = cargar(task)
    y = d[t["y"]].to_numpy()
    X = d[columnas(task)]
    meses = mes_idx(d["Fecha"])
    cv = splits(meses, t["emb"])
    print(f"\n=== {task}: {len(d)} filas de entrenamiento, {len(cv)} pliegues, embargo {t['emb']} meses")
    desb = pd.DataFrame({"clase": ["regular", "estable", "optimista"], "n": np.bincount(clase(y), minlength=3)})
    desb["pct"] = desb.n / desb.n.sum() * 100
    desb.to_csv(C.REP / f"desbalance_{task}.csv", index=False)
    print(desb.round(1).to_string(index=False))
    pd.DataFrame([{"pliegue": i, "n_train": len(tr), "n_test": len(te),
                   "regular": int((clase(y[te]) == 0).sum()), "estable": int((clase(y[te]) == 1).sum()),
                   "optimista": int((clase(y[te]) == 2).sum()),
                   "periodo": f"{d.Fecha.iloc[te].min():%Y-%m} a {d.Fecha.iloc[te].max():%Y-%m}"} for i, (tr, te) in enumerate(cv)]
                 ).to_csv(C.REP / f"pliegues_{task}.csv", index=False)

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
    pd.DataFrame(rows).sort_values(["modelo", "MAE_cv"]).to_csv(C.REP / f"cv_grid_{task}.csv", index=False)

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
    comp.to_csv(C.REP / f"comparacion_cv_{task}.csv", index=False)
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
    pd.DataFrame(cur).to_csv(C.REP / f"umbral_{task}.csv", index=False)
    cdf = pd.DataFrame(cur)
    m_star = float(cdf.assign(a=cdf.m_pp.abs()).sort_values(["costo_medio", "a"]).m_pp.iloc[0]) / 100

    # --- efecto de la ponderacion (balance) sobre el modelo final
    efecto = []
    for bal in (False, True):
        pipe = pipeline(final, task, bal, **mf["params"])
        po, fo = oof(pipe, d, task, cv)
        efecto.append({"balance": bal, **met(y, po), **{k: v for k, v in met_clase(y, po, 0.0).items() if k != "matriz"}})
    pd.DataFrame(efecto).to_csv(C.REP / f"efecto_balance_{task}.csv", index=False)

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
    pd.DataFrame(sens).to_csv(C.REP / f"sensibilidad_validacion_{task}.csv", index=False)

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
    pd.DataFrame(lc).to_csv(C.REP / f"curva_aprendizaje_{task}.csv", index=False)
    print(pd.DataFrame(lc).round(2).to_string(index=False))

    # --- curva de regularizacion del modelo final (si tiene alpha)
    if "alpha" in mf["params"]:
        cr = []
        for a in GRID[final]["alpha"] if "alpha" in GRID[final] else []:
            pr = {**mf["params"], "alpha": a}
            po, fo = oof(pipeline(final, task, mf["balance"], **pr), d, task, cv)
            m_tr = clone(pipeline(final, task, mf["balance"], **pr)).fit(X, y)
            cr.append({"alpha": a, "MAE_cv": float(np.abs(po - y).mean() * 100), "MAE_entrenamiento": float(np.abs(m_tr.predict(X) - y).mean() * 100)})
        pd.DataFrame(cr).to_csv(C.REP / f"curva_regularizacion_{task}.csv", index=False)

    # --- errores por especie en OOF (estabilidad)
    pe = pd.DataFrame({"Especie": d.Especie, "err": np.abs(oofs[final] - y) * 100}).groupby("Especie").err.agg(["mean", "std"]).reset_index()
    pe.to_csv(C.REP / f"oof_por_especie_{task}.csv", index=False)
    pd.DataFrame({"Fecha": d.Fecha, "Especie": d.Especie, "real": y, "oof": oofs[final], "pliegue": fold}).to_csv(C.REP / f"oof_{task}.csv", index=False)

    sel = dict(task=task, final=final, nombre=NOMBRES[final], params=mf["params"], balance=mf["balance"], elegibles=elegibles,
               mejores=mejores, MAE_cv_final=mf["MAE_cv"], sd_cv_final=mf["sd"], base_B1=b1, base_B2=b2, supera_lineas_base=supera,
               m_umbral=m_star, n_pliegues=len(cv), embargo=t["emb"], n_train=len(d))
    (C.REP / f"seleccion_{task}.json").write_text(json.dumps(sel, indent=1, default=float))
    print(f"  umbral recomendado: restar m = {m_star * 100:+.1f} pp antes de clasificar")
    return sel


if __name__ == "__main__":
    C.REP.mkdir(parents=True, exist_ok=True)
    for k in TASKS:
        dev(k)
