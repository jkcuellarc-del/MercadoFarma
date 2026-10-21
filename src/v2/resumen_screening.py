"""Resume el cribado de predictores: mejor modelo por combinacion y comparacion pareada contra S0 nominal."""
import json

import numpy as np
import pandas as pd

from . import config as C


def main():
    s = pd.read_csv(C.REP / "screening_predictores.csv")
    s["folds"] = s["folds"].apply(lambda x: json.loads(x) if isinstance(x, str) else None)
    filas = []
    for task, g in s.groupby("tarea"):
        mod = g[g.conjunto != "base"]
        ref = mod[(mod.objetivo == "nominal") & (mod.conjunto == "S0_actual")].sort_values("MAE_cv").iloc[0]
        for (obj, cj), h in mod.groupby(["objetivo", "conjunto"]):
            b = h.sort_values("MAE_cv").iloc[0]
            diff = np.array(b.folds) - np.array(ref.folds)
            se = diff.std(ddof=1) / np.sqrt(len(diff))
            filas.append({"tarea": task, "objetivo": obj, "conjunto": cj, "mejor_modelo": b.modelo, "MAE_cv": b.MAE_cv, "R2_oof": b.R2_oof,
                          "dif_vs_S0_nominal": diff.mean(), "SE_dif": se, "mejora_clara": bool(diff.mean() < -se),
                          "pliegues_que_mejoran": int((diff < 0).sum()), "n_pliegues": len(diff)})
        for nm in ("B0_media_global", "B2_media_especie"):
            b = g[g.modelo == nm].iloc[0]
            filas.append({"tarea": task, "objetivo": "nominal", "conjunto": "base", "mejor_modelo": nm, "MAE_cv": b.MAE_cv, "R2_oof": b.R2_oof})
    r = pd.DataFrame(filas)
    r.to_csv(C.REP / "screening_resumen.csv", index=False)
    pd.set_option("display.width", 230, "display.max_columns", 20, "display.float_format", "{:,.2f}".format)
    print(r.to_string(index=False))


if __name__ == "__main__":
    main()
