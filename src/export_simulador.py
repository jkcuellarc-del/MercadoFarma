"""Exporta el modelo final (Ridge por especie) a un JSON para el simulador web.

El simulador es una pagina de un solo archivo: calcula en el navegador con los coeficientes,
medias y desviaciones exportados aqui. Solo contiene porcentajes y pesos relativos (no ventas).
Salida: simulador/modelo.json
Escenario base 2027 (fuentes externas, septiembre-octubre 2026):
  IPC 5,1%   mediana encuesta de analistas del Banco de la Republica para dic-2027
  PIB 2,3%   BBVA Research (consenso de analistas 1,8%-2,6%)
  PIB agro   promedio 2020-2025 (sin pronostico publico)
  SMMLV      promedio de aumentos 2022-2025 (sin pronostico publico)
  precios    se mantienen en su nivel de junio 2026 durante 2027
"""
import json
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).resolve().parent))
import final_model as F  # noqa: E402
import lab_experimento as L  # noqa: E402

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
PROC, MODELS = ROOT / "data" / "processed", ROOT / "models"
ESP = F.ESPECIES
PRECIOS = list(F.PRECIOS)


def band_errors():
    """MAE (pp) por especie en validacion y prueba; laboratorio con mercado proyectado."""
    dm = pd.read_csv(PROC / "model_mercado_scaled.csv")
    dl = pd.read_csv(PROC / "model_lab_scaled.csv")
    raw_l = pd.read_csv(PROC / "model_lab.csv")
    Xm, Xl = F.features_of("mercado"), F.features_of("lab")
    sc = joblib.load(MODELS / "scaler_lab.joblib")
    i = sc["columns"].index("y_mercado")
    mu, sd = sc["scaler"].mean_[i], sc["scaler"].scale_[i]
    dl["yhat"] = L.market_pred(dl)
    out = {e: {} for e in ESP}
    for part, fit_s in (("validacion", ["train"]), ("prueba", ["train", "validacion"])):
        for e in ESP:
            a = dm[(dm.Especie == e) & dm.split.isin(fit_s)]
            b = dm[(dm.Especie == e) & (dm.split == part)]
            m = Ridge(alpha=F.ALPHA["mercado"]).fit(a[Xm], a.y_mercado)
            out[e][f"mercado_{part}"] = float(np.abs(m.predict(b[Xm]) - b.y_mercado).mean() * 100)
            a = dl[(dl.Especie == e) & dl.split.isin(fit_s)]
            b = dl[(dl.Especie == e) & (dl.split == part)].copy()
            m = Ridge(alpha=F.ALPHA["lab"]).fit(a[Xl], a.y_lab)
            b["y_mercado"] = (b["yhat"] - mu) / sd
            out[e][f"lab_{part}"] = float(np.abs(m.predict(b[Xl]) - b.y_lab).mean() * 100)
    return out


def main():
    models = {"mercado": F.fit("mercado", "y_mercado"), "lab": F.fit("lab", "y_lab")}
    base = F.base_inputs()
    ann = pd.read_csv(PROC / "annual_especie.csv")
    agro = ann[ann.Año.between(2020, 2025)].drop_duplicates("Año").set_index("Año").PIB_Agro.mean()
    for e in ESP:
        base[e]["ipc_yoy"] = 0.051
        base[e]["pib"] = 2.3
        base[e]["pib_agro"] = float(round(agro, 2))
    raw = pd.read_csv(PROC / "model_mercado.csv")
    raw = raw[raw.split.isin(["train", "validacion", "prueba"])]
    out = {"especies": ESP, "base": {e: {k: float(v) for k, v in base[e].items()} for e in ESP}, "modelos": {}}
    for nm in ("mercado", "lab"):
        X, mod = models[nm]
        sc = joblib.load(MODELS / f"scaler_{nm}.joblib")
        cols = sc["columns"]
        out["modelos"][nm] = {
            "mean": dict(zip(cols, map(float, sc["scaler"].mean_))),
            "scale": dict(zip(cols, map(float, sc["scaler"].scale_))),
            "features": X,
            "especies": {e: {"intercept": float(m.intercept_), "coef": dict(zip(X, map(float, m.coef_)))}
                         for e, m in mod.items()},
        }
    out["rangos"] = {e: {c: [float(raw[raw.Especie == e][c].min()), float(raw[raw.Especie == e][c].max())]
                         for c in ["ipc_yoy", "pib", "pib_agro", "smmlv"] + PRECIOS} for e in ESP}
    a26 = ann[ann.Año == 2026].set_index("Especie")
    out["pesos"] = {"mercado": {e: float(a26.loc[e, "Mercado"] / a26.Mercado.sum()) for e in ESP},
                    "lab": {e: float(a26.loc[e, "Venta_Laboratorio"] / a26.Venta_Laboratorio.sum()) for e in ESP}}
    h = ann[(ann.Año >= 2022)]
    out["historia"] = {"mercado": {e: {int(r.Año): (None if pd.isna(r.Crec_Mercado) else float(r.Crec_Mercado))
                                       for r in h[h.Especie == e].itertuples()} for e in ESP},
                       "lab": {e: {int(r.Año): (None if pd.isna(r.Crec_Lab) else float(r.Crec_Lab))
                                   for r in h[h.Especie == e].itertuples()} for e in ESP}}
    out["error_pp"] = band_errors()
    # historia total ponderada (mercado y laboratorio)
    tot = ann.groupby("Año")[["Mercado", "Venta_Laboratorio"]].sum().pct_change()
    out["historia"]["mercado"]["Total"] = {int(y): float(v) for y, v in tot.Mercado.items() if y >= 2022}
    out["historia"]["lab"]["Total"] = {int(y): (float(v) if y >= 2023 else None)
                                      for y, v in tot.Venta_Laboratorio.items() if y >= 2022}
    (ROOT / "simulador").mkdir(exist_ok=True)
    (ROOT / "simulador" / "modelo.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({"base": out["base"], "error_pp": out["error_pp"], "pesos": out["pesos"]}, indent=1))
    # verificacion contra la proyeccion de Python
    inp = {e: {k: float(v) for k, v in base[e].items()} for e in ESP}
    print(F.project(inp, models)[["Especie", "crec_mercado", "crec_lab", "escenario_mercado", "escenario_lab"]])


if __name__ == "__main__":
    main()
