"""Reune en informe_v2/cifras.json todas las cifras del informe tecnico (protocolo v2). Se ejecuta DESPUES de la prueba.
Uso: python informe_v2/construir_cifras.py  (desde la raiz del repositorio)"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.v2 import config as C, datos  # noqa: E402
from src.v2.exportar_simulador import evaluar  # noqa: E402
from src.v2.nucleo import TASKS  # noqa: E402

R = C.REP
rec = lambda f: pd.read_csv(R / f).astype(object).where(lambda x: x.notna(), None).to_dict("records")
out = {}

# ---------- ficha y calidad (fuente completa)
raw = pd.read_csv(C.FUENTE, encoding="utf-8-sig", dtype=str)
t = datos._tipar(raw.copy())
tipos = {"Especie": "Categórica", "Segmento": "Categórica", "Año": "Entera", "Subgrupo": "Categórica", "Mes": "Categórica (nombre del mes)",
         "Mercado": "Numérica (COP; texto con comas)", "Crec Mercado Q movil": "Fracción (crecimiento 12 meses sobre trimestre móvil)",
         "Crec Mercado Año": "Fracción (definición no reconciliable)", "Fecha": "Fecha (dd/mm/aaaa)", "Compite Laboraorio": "Categórica binaria (SI/NO)",
         "Precio Leche": "Numérica (COP/litro)", "Precio Carne Res": "Numérica (COP/kg, ganado en pie)", "Precio carne cerdo": "Numérica (COP/kg, cerdo en pie)",
         "Precio huevo": "Numérica (COP)", "Precio Pollo": "Numérica (COP/kg)", "Perros": "Entera (texto con comas)", "Gatos": "Entera (texto con comas)",
         "IPC": "Numérica (índice)", "Inflación Mensual": "Numérica (fracción)", "PIB": "Numérica (% anual)", "PIB Agro": "Numérica (% anual)",
         "Porc Crec SMMLV": "Numérica (fracción)", "Venta Laboratorio": "Numérica (COP; texto con comas)", "Share Laboratorio": "Numérica (fracción)",
         "Crec Laboratorio año": "Fracción (crecimiento anual de la venta)"}
out["ficha"] = [{"columna": c, "tipo": tipos[c], "faltantes": int(raw[c].isna().sum()), "pct": float(raw[c].isna().mean() * 100), "unicos": int(raw[c].nunique())} for c in raw.columns]
m, vl, sh = t["Mercado"], t["Venta Laboratorio"], t["Share Laboratorio"]
k = ["Especie", "Segmento", "Subgrupo"]
out["datos"] = {"filas": int(len(raw)), "columnas": int(raw.shape[1]), "fecha_min": t.Fecha.min().strftime("%Y-%m"), "fecha_max": t.Fecha.max().strftime("%Y-%m"),
                "meses": int(t.Fecha.nunique()), "series": int(t.groupby(k).ngroups), "subgrupos": int(t.Subgrupo.nunique()),
                "mercado_cero": int((m == 0).sum()), "lab_negativas": int((vl < 0).sum()), "lab_mayor_mercado": int((vl > m).sum()), "share_mayor_1": int((sh > 1).sum()),
                "lab_filas_con_venta": {int(y): int(((vl != 0) & (t.Año == y)).sum()) for y in range(2020, 2027)},
                "compite_filas_si": int((t["Compite_Laboratorio"] == "SI").sum()), "compite_series_marcadas_en_algun_mes": int(t.groupby(k).Compite_Laboratorio.apply(lambda s: (s == "SI").any()).sum()),
                "compite_series_cambian": int((t.groupby(k).Compite_Laboratorio.nunique() > 1).sum()),
                "compite_venta_lab_en_no": float(t[t.Compite_Laboratorio == "NO"]["Venta Laboratorio"].abs().sum()),
                "segmentos_por_especie": {e: sorted(g.Segmento.unique().tolist()) for e, g in t.groupby("Especie")},
                "crec_mercado_q_coincide": None}
sp = t.assign(c=t.Compite_Laboratorio).groupby(["Especie", "c"]).Mercado.sum().unstack()
out["datos"]["pct_mercado_compite"] = {e: float(sp.loc[e, "SI"] / sp.loc[e].sum() * 100) for e in sp.index}
pob = t.groupby("Fecha")[["Perros", "Gatos"]].first().dropna()
pa = pob.groupby(pob.index.year).first()
out["pob"] = {"perros": {int(y): float(v) for y, v in pa.Perros.items()}, "gatos": {int(y): float(v) for y, v in pa.Gatos.items()},
              "crecimiento": {int(y): float(v) for y, v in (pa.Perros.pct_change() * 100).dropna().items()}, "minsalud_2019": {"perros": 6403444, "gatos": 1938517},
              "minsalud_2017": {"perros": 5206617, "gatos": 1630828}, "factor_2020": float(pa.Perros.iloc[0] / 6403444)}
# ---------- desarrollo por tarea
out["tareas"] = {}
for task in TASKS:
    out["tareas"][task] = {"seleccion": json.loads((R / f"seleccion_{task}.json").read_text()), "comparacion_cv": rec(f"comparacion_cv_{task}.csv"), "desbalance": rec(f"desbalance_{task}.csv"),
                           "pliegues": rec(f"pliegues_{task}.csv"), "efecto_balance": rec(f"efecto_balance_{task}.csv"), "sens_validacion": rec(f"sensibilidad_validacion_{task}.csv"),
                           "curva_aprendizaje": rec(f"curva_aprendizaje_{task}.csv"), "curva_regularizacion": rec(f"curva_regularizacion_{task}.csv"),
                           "umbral": rec(f"umbral_{task}.csv"), "oof_especie": rec(f"oof_por_especie_{task}.csv"), "cv_grid": rec(f"cv_grid_{task}.csv")}
bo, ar = {}, {}
for task in TASKS:
    b = pd.read_csv(R / f"curva_boosting_{task}.csv")
    i = int(b.MAE_cv.idxmin())
    bo[task] = {"mejor_iter": int(b.iteracion[i]), "mae_min": float(b.MAE_cv[i]), "mae_50": float(b.MAE_cv[49]), "mae_400": float(b.MAE_cv.iloc[-1]), "mae_train_400": float(b.MAE_entrenamiento.iloc[-1]), "elegida": int(b.elegida.iloc[0])}
    a_ = pd.read_csv(R / f"curva_arboles_{task}.csv")
    ar[task] = {m: {int(n): float(v) for n, v in zip(g.n_arboles, g.MAE_cv)} for m, g in a_.groupby("modelo")}
out["boosting"], out["arboles"] = bo, ar
out["screening"] = rec("screening_resumen.csv")
out["importancia"] = rec("importancia_variables.csv")
out["prueba"] = json.loads((R / "prueba_resultados.json").read_text())
out["prueba_compl"] = json.loads((R / "prueba_complementaria.json").read_text())
out["locks"] = {"principal": (R / "prueba_consultada.lock").read_text().strip(), "complementaria": (R / "prueba_complementaria.lock").read_text().strip()}
out["accesos"] = [l.split("\t") for l in (R / "accesos_prueba.log").read_text().splitlines()]
out["manifiesto"] = json.loads((C.DATA / "manifiesto.json").read_text())
out["verificacion"] = (R / "verificacion_sello.txt").read_text()
out["proy"] = {"A": rec("proyeccion_2027_base.csv"), "B": rec("proyeccion_2027_alt.csv")}
out["bandas"] = {"A": json.loads((R / "bandas_error.json").read_text())}
sim = json.loads((C.ROOT / "simulador" / "modelo_v2.json").read_text())
out["bandas"]["B"] = sim["bandas"]["B"]
out["base"] = json.loads((R / "base_2027.json").read_text())
out["comparacion"] = sim["comparacion"]
out["historia"] = sim["historia"]
out["pesos"] = sim["pesos"]
# ---------- sensibilidad 2027 de ambos modelos (cambios en el escenario base)
base, A, B = out["base"], sim["modelos"]["A"], sim["modelos"]["B"]
ESPS = sim["especies"]
PR = {"var_leche": "Cattle", "var_res": "Cattle", "var_cerdo": "Swine", "var_huevo": "Poultry", "var_pollo": "Poultry"}


def feats(s, e, ym=None):
    r = {"ipc_yoy": s["ipc"], "ipc_yoy_CA": s["ipc"] if e == "CA" else 0.0, "pib": s["pib"], "pib_agro": s["pib_agro"], "smmlv": s["smmlv"]}
    for kk, esp in PR.items():
        r["real_" + kk] = (1 + s["nominal"][kk]) / (1 + s["ipc"]) - 1 if esp == e else 0.0
    if ym is not None:
        r["y_mercado"] = ym
    return r


def total(g, s, key):
    res = {}
    for e in ESPS:
        mm = evaluar(g["mercado"], feats(s, e), e)
        res[e] = (mm, evaluar(g["lab"], feats(s, e, mm), e))
    w = base["pesos"]["mercado" if key == 0 else "lab"]
    return sum(w[e] * res[e][key] for e in ESPS) * 100


sens = []
for nombre, kk, paso in [("Inflación +1 punto", "ipc", .01), ("PIB +1 punto", "pib", 1.0), ("PIB agropecuario +1 punto", "pib_agro", 1.0), ("Salario mínimo +1 punto", "smmlv", .01)] + \
        [(f"Cambio nominal del precio {n} +10 puntos", p, .10) for p, n in (("var_res", "de la carne de res"), ("var_leche", "de la leche"), ("var_cerdo", "de la carne de cerdo"), ("var_huevo", "del huevo"), ("var_pollo", "del pollo"))]:
    s2 = json.loads(json.dumps(base))
    if kk in s2["nominal"]:
        s2["nominal"][kk] += paso
    else:
        s2[kk] += paso
    fila = {"variable": nombre}
    for gn, g in (("A", A), ("B", B)):
        for key, kn in ((0, "mercado"), (1, "lab")):
            fila[f"{gn}_{kn}"] = total(g, s2, key) - total(g, base, key)
    sens.append(fila)
out["sens"] = sens
(ROOT / "informe_v2" / "cifras.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float).replace("NaN", "null"))
print("ok", len(json.dumps(out, default=float)) // 1024, "KB")
