"""Variables mensuales de 12 meses moviles, codificacion, escalamiento y particion.

Entrada : data/processed/monthly_especie.csv (salida de prepare_data.py)
Salidas : data/processed/model_mercado.csv / model_lab.csv   variables sin escalar + split
          data/processed/model_mercado_scaled.csv / model_lab_scaled.csv
          models/scaler_mercado.joblib / scaler_lab.joblib

Unidad de analisis: (especie, mes t). La variable objetivo es el crecimiento nominal
de la venta acumulada de 12 meses terminada en t frente a la acumulada 12 meses antes.
Para t = dic-2027 es el crecimiento anual 2027, que es lo que se quiere proyectar.

Variables explicativas (todas calculadas con informacion hasta t):
  ipc_yoy         inflacion de los ultimos 12 meses (IPC_t / IPC_t-12 - 1)
  pib, pib_agro,
  smmlv           promedio de los ultimos 12 meses (ya vienen como % de crecimiento)
  var_<precio>    cambio del precio promedio de 12 meses vs. el promedio 12 meses antes
                  (leche, res, cerdo, huevo, pollo); 0 si la especie no lo usa
  ipc_yoy_CA      ipc_yoy x (especie == CA): pendiente propia de animales de companía
                  ante la inflacion (los hogares priorizan gastos esenciales sobre la
                  salud de la mascota). Perros y gatos no se usan como variables.
  esp_*           especie en one-hot
  y_mercado       (solo modelo del laboratorio) crecimiento del mercado de la especie

Particion cronologica segun el mes t:
  train 2021-12..2024-12 (laboratorio: 2023-12..2024-12) | validacion 2025 | prueba 2026-01..06
  estimado 2026-07..12: ventanas que incluyen meses completados, no se usan para evaluar.
Las ventanas de 12 meses se solapan entre particiones vecinas (inevitable con datos
mensuales); por eso la validacion es algo mas optimista que una prueba real.
"""
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
MODELS = ROOT / "models"
MODELS.mkdir(exist_ok=True)

PRECIOS = {"var_leche": "Precio Leche", "var_res": "Precio Carne Res", "var_cerdo": "Precio carne cerdo",
           "var_huevo": "Precio huevo", "var_pollo": "Precio Pollo"}
ESPECIES = ["CA", "Cattle", "Poultry", "Swine"]
CONT = ["ipc_yoy", "ipc_yoy_CA", "pib", "pib_agro", "smmlv"] + list(PRECIOS)
ONEHOT = [f"esp_{e}" for e in ESPECIES]


def yoy12(s):
    """Cambio del promedio movil de 12 meses frente al de 12 meses antes."""
    r = s.rolling(12).mean()
    return r / r.shift(12) - 1


def features(m):
    out = []
    for esp, g in m.sort_values("Fecha").groupby("Especie"):
        g = g.set_index("Fecha")
        f = pd.DataFrame(index=g.index)
        f["Especie"] = esp
        r_m, r_l = g["Mercado"].rolling(12).sum(), g["Venta Laboratorio"].rolling(12).sum()
        f["y_mercado"] = r_m / r_m.shift(12) - 1
        r_l = r_l.where(f.index >= "2022-12-01")  # ventana 100% posterior al inicio de la historia del laboratorio
        f["y_lab"] = r_l / r_l.shift(12) - 1
        f["ipc_yoy"] = g["IPC"] / g["IPC"].shift(12) - 1
        f["pib"] = g["PIB"].rolling(12).mean()
        f["pib_agro"] = g["PIB Agro"].rolling(12).mean()
        f["smmlv"] = g["Porc Crec SMMLV"].rolling(12).mean()
        for k, c in PRECIOS.items():
            f[k] = yoy12(g[c]) if g[c].notna().any() else 0.0
        f["ipc_yoy_CA"] = f["ipc_yoy"] if esp == "CA" else 0.0
        f["Estimado"] = g["Estimado"].astype(int).rolling(12).max().astype(bool)
        out.append(f.reset_index())
    return pd.concat(out, ignore_index=True)


def split(fecha, train_ini):
    s = pd.Series("", index=fecha.index)
    s[(fecha >= train_ini) & (fecha <= "2024-12-01")] = "train"
    s[(fecha >= "2025-01-01") & (fecha <= "2025-12-01")] = "validacion"
    s[(fecha >= "2026-01-01") & (fecha <= "2026-06-01")] = "prueba"
    s[fecha >= "2026-07-01"] = "estimado"
    return s


def escenario(y):
    return pd.cut(y, [-np.inf, .08, .15, np.inf], labels=["regular", "estable", "optimista"], right=False)


def build(f, target, train_ini, extra, name):
    d = f.dropna(subset=[target] + CONT + extra).copy()
    d["split"] = split(d["Fecha"], train_ini)
    d = d[d.split != ""].copy()
    d["escenario"] = escenario(d[target])
    for e in ESPECIES:
        d[f"esp_{e}"] = (d["Especie"] == e).astype(int)
    cols = CONT + extra
    sc = StandardScaler().fit(d.loc[d.split == "train", cols])
    ds = d.copy()
    ds[cols] = sc.transform(d[cols])
    keep = ["Fecha", "Especie", "split", "Estimado", target, "escenario"] + cols + ONEHOT
    d[keep].to_csv(PROC / f"model_{name}.csv", index=False)
    ds[keep].to_csv(PROC / f"model_{name}_scaled.csv", index=False)
    joblib.dump({"scaler": sc, "columns": cols}, MODELS / f"scaler_{name}.joblib")
    return d


def main():
    m = pd.read_csv(PROC / "monthly_especie.csv", parse_dates=["Fecha"])
    f = features(m)
    mer = build(f, "y_mercado", "2021-12-01", [], "mercado")
    lab = build(f, "y_lab", "2023-12-01", ["y_mercado"], "lab")

    pd.set_option("display.width", 220, "display.float_format", "{:,.3f}".format)
    for nombre, d, t in (("MERCADO", mer, "y_mercado"), ("LABORATORIO", lab, "y_lab")):
        print(f"== {nombre}: filas por particion y especie")
        print(d.pivot_table(index="split", columns="Especie", values=t, aggfunc="count", margins=True))
        print("escenarios (train+val+prueba):")
        print(d[d.split.isin(["train", "validacion", "prueba"])].groupby("split").escenario.value_counts().unstack())
        tr = d[d.split == "train"]
        print("correlacion con el objetivo (train):")
        print(tr[CONT + (["y_mercado"] if t == "y_lab" else [])].corrwith(tr[t]).round(2).to_dict())
    print("Dic-2026 (base para 2027):")
    print(mer[mer.Fecha == "2026-12-01"][["Especie", "y_mercado", "ipc_yoy", "pib", "smmlv"]])


if __name__ == "__main__":
    main()
