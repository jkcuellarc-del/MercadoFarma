"""Segunda consulta del examen, COMPLEMENTARIA e informativa: K vecinos, Random Forest y regresion lineal.

La evaluacion unica (prueba.py) midio el modelo elegido por la regla, el de menor error de CV y los metodos sencillos. Esta consulta
posterior mide otros tres modelos ya ajustados en desarrollo, con los mismos hiperparametros elegidos por validacion cruzada, y NO se usa
para seleccionar nada. Queda registrada en accesos_prueba.log y con su propio candado. Cada modelo usa su propia cadena
(el laboratorio recibe el crecimiento del mercado que proyecta el mismo modelo).
"""
import json
import sys
import time

import numpy as np
import pandas as pd

from . import config as C
from . import datos, variables
from .nucleo import *  # noqa: F401,F403

MODELOS = ("knn", "rf", "ols")


def main():
    lock = C.REP / "prueba_complementaria.lock"
    if lock.exists() and "--force" not in sys.argv:
        sys.exit(f"La consulta complementaria ya se hizo ({lock.read_text().strip()}).")
    res0 = json.loads((C.REP / "prueba_resultados.json").read_text())
    lv = res0["variante_lab"]
    sels = {t: json.loads((C.REP / f"seleccion_{t}.json").read_text()) for t in ("mercado", lv)}
    todo = pd.concat([datos.leer_desarrollo(), datos.leer_prueba("segunda consulta complementaria: K vecinos, Random Forest y regresion lineal")], ignore_index=True)
    f = variables.construir(todo, pd.read_csv(C.DATA / "series_compite.csv"))
    tm = {"tr": variables.tabla(f, "mercado", TASKS["mercado"]["ini"], C.CORTE), "te": variables.tabla(f, "mercado", C.PRUEBA_INI, C.PRUEBA_FIN)}
    tl = {"tr": variables.tabla(f, lv, TASKS[lv]["ini"], C.CORTE), "te": variables.tabla(f, lv, C.PRUEBA_INI, C.PRUEBA_FIN)}
    out = {}
    for kind in MODELOS:
        a = sels["mercado"]["mejores"][kind]
        pm = pipeline(kind, "mercado", a["balance"], **a["params"]).fit(tm["tr"][columnas("mercado")], tm["tr"][TASKS["mercado"]["y"]])
        gm = pm.predict(tm["te"][columnas("mercado")])
        ym = tm["te"][TASKS["mercado"]["y"]].to_numpy()
        b = sels[lv]["mejores"][kind]
        pl = pipeline(kind, lv, b["balance"], **b["params"]).fit(tl["tr"][columnas(lv)], tl["tr"][TASKS[lv]["y"]])
        X = tl["te"][columnas(lv)].copy()
        ph = pd.Series(gm, index=pd.MultiIndex.from_frame(tm["te"][["Fecha", "Especie"]]))
        X["y_mercado"] = ph.reindex(pd.MultiIndex.from_frame(tl["te"][["Fecha", "Especie"]])).to_numpy()
        gl = pl.predict(X)
        yl = tl["te"][TASKS[lv]["y"]].to_numpy()
        out[kind] = {"mercado": {**met(ym, gm), "R2": r2(ym, gm)}, "lab": {**met(yl, gl), "R2": r2(yl, gl)}, "variante_lab": lv}
        print(kind, {k: round(v["MAE_pp"], 2) for k, v in out[kind].items() if isinstance(v, dict)})
    (C.REP / "prueba_complementaria.json").write_text(json.dumps(out, indent=1, default=float))
    lock.write_text(time.strftime("%Y-%m-%d %H:%M:%S"))


if __name__ == "__main__":
    main()
