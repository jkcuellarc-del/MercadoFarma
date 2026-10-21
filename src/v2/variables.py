"""Variables de 12 meses moviles, a partir de un DataFrame ya tipado (desarrollo, o desarrollo + prueba).

Todas las variables en el mes t usan solo informacion hasta t, de modo que las filas con t <= CORTE
son identicas se construyan con o sin los meses de la prueba.
"""
import numpy as np
import pandas as pd

from . import config as C
from . import datos
from .nucleo import TASKS

PRECIOS = {"var_leche": "Precio Leche", "var_res": "Precio Carne Res", "var_cerdo": "Precio carne cerdo",
           "var_huevo": "Precio huevo", "var_pollo": "Precio Pollo"}
ESPS = ["CA", "Cattle", "Poultry", "Swine"]
LAB_INI = "2022-12-01"  # primera ventana de 12 meses 100% posterior al inicio de la historia del laboratorio


K = ["Especie", "Segmento", "Subgrupo"]


def series_compite(df):
    """Series donde el Laboratorio compite = marcadas 'SI' en algun mes del DESARROLLO.
    Se fija una sola vez a nivel de serie: en 4 series la marca cambia mes a mes con la venta del
    Laboratorio, y usarla mes a mes metería la venta propia dentro de la definicion del mercado."""
    s = df.assign(c=df["Compite_Laboratorio"] == "SI").groupby(K).c.any()
    return s[s].reset_index()[K]


def panel(df, comp):
    d = df.merge(comp.assign(_c=True), on=K, how="left")
    d["_c"] = d["_c"].fillna(False).astype(bool)
    m = d.groupby(["Fecha", "Especie"])[["Mercado", "Venta Laboratorio"]].sum()
    mc = d[d["_c"]].groupby(["Fecha", "Especie"])["Mercado"].sum().rename("Mercado_compite")
    nac = d.groupby("Fecha")[["IPC", "PIB", "PIB Agro", "Porc Crec SMMLV"]].first()
    pre = d.groupby(["Fecha", "Especie"])[list(PRECIOS.values())].first()
    return m.join(mc).join(pre).reset_index().merge(nac.reset_index(), on="Fecha")


def yoy12(s):
    r = s.rolling(12).mean()
    return r / r.shift(12) - 1


def construir(df, comp):
    out = []
    for esp, g in panel(df, comp).sort_values("Fecha").groupby("Especie"):
        g = g.set_index("Fecha")
        f = pd.DataFrame(index=g.index)
        f["Especie"] = esp
        r_m, r_l = g["Mercado"].rolling(12).sum(), g["Venta Laboratorio"].rolling(12).sum()
        f["y_mercado"] = r_m / r_m.shift(12) - 1
        r_c = g["Mercado_compite"].rolling(12).sum()
        f["y_compite"] = r_c / r_c.shift(12) - 1
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
    t = TASKS[tarea]
    y, cont = t["y"], t["cont"]
    k = f[["Especie", "Fecha", y]].assign(Fecha=lambda x: x.Fecha + pd.DateOffset(years=1)).rename(columns={y: "lag12"})
    d = f.merge(k, on=["Especie", "Fecha"], how="left")
    d = d[(d.Fecha >= ini) & (d.Fecha <= fin)].dropna(subset=[y] + cont).copy()
    for e in ESPS:
        d[f"esp_{e}"] = (d.Especie == e).astype(int)
    return d.sort_values(["Fecha", "Especie"]).reset_index(drop=True)


def main():
    df = datos.leer_desarrollo()
    comp = series_compite(df)
    comp.to_csv(C.DATA / "series_compite.csv", index=False)
    f = construir(df, comp)
    for tarea, t in TASKS.items():
        d = tabla(f, tarea, t["ini"], C.CORTE)
        d.to_csv(C.DATA / f"features_desarrollo_{tarea}.csv", index=False)
        print(tarea, len(d), d.Fecha.min().date(), d.Fecha.max().date())
    print("series donde compite el Laboratorio:", len(comp))


if __name__ == "__main__":
    main()
