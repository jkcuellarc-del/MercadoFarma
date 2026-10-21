"""Predictores ampliados y conjuntos candidatos (solo con datos de desarrollo).

Conjuntos declarados ANTES de evaluar:
  S0_actual    las 10 variables actuales
  S1_ar        S0 + crecimiento de hace 12 meses de la propia serie (autorregresivo)
  S2_real      S0 con los cambios de precio en terminos reales (precio nominal deflactado por el IPC promedio)
  S3_rezagos   S0 + inflacion y precios rezagados 6 y 12 meses
  S4_mezcla    S0 + participacion del mercado donde compite el Laboratorio en el mercado total, de hace 12 meses
  S5_todo      S2_real + autorregresivo + rezagos + mezcla
  S6_trm       S0 + TRM (cambio del promedio de 12 meses, y rezagos de 6 y 12 meses)
  S7_real_trm  S2_real + TRM (igual que S6)
Objetivos: crecimiento nominal, o crecimiento real (deflactado por el IPC promedio de 12 meses) que se convierte de
vuelta a nominal sumando la inflacion del escenario.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from . import variables as V
from .nucleo import EST, ONEHOT, Balanceado, ESPS  # noqa: F401

PRECIO_DE = {"var_leche": "Cattle", "var_res": "Cattle", "var_cerdo": "Swine", "var_huevo": "Poultry", "var_pollo": "Poultry"}
PRECIOS = list(PRECIO_DE)
BASE = ["ipc_yoy", "ipc_yoy_CA", "pib", "pib_agro", "smmlv"] + PRECIOS


def extra(df, comp, trm):
    p = V.panel(df, comp).sort_values("Fecha")
    tm = trm.set_index("Fecha").sort_index()["trm_prom"]
    t_f = pd.DataFrame({"trm_yoy12": V.yoy12(tm), "trm_yoy": tm / tm.shift(12) - 1}).reset_index()
    out = []
    for esp, g in p.groupby("Especie"):
        g = g.set_index("Fecha")
        f = pd.DataFrame(index=g.index)
        f["Especie"] = esp
        f["ipcm_yoy"] = V.yoy12(g["IPC"])
        f["part_compite"] = g["Mercado_compite"].rolling(12).sum() / g["Mercado"].rolling(12).sum()
        out.append(f.reset_index())
    e = pd.concat(out, ignore_index=True)
    return e.merge(t_f, on="Fecha", how="left")


def ampliar(f, ex):
    d = f.merge(ex, on=["Fecha", "Especie"]).sort_values(["Especie", "Fecha"]).reset_index(drop=True)
    for k in PRECIOS:
        aplica = (d.Especie == PRECIO_DE[k])
        d["real_" + k] = np.where(aplica, (1 + d[k]) / (1 + d["ipcm_yoy"]) - 1, 0.0)
    g = d.groupby("Especie")
    for c in ["ipc_yoy"] + PRECIOS:
        d[c + "_l6"] = g[c].shift(6)
        d[c + "_l12"] = g[c].shift(12)
    d["trm_real_yoy12"] = (1 + d["trm_yoy12"]) / (1 + d["ipcm_yoy"]) - 1
    for c in ("trm_yoy12", "trm_real_yoy12"):
        d[c + "_l6"] = d.groupby("Especie")[c].shift(6)
        d[c + "_l12"] = d.groupby("Especie")[c].shift(12)
    for y in ("y_mercado", "y_compite"):
        d[y + "_l12"] = g[y].shift(12)
        d[y + "_real"] = (1 + d[y]) / (1 + d["ipcm_yoy"]) - 1
    d["y_lab_real"] = (1 + d["y_lab"]) / (1 + d["ipcm_yoy"]) - 1
    d["part_compite_l12"] = g["part_compite"].shift(12)
    return d


def conjuntos(target):
    ar = [f"{target}_l12"]
    real = [c for c in BASE if c not in PRECIOS] + ["real_" + k for k in PRECIOS]
    rez = [c + s for c in ["ipc_yoy"] + PRECIOS for s in ("_l6", "_l12")]
    trm = ["trm_yoy12", "trm_yoy12_l6", "trm_yoy12_l12"]
    return {"S0_actual": BASE, "S1_ar": BASE + ar, "S2_real": real, "S3_rezagos": BASE + rez, "S4_mezcla": BASE + ["part_compite_l12"],
            "S5_todo": real + ar + rez + ["part_compite_l12"], "S6_trm": BASE + trm, "S7_real_trm": real + trm}


def pipeline_cont(kind, cont, **params):
    pre = ColumnTransformer([("num", StandardScaler(), cont), ("esp", "passthrough", ONEHOT)])
    p = Pipeline([("pre", pre), ("model", Balanceado(EST[kind](), False))])
    p.set_params(**{f"model__est__{k}": v for k, v in params.items()})
    return p
