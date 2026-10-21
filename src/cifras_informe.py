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
out["lock"] = (R / "prueba_consultada.lock").read_text().strip()
(ROOT / "informe" / "cifras.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float))
print("ok", len(json.dumps(out)) // 1024, "KB")
