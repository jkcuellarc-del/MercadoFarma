"""Reajuste final y exportacion para el simulador. SE EJECUTA SOLO DESPUES de la evaluacion unica de la prueba.

1) Reajusta los modelos elegidos con todo lo observado hasta junio de 2026 (desarrollo + prueba).
2) Exporta los coeficientes (modelos lineales) a simulador/modelo_v2.json con: escalamiento, coeficientes, escenario base 2027,
   pesos por especie (ventas de los ultimos 12 meses observados) y margenes de error (CV fuera de pliegue y prueba).
Entradas del escenario base 2027 (fuentes externas, octubre de 2026): IPC 5,1% (encuesta de analistas del Banco de la Republica,
dic-2027); PIB 2,3% (BBVA Research); PIB agro = promedio 2020-2025; SMMLV = promedio de aumentos 2022-2025; precios nominales
constantes en su nivel de junio 2026 durante 2027.
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor  # noqa: F401

from . import config as C
from . import datos, variables
from .nucleo import *  # noqa: F401,F403
from .nucleo import PerEspecie

PRECIO_DE = {"var_leche": "Cattle", "var_res": "Cattle", "var_cerdo": "Swine", "var_huevo": "Poultry", "var_pollo": "Poultry"}


def reajustar():
    sels = {k: json.loads((C.REP / f"seleccion_{k}.json").read_text()) for k in TASKS}
    lab_var = min(("lab", "lab_ym"), key=lambda k: sels[k]["MAE_cv_final"])
    dev = datos.leer_desarrollo()
    test = datos.leer_prueba("reajuste final (posterior a la evaluacion unica)")
    todo = pd.concat([dev, test], ignore_index=True)
    comp = pd.read_csv(C.DATA / "series_compite.csv")
    f = variables.construir(todo, comp)
    C.MODELOS.mkdir(parents=True, exist_ok=True)
    out = {"lab_var": lab_var, "panel": todo}
    for task in ("mercado", "compite", lab_var):
        t, sel = TASKS[task], sels[task]
        d = variables.tabla(f, task, t["ini"], C.PRUEBA_FIN)
        pipe = pipeline(sel["final"], task, sel["balance"], **sel["params"]).fit(d[columnas(task)], d[t["y"]])
        joblib.dump({"pipeline": pipe, "columnas": columnas(task), "seleccion": sel, "n_filas": len(d)}, C.MODELOS / f"pipeline_final_{task}.joblib")
        out[task] = pipe
        print(task, sel["nombre"], "reajustado con", len(d), "filas")
    return out


def exportar_lineal(pipe, task):
    pre, est = pipe.named_steps["pre"], pipe.named_steps["model"].est_
    sc = pre.named_transformers_["num"]
    cont = TASKS[task]["cont"]
    base = {"cont": cont, "mean": dict(zip(cont, map(float, sc.mean_))), "scale": dict(zip(cont, map(float, sc.scale_)))}
    if isinstance(est, PerEspecie):
        base["tipo"] = "por_especie"
        base["especies"] = {ESPS[k]: {"intercept": float(m.intercept_), "coef": dict(zip(cont, map(float, m.coef_)))} for k, m in est.models_.items()}
    elif hasattr(est, "coef_"):
        base["tipo"] = "comun"
        base["intercept"] = float(est.intercept_)
        base["coef"] = dict(zip(cont + ONEHOT, map(float, est.coef_)))
    else:
        raise ValueError(f"El modelo {type(est).__name__} no es lineal: el simulador web no lo puede calcular")
    return base
