"""Busqueda de un mejor modelo para el crecimiento del laboratorio.

Evaluacion realista: en validacion/prueba el crecimiento del mercado que entra al modelo del
laboratorio es el PROYECTADO por el modelo de mercado (Ridge por especie), no el observado,
porque en 2027 solo habra proyeccion. Tambien se reporta el caso con mercado observado.
Los modelos de "participacion" predicen el cambio de la participacion del laboratorio:
    (1 + y_lab) = (1 + y_mercado) * (1 + y_part)
Salida: reports/lab_experimento.csv
"""
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
PROC, MODELS, REP = ROOT / "data" / "processed", ROOT / "models", ROOT / "reports"
ESP = ["CA", "Cattle", "Poultry", "Swine"]


def esc(y):
    return pd.cut(pd.Series(y), [-np.inf, .08, .15, np.inf], labels=False, right=False).to_numpy()


def met(y, p):
    e = p - y
    return dict(MAE_pp=np.abs(e).mean() * 100, sesgo_pp=e.mean() * 100, acierto_esc=(esc(y) == esc(p)).mean())


def market_pred(d_lab):
    """Crecimiento de mercado proyectado (Ridge por especie, alpha=100) para cada fila del lab."""
    dm = pd.read_csv(PROC / "model_mercado_scaled.csv")
    X = [c for c in joblib.load(MODELS / "scaler_mercado.joblib")["columns"] if c != "ipc_yoy_CA"]
    out = pd.Series(np.nan, index=d_lab.index)
    for part, fit_s in (("validacion", ["train"]), ("prueba", ["train", "validacion"])):
        for e in ESP:
            a = dm[(dm.Especie == e) & dm.split.isin(fit_s)]
            m = Ridge(alpha=100).fit(a[X], a.y_mercado)
            idx = d_lab[(d_lab.split == part) & (d_lab.Especie == e)]
            out[idx.index] = m.predict(idx[X])
    return out


def main():
    d = pd.read_csv(PROC / "model_lab_scaled.csv", parse_dates=["Fecha"])
    raw = pd.read_csv(PROC / "model_lab.csv", parse_dates=["Fecha"])
    d["y_part"] = (1 + raw.y_lab) / (1 + raw.y_mercado) - 1  # cambio de participacion
    d["y_part_lag12"] = np.nan
    k = d[["Especie", "Fecha", "y_part"]].assign(Fecha=lambda x: x.Fecha + pd.DateOffset(years=1))
    d = d.drop(columns="y_part_lag12").merge(k.rename(columns={"y_part": "y_part_lag12"}), on=["Especie", "Fecha"], how="left")
    d["y_mkt_hat"] = market_pred(d)
    X0 = ["ipc_yoy", "pib", "pib_agro", "smmlv", "var_leche", "var_res", "var_cerdo", "var_huevo", "var_pollo"]
    sc = joblib.load(MODELS / "scaler_lab.joblib")
    global SC, COLS
    SC, COLS = sc["scaler"], sc["columns"]

    def run(fit_df, te, mkt, kind):
        """Devuelve prediccion de y_lab para te, usando `mkt` como crecimiento de mercado."""
        p = pd.Series(np.nan, index=te.index)
        for e in ESP:
            a, b = fit_df[fit_df.Especie == e], te[te.Especie == e]
            if b.empty:
                continue
            g = mkt[b.index]
            if kind == "actual_ridge_y":  # modelo actual: y_lab ~ exogenas + y_mercado (Ridge por especie)
                m = Ridge(alpha=10).fit(a[X0 + ["y_mercado"]], a.y_lab)
                bb = b[X0 + ["y_mercado"]].copy()
                bb["y_mercado"] = (g - SC.mean_[COLS.index("y_mercado")]) / SC.scale_[COLS.index("y_mercado")]
                p[b.index] = m.predict(bb)
            elif kind == "part_const":  # participacion crece como su promedio historico
                s = a.y_part.mean(); p[b.index] = (1 + g) * (1 + s) - 1
            elif kind == "part_cero":  # participacion constante
                p[b.index] = g
            elif kind == "part_persist":  # participacion repite cambio de hace 12 meses
                s = b.y_part_lag12.fillna(a.y_part.mean()); p[b.index] = (1 + g) * (1 + s) - 1
            elif kind.startswith("part_mezcla"):  # mezcla persistencia y promedio (lambda=0.5)
                s = 0.5 * b.y_part_lag12.fillna(a.y_part.mean()) + 0.5 * a.y_part.mean(); p[b.index] = (1 + g) * (1 + s) - 1
            elif kind == "part_ridge":  # Ridge sobre exogenas -> cambio de participacion
                m = Ridge(alpha=30).fit(a[X0], a.y_part); s = m.predict(b[X0]); p[b.index] = (1 + g) * (1 + s) - 1
            elif kind == "part_gbm":
                m = GradientBoostingRegressor(n_estimators=100, learning_rate=.05, max_depth=1, subsample=.8, random_state=0).fit(a[X0], a.y_part)
                s = m.predict(b[X0]); p[b.index] = (1 + g) * (1 + s) - 1
        return p

    kinds = ["actual_ridge_y", "part_cero", "part_const", "part_persist", "part_mezcla", "part_ridge", "part_gbm"]
    rows = []
    for kind in kinds:
        for fuente in ("proyectado", "observado"):
            for part, fit_s in (("validacion", ["train"]), ("prueba", ["train", "validacion"])):
                a, b = d[d.split.isin(fit_s)], d[d.split == part]
                mkt = b["y_mkt_hat"] if fuente == "proyectado" else raw.loc[b.index, "y_mercado"]
                mkt = pd.Series(mkt.to_numpy(), index=b.index)
                allm = pd.Series(np.nan, index=d.index); allm[b.index] = mkt
                p = run(a, b, allm, kind)
                ok = p.notna()
                rows.append(dict(modelo=kind, mercado=fuente, particion=part, n=ok.sum(), **met(raw.loc[b.index[ok], "y_lab"].to_numpy(), p[ok].to_numpy())))
    r = pd.DataFrame(rows)
    pd.set_option("display.width", 220, "display.float_format", "{:,.2f}".format)
    print(r.pivot_table(index=["modelo"], columns=["mercado", "particion"], values="MAE_pp"))
    print(r.pivot_table(index=["modelo"], columns=["mercado", "particion"], values="acierto_esc"))
    r.to_csv(REP / "lab_experimento.csv", index=False)


if __name__ == "__main__":
    main()
