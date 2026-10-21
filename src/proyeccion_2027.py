"""Proyeccion 2027 con los Pipelines finales del protocolo (reajustados con datos hasta junio 2026).

Entradas del escenario base: las de simulador/modelo.json (IPC 5,1%, PIB 2,3%, PIB agro 2,7%,
SMMLV 11,9%, precios en su nivel de junio 2026). Salidas: reports/protocolo/proyeccion_2027_base.csv
y reports/protocolo/sensibilidad_2027.csv
"""
import json
from pathlib import Path

import sys

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import protocolo  # noqa: E402,F401  (necesario para deserializar los Pipelines)
OUT = ROOT / "reports" / "protocolo"
ESPS = ["CA", "Cattle", "Poultry", "Swine"]
PRECIOS = ["var_leche", "var_res", "var_cerdo", "var_huevo", "var_pollo"]
PRECIO_DE = {"var_leche": "Cattle", "var_res": "Cattle", "var_cerdo": "Swine", "var_huevo": "Poultry", "var_pollo": "Poultry"}
GEN = {"ipc_yoy": 0.01, "pib": 1.0, "pib_agro": 1.0, "smmlv": 0.01}


def cargar():
    m = joblib.load(ROOT / "models" / "pipeline_final_mercado.joblib")
    l = joblib.load(ROOT / "models" / "pipeline_final_lab.joblib")
    base = json.loads((ROOT / "simulador" / "modelo.json").read_text())["base"]
    ann = pd.read_csv(ROOT / "data" / "processed" / "annual_especie.csv")
    a26 = ann[ann.Año == 2026].set_index("Especie")
    w = {"mercado": (a26.Mercado / a26.Mercado.sum()).to_dict(), "lab": (a26.Venta_Laboratorio / a26.Venta_Laboratorio.sum()).to_dict()}
    return m, l, base, w


def proyectar(m, l, entradas, w):
    filas = []
    for e in ESPS:
        r = {**entradas[e], "ipc_yoy_CA": entradas[e]["ipc_yoy"] if e == "CA" else 0.0}
        for s in ESPS:
            r[f"esp_{s}"] = int(s == e)
        filas.append(r)
    X = pd.DataFrame(filas)
    gm = m["pipeline"].predict(X[m["columnas"]])
    X["y_mercado"] = gm
    gl = l["pipeline"].predict(X[l["columnas"]])
    out = pd.DataFrame({"Especie": ESPS, "crec_mercado": gm, "crec_lab": gl})
    tot = {"Especie": "Total", "crec_mercado": sum(w["mercado"][e] * g for e, g in zip(ESPS, gm)),
           "crec_lab": sum(w["lab"][e] * g for e, g in zip(ESPS, gl))}
    return pd.concat([out, pd.DataFrame([tot])], ignore_index=True)


def main():
    m, l, base, w = cargar()
    b = proyectar(m, l, base, w)
    b["escenario_mercado"] = pd.cut(b.crec_mercado, [-np.inf, .08, .15, np.inf], labels=["regular", "estable", "optimista"], right=False)
    b["escenario_lab"] = pd.cut(b.crec_lab, [-np.inf, .08, .15, np.inf], labels=["regular", "estable", "optimista"], right=False)
    b.to_csv(OUT / "proyeccion_2027_base.csv", index=False)
    print(b.round(4).to_string(index=False))
    sens = []
    for k, step in {**GEN, **{p: 0.10 for p in PRECIOS}}.items():
        e2 = json.loads(json.dumps(base))
        for e in ESPS:
            if k in PRECIOS:
                if PRECIO_DE[k] == e:
                    e2[e][k] += step
            else:
                e2[e][k] += step
        p = proyectar(m, l, e2, w)
        t0, t1 = b[b.Especie == "Total"].iloc[0], p[p.Especie == "Total"].iloc[0]
        sens.append({"variable": k, "cambio": step, "d_mercado_pp": (t1.crec_mercado - t0.crec_mercado) * 100, "d_lab_pp": (t1.crec_lab - t0.crec_lab) * 100})
    s = pd.DataFrame(sens)
    s.to_csv(OUT / "sensibilidad_2027.csv", index=False)
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
