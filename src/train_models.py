"""Entrena, compara y elige modelos para el crecimiento de mercado y laboratorio.

Candidatos: linea base (crecimiento de hace 12 meses), Ridge, Elastic Net, Random Forest,
Gradient Boosting y Ridge por especie. Los hiperparametros se eligen en validacion (2025)
y el desempeno se confirma en prueba (enero-junio 2026), que no se usa para ajustar nada.
El modelo elegido se reentrena con entrenamiento + validacion + prueba.

Salidas: reports/comparacion_modelos.csv, reports/predicciones_<mercado|lab>.csv,
         models/final_<mercado|lab>.joblib, reports/escenario_base_2027.csv
"""
import itertools
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import ElasticNet, Ridge

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
PROC, MODELS, REP = ROOT / "data" / "processed", ROOT / "models", ROOT / "reports"
REP.mkdir(exist_ok=True)
ESPECIES = ["CA", "Cattle", "Poultry", "Swine"]
SEED = 0


def escenario(y):
    return pd.cut(y, [-np.inf, .08, .15, np.inf], labels=["regular", "estable", "optimista"], right=False)


def metrics(y, p):
    e = p - y
    acc = (escenario(pd.Series(p)).astype(str).to_numpy() == escenario(pd.Series(y)).astype(str).to_numpy()).mean()
    return {"MAE_pp": np.abs(e).mean() * 100, "RMSE_pp": np.sqrt((e ** 2).mean()) * 100,
            "sesgo_pp": e.mean() * 100, "acierto_escenario": acc}


def lag12(d, target):
    """Crecimiento observado 12 meses antes (linea base)."""
    k = d[["Especie", "Fecha", target]].copy()
    k["Fecha"] = (pd.to_datetime(k["Fecha"]) + pd.DateOffset(years=1)).dt.strftime("%Y-%m-%d")
    k = k.rename(columns={target: "lag12"})
    d = d.assign(Fecha=pd.to_datetime(d["Fecha"]).dt.strftime("%Y-%m-%d"))
    return d.merge(k, on=["Especie", "Fecha"], how="left")["lag12"].to_numpy()


def make(kind, **kw):
    return {"ridge": lambda: Ridge(**kw), "enet": lambda: ElasticNet(max_iter=20000, **kw),
            "rf": lambda: RandomForestRegressor(n_estimators=300, random_state=SEED, **kw),
            "gbm": lambda: GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, subsample=0.8,
                                                     random_state=SEED, **kw)}[kind]()


GRIDS = {
    "ridge": [dict(alpha=a) for a in (0.1, 1, 10, 100)],
    "enet": [dict(alpha=a, l1_ratio=l) for a, l in itertools.product((0.001, 0.01, 0.1), (0.2, 0.5, 0.8))],
    "rf": [dict(max_depth=d, min_samples_leaf=l) for d, l in itertools.product((2, 3, 5), (3, 5, 10))],
    "gbm": [dict(max_depth=d, min_samples_leaf=l) for d, l in itertools.product((1, 2, 3), (3, 8))],
    "ridge_especie": [dict(alpha=a) for a in (0.1, 1, 10, 100)],
}


def fit_predict(kind, params, tr, te, X, ycol):
    if kind == "ridge_especie":
        p = pd.Series(np.nan, index=te.index)
        Xe = [c for c in X if not c.startswith("esp_") and c != "ipc_yoy_CA"]
        for e in ESPECIES:
            a, b = tr[tr.Especie == e], te[te.Especie == e]
            if len(b):
                p[b.index] = Ridge(**params).fit(a[Xe], a[ycol]).predict(b[Xe])
        return p.to_numpy()
    return make(kind, **params).fit(tr[X], tr[ycol]).predict(te[X])


def run(name, ycol):
    d = pd.read_csv(PROC / f"model_{name}_scaled.csv", parse_dates=["Fecha"])
    cols = joblib.load(MODELS / f"scaler_{name}.joblib")["columns"]
    X = cols + [c for c in d.columns if c.startswith("esp_")]
    d["lag12"] = lag12(d, ycol)
    tr, va, te = (d[d.split == s] for s in ("train", "validacion", "prueba"))
    rows, preds, best = [], {}, {}

    # linea base
    for nm, part in (("validacion", va), ("prueba", te)):
        m = part.dropna(subset=["lag12"])
        rows.append({"modelo": "base_lag12", "parametros": "", "particion": nm, "n": len(m),
                     **metrics(m[ycol].to_numpy(), m["lag12"].to_numpy())})
    base_val = rows[0]["MAE_pp"]

    for kind, grid in GRIDS.items():
        res = []
        for params in grid:
            p = fit_predict(kind, params, tr, va, X, ycol)
            res.append((np.abs(p - va[ycol]).mean(), params))
        _, params = min(res, key=lambda r: r[0])
        best[kind] = params
        trva = pd.concat([tr, va])
        for nm, a, b in (("validacion", tr, va), ("prueba", trva, te)):
            # prueba: modelo con hiperparametros elegidos, ajustado con train+validacion
            p = fit_predict(kind, params, a, b, X, ycol)
            rows.append({"modelo": kind, "parametros": str(params), "particion": nm, "n": len(b),
                         **metrics(b[ycol].to_numpy(), p)})
            preds[(kind, nm)] = pd.DataFrame({"Fecha": b.Fecha, "Especie": b.Especie, "real": b[ycol], "pred": p})
    comp = pd.DataFrame(rows)
    comp.insert(0, "objetivo", name)
    pd.concat([v.assign(modelo=k[0], particion=k[1]) for k, v in preds.items()]).to_csv(
        REP / f"predicciones_{name}.csv", index=False)
    return d, X, comp, best, base_val


def main():
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.float_format", "{:,.2f}".format)
    allc, ctx = [], {}
    for name, y in (("mercado", "y_mercado"), ("lab", "y_lab")):
        d, X, comp, best, base_val = run(name, y)
        allc.append(comp)
        ctx[name] = (d, X, best, y)
        print(f"\n===== {name.upper()} =====")
        print(comp.pivot_table(index="modelo", columns="particion", values=["MAE_pp", "sesgo_pp", "acierto_escenario"]))
        print({k: v for k, v in best.items()})
    pd.concat(allc).to_csv(REP / "comparacion_modelos.csv", index=False)
    joblib.dump({k: (v[1], v[2]) for k, v in ctx.items()}, MODELS / "seleccion_hiperparametros.joblib")


if __name__ == "__main__":
    main()
