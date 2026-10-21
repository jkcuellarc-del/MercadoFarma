"""Proyeccion 2027 (escenario base) con los modelos reajustados, y bandas de error. Se ejecuta despues de la prueba.

Escenario base 2027: inflacion 5,1% (encuesta de analistas del Banco de la Republica, dic-2027), PIB 2,3% (BBVA Research),
PIB agropecuario = promedio 2020-2025, salario minimo = promedio de aumentos 2022-2025, precios nominales constantes en su
nivel de junio 2026 durante 2027 (cambio frente al promedio de 2026, con julio a diciembre de 2026 en el nivel de junio).
Precio real = (1 + cambio nominal) / (1 + inflacion) - 1. Los pesos de los totales son las ventas de los ultimos 12 meses observados.
Salidas: reports/v2/proyeccion_2027_base.csv (modelos elegidos por la regla), proyeccion_2027_alt.csv (modelos de menor MAE de CV),
bandas_error.json, base_2027.json
"""
import json

import joblib
import numpy as np
import pandas as pd

from . import config as C
from . import datos, variables
from .nucleo import *  # noqa: F401,F403

PRECIO_DE = {"var_leche": "Cattle", "var_res": "Cattle", "var_cerdo": "Swine", "var_huevo": "Poultry", "var_pollo": "Poultry"}
COL_PRECIO = {"var_leche": "Precio Leche", "var_res": "Precio Carne Res", "var_cerdo": "Precio carne cerdo", "var_huevo": "Precio huevo", "var_pollo": "Precio Pollo"}
IPC, PIB = 0.051, 2.3


def base_2027(todo, comp):
    p = variables.panel(todo, comp).sort_values("Fecha")
    anual = todo.assign(a=todo.Fecha.dt.year).groupby("a")[["PIB Agro", "Porc Crec SMMLV"]].first()
    base = {"ipc": IPC, "pib": PIB, "pib_agro": float(anual.loc[2020:2025, "PIB Agro"].mean()), "smmlv": float(anual.loc[2022:2025, "Porc Crec SMMLV"].mean()), "nominal": {}}
    for k, esp in PRECIO_DE.items():
        s = p[p.Especie == esp].set_index("Fecha")[COL_PRECIO[k]]
        jun = s.loc["2026-06-01"]
        prom26 = (s.loc["2026-01-01":"2026-06-01"].sum() + 6 * jun) / 12
        base["nominal"][k] = float(jun / prom26 - 1)
    q = p[(p.Fecha > "2025-06-01") & (p.Fecha <= "2026-06-01")].groupby("Especie")[["Mercado", "Venta Laboratorio"]].sum()
    base["pesos"] = {"mercado": (q.Mercado / q.Mercado.sum()).to_dict(), "lab": (q["Venta Laboratorio"] / q["Venta Laboratorio"].sum()).to_dict()}
    return base


def filas(base, e, y_mercado=None, delta=None):
    d = {"ipc": base["ipc"], "pib": base["pib"], "pib_agro": base["pib_agro"], "smmlv": base["smmlv"], "nominal": dict(base["nominal"])}
    d.update(delta or {})
    r = {"ipc_yoy": d["ipc"], "ipc_yoy_CA": d["ipc"] if e == "CA" else 0.0, "pib": d["pib"], "pib_agro": d["pib_agro"], "smmlv": d["smmlv"]}
    for k, esp in PRECIO_DE.items():
        r["real_" + k] = (1 + d["nominal"][k]) / (1 + d["ipc"]) - 1 if esp == e else 0.0
    for s_ in ESPS:
        r[f"esp_{s_}"] = int(s_ == e)
    if y_mercado is not None:
        r["y_mercado"] = y_mercado
    return r


def proyectar(base, m_mer, m_lab, delta=None):
    X = pd.DataFrame([filas(base, e, delta=delta) for e in ESPS])
    gm = m_mer.predict(X[columnas("mercado")])
    X["y_mercado"] = gm
    gl = m_lab.predict(X[columnas("lab_ym")])
    o = pd.DataFrame({"Especie": ESPS, "crec_mercado": gm, "crec_lab": gl})
    tot = {"Especie": "Total", "crec_mercado": sum(base["pesos"]["mercado"][e] * g for e, g in zip(ESPS, gm)),
           "crec_lab": sum(base["pesos"]["lab"][e] * g for e, g in zip(ESPS, gl))}
    o = pd.concat([o, pd.DataFrame([tot])], ignore_index=True)
    for k in ("mercado", "lab"):
        o["escenario_" + k] = pd.cut(o["crec_" + k], [-np.inf, .08, .15, np.inf], labels=["regular", "estable", "optimista"], right=False)
    return o


def main():
    res = json.loads((C.REP / "prueba_resultados.json").read_text())
    lv = res["variante_lab"]
    todo = pd.concat([datos.leer_desarrollo(), datos.leer_prueba("proyeccion 2027 (posterior a la evaluacion unica)")], ignore_index=True)
    comp = pd.read_csv(C.DATA / "series_compite.csv")
    base = base_2027(todo, comp)
    (C.REP / "base_2027.json").write_text(json.dumps(base, indent=1))
    M = {t: joblib.load(C.MODELOS / f"pipeline_final_{t}.joblib")["pipeline"] for t in ("mercado", "compite", lv)}
    A = {t: joblib.load(C.MODELOS / f"pipeline_alt_{t}.joblib")["pipeline"] if (C.MODELOS / f"pipeline_alt_{t}.joblib").exists() else M[t] for t in M}
    pd.set_option("display.width", 200, "display.float_format", "{:,.3f}".format)
    p = proyectar(base, M["mercado"], M[lv])
    p.to_csv(C.REP / "proyeccion_2027_base.csv", index=False)
    a = proyectar(base, A["mercado"], A[lv])
    a.to_csv(C.REP / "proyeccion_2027_alt.csv", index=False)
    print("base 2027:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in base.items() if k not in ("pesos", "nominal")}, {k: round(v, 3) for k, v in base["nominal"].items()})
    print("\nModelos elegidos por la regla:\n", p.to_string(index=False), "\n\nModelos de menor MAE de CV (informativo):\n", a.to_string(index=False))
    # bandas de error por especie: promedio del MAE fuera de pliegue (CV) y del MAE de prueba
    w = base["pesos"]
    ban = {}
    for k, t in (("mercado", "mercado"), ("lab", lv)):
        oo = pd.read_csv(C.REP / f"oof_por_especie_{t}.csv").set_index("Especie")["mean"]
        ban[k] = {e: float((oo[e] + res[t]["por_especie"][e]["MAE_pp"]) / 2) for e in ESPS}
        ban[k]["Total"] = float(sum(w[k][e] * ban[k][e] for e in ESPS))
    (C.REP / "bandas_error.json").write_text(json.dumps(ban, indent=1))
    print("\nbandas:", {k: {e: round(v, 1) for e, v in d.items()} for k, d in ban.items()})


if __name__ == "__main__":
    main()
