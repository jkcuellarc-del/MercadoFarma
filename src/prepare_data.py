"""Limpieza de la base y completado estacional de julio-diciembre 2026.

Entrada : Base Mercado Salud Animal.csv (formato largo: subgrupo x mes)
Salidas : data/processed/monthly_clean.csv       base limpia (sin 2026 H2)
          data/processed/monthly_especie.csv     mensual por especie, 2026 H2 completado
          data/processed/annual_especie.csv      anual por especie con variables explicativas
          data/processed/backtest_completado.csv error del completado en H2 2023-2025

Decisiones del negocio:
  - Ventas negativas del laboratorio son devoluciones validas: se conservan.
  - Se modela crecimiento nominal (el IPC es una variable que elige el usuario).
  - Poultry -20% en 2026 y share alto de Swine son reales: no se corrigen.
  - Julio-diciembre 2026 se completa con un ensamble de tres modelos estacionales.
"""
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "Base Mercado Salud Animal.csv"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

LAST_REAL = pd.Timestamp("2026-06-01")
LAB_START = 2022  # 2020 en cero y 2021 casi vacio: la historia real inicia en 2022
PRECIOS = ["Precio Leche", "Precio Carne Res", "Precio carne cerdo", "Precio huevo", "Precio Pollo"]
MACRO_ANUAL = ["PIB", "PIB Agro", "Porc Crec SMMLV"]
CRECS = ["Crec Mercado Q movil", "Crec Mercado Año", "Crec Laboratorio año"]


def load():
    df = pd.read_csv(RAW, thousands=",", encoding="utf-8-sig")
    df = df.dropna(subset=["Año"]).drop_duplicates().copy()
    df["Año"] = df["Año"].astype(int)
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y")
    for c in CRECS:  # vienen como texto "12.3%"
        df[c] = pd.to_numeric(df[c].str.rstrip("%"), errors="coerce") / 100
    return df


# ---------- completado estacional ----------
def fc_ratio(s, y, yrs=3):
    """H2 = H1 * promedio(H2/H1) de los ultimos `yrs` anios."""
    r = []
    for k in range(1, yrs + 1):
        h1 = s[(s.index.year == y - k) & (s.index.month <= 6)].sum()
        h2 = s[(s.index.year == y - k) & (s.index.month > 6)].sum()
        if h1 > 0 and h2 > 0:
            r.append(h2 / h1)
    return s[(s.index.year == y) & (s.index.month <= 6)].sum() * np.mean(r)


def fc_yoy(s, y):
    """H2 = H2 del anio previo * (H1 actual / H1 previo)."""
    h1 = s[(s.index.year == y) & (s.index.month <= 6)].sum()
    h1p = s[(s.index.year == y - 1) & (s.index.month <= 6)].sum()
    h2p = s[(s.index.year == y - 1) & (s.index.month > 6)].sum()
    return h2p * h1 / h1p


def fc_ets(s):
    m = ExponentialSmoothing(
        s, trend="add", damped_trend=True,
        seasonal="mul" if (s > 0).all() else "add", seasonal_periods=12,
    ).fit()
    return m.forecast(6).sum()


def h2_total(s, y):
    """Total de jul-dic del anio y (s solo llega a junio de y). Ensamble de 3 metodos."""
    return np.mean([fc_ratio(s, y), fc_yoy(s, y), fc_ets(s)])


def complete_h2(s, y):
    """Devuelve 6 meses jul-dic de y: total del ensamble repartido con el patron
    estacional de los ultimos 3 anios (peso de cada mes dentro de H2)."""
    tot = h2_total(s, y)
    w = np.zeros(6)
    for k in (1, 2, 3):
        h = s[(s.index.year == y - k) & (s.index.month > 6)].to_numpy()
        w += h / h.sum()
    w /= 3
    idx = pd.date_range(f"{y}-07-01", periods=6, freq="MS")
    return pd.Series(tot * w, index=idx)


def backtest(especie_m):
    rows = []
    for var, years in (("Mercado", (2023, 2024, 2025)), ("Venta Laboratorio", (2024, 2025))):
        for esp in especie_m.columns.levels[1]:
            s = especie_m[(var, esp)]
            if var == "Venta Laboratorio":
                s = s[s.index.year >= LAB_START]
            for y in years:
                tr = s[s.index <= pd.Timestamp(f"{y}-06-01")]
                act = s[(s.index.year == y) & (s.index.month > 6)].sum()
                est = h2_total(tr, y)
                rows.append(dict(variable=var, especie=esp, año=y, real_h2=act, estimado_h2=est,
                                 error_pct=(est / act - 1) * 100))
    return pd.DataFrame(rows)


