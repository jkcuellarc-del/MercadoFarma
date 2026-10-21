"""Reune en informe/cifras.json todas las cifras que cita el informe (para que no se digiten a mano)."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "reports" / "protocolo"
rec = lambda f: pd.read_csv(R / f).where(lambda x: x.notna(), None).to_dict("records")
out = json.loads((ROOT / "informe" / "datos_informe.json").read_text())
for t in ("mercado", "lab"):
    out[t] = {
        "seleccion": json.loads((R / f"seleccion_{t}.json").read_text()),
        "comparacion_cv": rec(f"comparacion_cv_{t}.csv"), "cv_grid": rec(f"cv_grid_{t}.csv"), "desbalance": rec(f"desbalance_{t}.csv"),
        "pliegues": rec(f"pliegues_{t}.csv"), "efecto_balance": rec(f"efecto_balance_{t}.csv"), "sens_validacion": rec(f"sensibilidad_validacion_{t}.csv"),
        "curva_aprendizaje": rec(f"curva_aprendizaje_{t}.csv"), "curva_regularizacion": rec(f"curva_regularizacion_{t}.csv"),
        "umbral": rec(f"umbral_{t}.csv"), "oof_especie": rec(f"oof_por_especie_{t}.csv"),
    }
out["prueba"] = json.loads((R / "prueba_resultados.json").read_text())
out["proyeccion"] = rec("proyeccion_2027_base.csv")
out["sens2027"] = rec("sensibilidad_2027.csv")
# metricas de la prueba recalculadas desde las predicciones guardadas de la consulta unica (cadena realista)
import numpy as np
pp = pd.read_csv(R / "prueba_predicciones.csv")
cls = lambda y: np.digitize(np.asarray(y, float), [0.08, 0.15])
cost = lambda r, p: np.where(np.asarray(p) - np.asarray(r) > 0, 2.0 * (np.asarray(p) - np.asarray(r)), -(np.asarray(p) - np.asarray(r)))
prc = {}
for t in ("mercado", "lab"):
    d = pp[pp.tarea == t]
    m_u = json.loads((R / f"seleccion_{t}.json").read_text())["m_umbral"]
    o = {"por_especie": {e: float(np.abs(g.pred - g.real).mean() * 100) for e, g in d.groupby("Especie")}}
    for nm, col in (("modelo", "pred"), ("B2", "B2")):
        for lab, m in (("m0", 0.0), ("mstar", m_u)):
            cr, cp = cls(d.real), cls(d[col] - m)
            o[f"{nm}_{lab}"] = {"acierto": float((cr == cp).mean()), "costo": float(cost(cr, cp).mean()), "recall_regular": float((cp[cr == 0] == 0).mean()) if (cr == 0).any() else None,
                                "n_regular": int((cr == 0).sum()), "matriz": [[int(((cr == i) & (cp == j)).sum()) for j in range(3)] for i in range(3)]}
    prc[t] = o
out["prueba_recalculada"] = prc
a = pd.read_csv(ROOT / "data" / "processed" / "annual_especie.csv"); a = a[a.Año == 2026].set_index("Especie")
w = {"mercado": (a.Mercado / a.Mercado.sum()).to_dict(), "lab": (a.Venta_Laboratorio / a.Venta_Laboratorio.sum()).to_dict()}
band = {}
for t in ("mercado", "lab"):
    oo = {r["Especie"]: r["mean"] for r in out[t]["oof_especie"]}
    band[t] = {e: (oo[e] + prc[t]["por_especie"][e]) / 2 for e in oo}
    band[t]["Total"] = sum(w[t][e] * band[t][e] for e in oo)
out["banda"] = band
out["lock"] = (R / "prueba_consultada.lock").read_text().strip()
txt = json.dumps(out, indent=1, ensure_ascii=False, default=float).replace("NaN", "null")
(ROOT / "informe" / "cifras.json").write_text(txt)
print("ok", len(json.dumps(out)) // 1024, "KB")
