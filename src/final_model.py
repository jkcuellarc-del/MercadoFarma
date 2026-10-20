"""Modelo final (Ridge por especie) y proyeccion 2027.

Mercado : y_mercado = f(ipc_yoy, pib, pib_agro, smmlv, variaciones de precio propias)
Lab     : y_lab     = f(las mismas + crecimiento del mercado proyectado de la especie)
Cada especie tiene su propio Ridge; solo se ajusta con filas de esa especie.
Se entrena con entrenamiento + validacion + prueba (hasta junio 2026).

Entradas 2027 (las que mueve el usuario en el simulador), por especie:
  ipc_yoy   inflacion 2027 (dic/dic)        pib, pib_agro  crecimiento 2027 (%)
  smmlv     aumento del salario minimo 2027  var_<precio>   cambio del precio promedio 2027 vs 2026
Escenario base: IPC, PIB y PIB agro de 2026 se mantienen; salario minimo = promedio 2022-2025;
precios constantes en su nivel de junio 2026 durante todo 2027.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[1]
PROC, MODELS, REP = ROOT / "data" / "processed", ROOT / "models", ROOT / "reports"
ESPECIES = ["CA", "Cattle", "Poultry", "Swine"]
PRECIOS = {"var_leche": "Precio Leche", "var_res": "Precio Carne Res", "var_cerdo": "Precio carne cerdo",
           "var_huevo": "Precio huevo", "var_pollo": "Precio Pollo"}
ALPHA = {"mercado": 100, "lab": 10}  # elegidos en validacion (ver reports/comparacion_modelos.csv)
SPLITS = ["train", "validacion", "prueba"]


def features_of(name):
    cols = joblib.load(MODELS / f"scaler_{name}.joblib")["columns"]
    return [c for c in cols if c != "ipc_yoy_CA"]  # la pendiente propia ya la da el modelo por especie


def fit(name, ycol):
    d = pd.read_csv(PROC / f"model_{name}_scaled.csv")
    X = features_of(name)
    fit_d = d[d.split.isin(SPLITS)]
    return X, {e: Ridge(alpha=ALPHA[name]).fit(g[X], g[ycol]) for e, g in fit_d.groupby("Especie")}


def base_inputs():
    m = pd.read_csv(PROC / "monthly_especie.csv", parse_dates=["Fecha"])
    a = pd.read_csv(PROC / "annual_especie.csv")
    inp = {}
    for e in ESPECIES:
        g = m[m.Especie == e].set_index("Fecha")
        d = {"ipc_yoy": g.loc["2026-12-01", "IPC"] / g.loc["2025-12-01", "IPC"] - 1,
             "pib": g.loc["2026-12-01", "PIB"], "pib_agro": g.loc["2026-12-01", "PIB Agro"],
             "smmlv": a[(a.Año.between(2022, 2025)) & (a.Especie == e)].SMMLV.mean()}
        for k, c in PRECIOS.items():
            p = g[c]
            d[k] = (p.loc["2026-06-01"] / p["2026-01-01":"2026-12-01"].mean() - 1) if p.notna().any() else 0.0
        inp[e] = d
    return inp


def project(inputs, models=None):
    """inputs: {especie: {variable: valor}} -> DataFrame con crecimiento 2027 de mercado y laboratorio."""
    if models is None:
        models = {"mercado": fit("mercado", "y_mercado"), "lab": fit("lab", "y_lab")}
    sc_m = joblib.load(MODELS / "scaler_mercado.joblib")
    sc_l = joblib.load(MODELS / "scaler_lab.joblib")
    a = pd.read_csv(PROC / "annual_especie.csv")
    a = a[a.Año == 2026].set_index("Especie")
    rows = []
    for e in ESPECIES:
        x = pd.DataFrame([{**{c: 0.0 for c in sc_m["columns"]}, **inputs[e]}])
        x["ipc_yoy_CA"] = x["ipc_yoy"] if e == "CA" else 0.0
        xm = pd.DataFrame(sc_m["scaler"].transform(x[sc_m["columns"]]), columns=sc_m["columns"])
        Xm, mm = models["mercado"]
        g_m = float(mm[e].predict(xm[Xm])[0])
        x["y_mercado"] = g_m
        xl = pd.DataFrame(sc_l["scaler"].transform(x[sc_l["columns"]]), columns=sc_l["columns"])
        Xl, ml = models["lab"]
        g_l = float(ml[e].predict(xl[Xl])[0])
        rows.append({"Especie": e, "crec_mercado": g_m, "crec_lab": g_l,
                     "mercado_2026": a.loc[e, "Mercado"], "lab_2026": a.loc[e, "Venta_Laboratorio"]})
    r = pd.DataFrame(rows)
    tot = {"Especie": "Total",
           "crec_mercado": (r.mercado_2026 * (1 + r.crec_mercado)).sum() / r.mercado_2026.sum() - 1,
           "crec_lab": (r.lab_2026 * (1 + r.crec_lab)).sum() / r.lab_2026.sum() - 1,
           "mercado_2026": r.mercado_2026.sum(), "lab_2026": r.lab_2026.sum()}
    r = pd.concat([r, pd.DataFrame([tot])], ignore_index=True)
    for k in ("mercado", "lab"):
        r[f"escenario_{k}"] = pd.cut(r[f"crec_{k}"], [-np.inf, .08, .15, np.inf],
                                     labels=["regular", "estable", "optimista"], right=False)
    return r


def main():
    pd.set_option("display.width", 220, "display.float_format", "{:,.3f}".format)
    models = {"mercado": fit("mercado", "y_mercado"), "lab": fit("lab", "y_lab")}
    joblib.dump(models, MODELS / "final_ridge_por_especie.joblib")
    REP.mkdir(exist_ok=True)
    # coeficientes (variables estandarizadas: efecto en pp de crecimiento por 1 desv. estandar)
    for nm, (X, mod) in models.items():
        co = pd.DataFrame({e: pd.Series(m.coef_ * 100, index=X) for e, m in mod.items()})
        co.loc["intercepto"] = [m.intercept_ * 100 for m in mod.values()]
        co.to_csv(REP / f"coeficientes_{nm}.csv")
        print(f"\nCoeficientes {nm} (pp por 1 desv. estandar):"); print(co.round(2))
    inp = base_inputs()
    print("\nEntradas escenario base 2027:"); print(pd.DataFrame(inp).T)
    r = project(inp, models)
    r.to_csv(REP / "escenario_base_2027.csv", index=False)
    print("\nProyeccion 2027 (escenario base):"); print(r)


if __name__ == "__main__":
    main()
