"""Variables de 12 meses moviles, a partir de un DataFrame ya tipado (desarrollo, o desarrollo + prueba).

Todas las variables en el mes t usan solo informacion hasta t, de modo que las filas con t <= CORTE
son identicas se construyan con o sin los meses de la prueba.
"""
import numpy as np
import pandas as pd

from . import config as C
from . import datos

PRECIOS = {"var_leche": "Precio Leche", "var_res": "Precio Carne Res", "var_cerdo": "Precio carne cerdo",
           "var_huevo": "Precio huevo", "var_pollo": "Precio Pollo"}
ESPS = ["CA", "Cattle", "Poultry", "Swine"]
LAB_INI = "2022-12-01"  # primera ventana de 12 meses 100% posterior al inicio de la historia del laboratorio


def panel(df):
    m = df.groupby(["Fecha", "Especie"])[["Mercado", "Venta Laboratorio"]].sum()
    nac = df.groupby("Fecha")[["IPC", "PIB", "PIB Agro", "Porc Crec SMMLV"]].first()
    pre = df.groupby(["Fecha", "Especie"])[list(PRECIOS.values())].first()
    return m.join(pre).reset_index().merge(nac.reset_index(), on="Fecha")


def yoy12(s):
    r = s.rolling(12).mean()
    return r / r.shift(12) - 1


def construir(df):
    out = []
    for esp, g in panel(df).sort_values("Fecha").groupby("Especie"):
        g = g.set_index("Fecha")
        f = pd.DataFrame(index=g.index)
        f["Especie"] = esp
        r_m, r_l = g["Mercado"].rolling(12).sum(), g["Venta Laboratorio"].rolling(12).sum()
        f["y_mercado"] = r_m / r_m.shift(12) - 1
        r_l = r_l.where(f.index >= LAB_INI)
        f["y_lab"] = r_l / r_l.shift(12) - 1
        f["ipc_yoy"] = g["IPC"] / g["IPC"].shift(12) - 1
        f["ipc_yoy_CA"] = f["ipc_yoy"] if esp == "CA" else 0.0
        f["pib"] = g["PIB"].rolling(12).mean()
        f["pib_agro"] = g["PIB Agro"].rolling(12).mean()
        f["smmlv"] = g["Porc Crec SMMLV"].rolling(12).mean()
        for k, c in PRECIOS.items():
            f[k] = yoy12(g[c]) if g[c].notna().any() else 0.0
        out.append(f.reset_index())
    return pd.concat(out, ignore_index=True)


def tabla(f, tarea, ini, fin):
    """Filas del modelo: meses t en [ini, fin] con todas las variables disponibles, con one-hot y crecimiento de hace 12 meses."""
    y = {"mercado": "y_mercado", "lab": "y_lab"}[tarea]
    cont = ["ipc_yoy", "ipc_yoy_CA", "pib", "pib_agro", "smmlv"] + list(PRECIOS) + (["y_mercado"] if tarea == "lab" else [])
    k = f[["Especie", "Fecha", y]].assign(Fecha=lambda x: x.Fecha + pd.DateOffset(years=1)).rename(columns={y: "lag12"})
    d = f.merge(k, on=["Especie", "Fecha"], how="left")
    d = d[(d.Fecha >= ini) & (d.Fecha <= fin)].dropna(subset=[y] + cont).copy()
    for e in ESPS:
        d[f"esp_{e}"] = (d.Especie == e).astype(int)
    return d.sort_values(["Fecha", "Especie"]).reset_index(drop=True)


def main():
    df = datos.leer_desarrollo()
    f = construir(df)
    for tarea, ini in (("mercado", "2021-12-01"), ("lab", "2023-12-01")):
        d = tabla(f, tarea, ini, C.CORTE)
        d.to_csv(C.DATA / f"features_desarrollo_{tarea}.csv", index=False)
        print(tarea, len(d), d.Fecha.min().date(), d.Fecha.max().date())


if __name__ == "__main__":
    main()