def main():
    df = load()
    df.to_csv(OUT / "monthly_clean.csv", index=False)

    # mensual por especie
    m = df.groupby(["Fecha", "Especie"])[["Mercado", "Venta Laboratorio"]].sum().unstack("Especie")
    m.index.name = None
    bt = backtest(m)
    bt.to_csv(OUT / "backtest_completado.csv", index=False)

    # completar 2026 H2
    filas = {}
    for esp in m["Mercado"].columns:
        mk = complete_h2(m[("Mercado", esp)], 2026)
        lb = complete_h2(m[("Venta Laboratorio", esp)][m.index.year >= LAB_START], 2026)
        for f in mk.index:
            filas[(f, esp)] = (mk[f], lb[f])
    est = pd.DataFrame(filas, index=["Mercado", "Venta Laboratorio"]).T
    est.index.names = ["Fecha", "Especie"]
    est = est.reset_index()
    est["Estimado"] = True

    real = m.stack("Especie", future_stack=True).reset_index()
    real.columns = ["Fecha", "Especie", "Mercado", "Venta Laboratorio"]
    real["Estimado"] = False
    me = pd.concat([real, est], ignore_index=True).sort_values(["Especie", "Fecha"])

    # variables explicativas mensuales (macro nacional + precios por especie)
    nac = (df.groupby("Fecha")[["IPC", "Inflación Mensual"] + MACRO_ANUAL].first())
    pre = df.groupby(["Fecha", "Especie"])[PRECIOS + ["Perros", "Gatos"]].first().reset_index()
    me = me.merge(nac.reset_index(), on="Fecha", how="left").merge(pre, on=["Fecha", "Especie"], how="left")

    # H2 2026 de variables exogenas (supuesto, el usuario las elige en el simulador):
    #   IPC: inflacion mensual de 2025 repetida mes a mes; macro anual: valor 2026;
    #   precios: H2 2025 * (H1 2026 / H1 2025); poblacion perros/gatos: valor 2026.
    me = me.sort_values(["Especie", "Fecha"]).reset_index(drop=True)
    infl25 = nac.loc["2025-07-01":"2025-12-01", "Inflación Mensual"].to_numpy()
    ipc = nac.loc[LAST_REAL, "IPC"]
    ipc_h2 = {}
    for f, i in zip(pd.date_range("2026-07-01", periods=6, freq="MS"), infl25):
        ipc = ipc * (1 + i)
        ipc_h2[f] = (ipc, i)
    for f, (v, i) in ipc_h2.items():
        me.loc[me.Fecha == f, "IPC"] = v
        me.loc[me.Fecha == f, "Inflación Mensual"] = i
    for c in MACRO_ANUAL:
        me[c] = me.groupby(me.Fecha.dt.year)[c].transform(lambda x: x.ffill().bfill())
    for c in PRECIOS + ["Perros", "Gatos"]:
        for esp, g in me.groupby("Especie"):
            if g[c].notna().sum() == 0:
                continue
            if c in ("Perros", "Gatos"):
                v = g.loc[g.Fecha == LAST_REAL, c].iloc[0]
                me.loc[(me.Especie == esp) & (me.Fecha > LAST_REAL), c] = v
            else:
                k = (g.loc[g.Fecha.between("2026-01-01", LAST_REAL), c].sum()
                     / g.loc[g.Fecha.between("2025-01-01", "2025-06-01"), c].sum())
                for f in pd.date_range("2026-07-01", periods=6, freq="MS"):
                    prev = g.loc[g.Fecha == f - pd.DateOffset(years=1), c].iloc[0]
                    me.loc[(me.Especie == esp) & (me.Fecha == f), c] = prev * k
    me.to_csv(OUT / "monthly_especie.csv", index=False)

    # anual por especie
    a = me.assign(Año=me.Fecha.dt.year).groupby(["Especie", "Año"]).agg(
        Mercado=("Mercado", "sum"), Venta_Laboratorio=("Venta Laboratorio", "sum"),
        IPC_prom=("IPC", "mean"), IPC_dic=("IPC", "last"),
        PIB=("PIB", "first"), PIB_Agro=("PIB Agro", "first"), SMMLV=("Porc Crec SMMLV", "first"),
        Leche=("Precio Leche", "mean"), Carne_Res=("Precio Carne Res", "mean"),
        Carne_Cerdo=("Precio carne cerdo", "mean"), Huevo=("Precio huevo", "mean"),
        Pollo=("Precio Pollo", "mean"), Perros=("Perros", "first"), Gatos=("Gatos", "first"),
        Estimado=("Estimado", "any"),
    ).reset_index().sort_values(["Especie", "Año"])
    g = a.groupby("Especie")
    a["Crec_Mercado"] = g["Mercado"].pct_change()
    a["Crec_Lab"] = g["Venta_Laboratorio"].pct_change()
    a.loc[a["Año"] <= LAB_START, "Crec_Lab"] = np.nan
    a["Share_Lab"] = a["Venta_Laboratorio"] / a["Mercado"]
    a["Inflacion_anual"] = g["IPC_prom"].pct_change()
    for c in ["Leche", "Carne_Res", "Carne_Cerdo", "Huevo", "Pollo", "Perros", "Gatos"]:
        a["Var_" + c] = g[c].pct_change()
    a["Escenario_Mercado"] = pd.cut(a["Crec_Mercado"], [-np.inf, .08, .15, np.inf],
                                    labels=["regular", "estable", "optimista"], right=False)
    a["Escenario_Lab"] = pd.cut(a["Crec_Lab"], [-np.inf, .08, .15, np.inf],
                                labels=["regular", "estable", "optimista"], right=False)
    a.to_csv(OUT / "annual_especie.csv", index=False)

    pd.set_option("display.width", 250, "display.max_columns", 40, "display.float_format", "{:,.3f}".format)
    print(bt.groupby("variable").error_pct.agg(["mean", lambda x: x.abs().mean()]))
    print(a[["Especie", "Año", "Mercado", "Venta_Laboratorio", "Crec_Mercado", "Crec_Lab", "Share_Lab",
             "Inflacion_anual", "Estimado", "Escenario_Mercado", "Escenario_Lab"]].to_string())
    tot = a.groupby("Año")[["Mercado", "Venta_Laboratorio"]].sum()
    print(tot.pct_change())


if __name__ == "__main__":
    main()
