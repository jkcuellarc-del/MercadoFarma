"""Etapa de PRUEBA: una sola evaluacion sobre enero-junio 2026.

Es el unico modulo que abre los datos sellados (datos.leer_prueba deja registro de cada acceso).
Se ejecuta despues de congelar la seleccion del desarrollo (reports/v2/seleccion_*.json) y deja un
candado: una segunda ejecucion exige --force y queda documentada como segunda consulta.
Los parametros del modelo (escalador, coeficientes, descuento m) salen solo del entrenamiento (t <= 2025-12).
"""
import json
import sys
import time

import numpy as np
import pandas as pd

from . import config as C
from . import datos, variables
from .nucleo import *  # noqa: F401,F403


def main():
    lock = C.REP / "prueba_consultada.lock"
    if lock.exists() and "--force" not in sys.argv:
        sys.exit(f"La prueba ya fue consultada ({lock.read_text().strip()}). Protocolo: una sola consulta.")
    sels = {k: json.loads((C.REP / f"seleccion_{k}.json").read_text()) for k in TASKS}
    # variante del modelo del laboratorio, definida en desarrollo: la de menor MAE de CV del modelo elegido
    lab_var = min(("lab", "lab_ym"), key=lambda k: sels[k]["MAE_cv_final"])
    tareas = ["mercado", "compite", lab_var]
    dev = datos.leer_desarrollo()
    todo = pd.concat([dev, datos.leer_prueba("evaluacion unica de prueba")], ignore_index=True)
    comp = pd.read_csv(C.DATA / "series_compite.csv")  # definido solo con desarrollo
    f = variables.construir(todo, comp)
    res, preds, modelos = {"variante_lab": lab_var}, [], {}
    feat_cadena = {"lab": ("y_compite", "compite"), "lab_ym": ("y_mercado", "mercado")}
    for task in tareas:
        sel, t = sels[task], TASKS[task]
        tr = variables.tabla(f, task, t["ini"], C.CORTE)
        te = variables.tabla(f, task, C.PRUEBA_INI, C.PRUEBA_FIN)
        ref = pd.read_csv(C.DATA / f"features_desarrollo_{task}.csv", parse_dates=["Fecha"])
        assert len(tr) == len(ref) and np.allclose(tr[columnas(task)].to_numpy(float), ref[columnas(task)].to_numpy(float)), "El entrenamiento cambio al agregar la prueba"
        pipe = pipeline(sel["final"], task, sel["balance"], **sel["params"]).fit(tr[columnas(task)], tr[t["y"]])
        modelos[task] = pipe
        y = te[t["y"]].to_numpy()
        X = te[columnas(task)].copy()
        if task in feat_cadena:  # cadena realista: el crecimiento del mercado entra proyectado, no observado
            col, origen = feat_cadena[task]
            tm = variables.tabla(f, origen, C.PRUEBA_INI, C.PRUEBA_FIN)
            ph = pd.Series(modelos[origen].predict(tm[columnas(origen)]), index=pd.MultiIndex.from_frame(tm[["Fecha", "Especie"]]))
            X[col] = ph.reindex(pd.MultiIndex.from_frame(te[["Fecha", "Especie"]])).to_numpy()
        p = pipe.predict(X)
        mu = tr.groupby("Especie")[t["y"]].mean()
        pb2 = te.Especie.map(mu).to_numpy()
        pb1 = te.lag12.to_numpy()
        ok = ~np.isnan(pb1)
        mstar = sel["m_umbral"]
        r = {"modelo_final": sel["nombre"], "n": int(len(te)), **met(y, p), "R2": r2(y, p),
             "B2_media_especie": {**met(y, pb2), "R2": r2(y, pb2)}, "B1_crecimiento_hace_12m": {**met(y[ok], pb1[ok]), "n": int(ok.sum())},
             "por_especie": {e: met(y[(te.Especie == e).to_numpy()], p[(te.Especie == e).to_numpy()]) for e in ESPS}, "m_umbral": mstar}
        for nm, q in (("modelo", p), ("B2", pb2)):
            for lab, m in (("m0", 0.0), ("mstar", mstar)):
                r[f"{nm}_{lab}"] = met_clase(y, q, m)
        if task in feat_cadena:  # referencia: con el mercado observado (no es lo que ocurrira en 2027)
            r["con_mercado_observado"] = met(y, pipe.predict(te[columnas(task)]))
        # informativo, declarado antes de la consulta: el modelo de menor MAE de CV si difiere del elegido por la regla de parsimonia.
        # No cambia la seleccion.
        alt = min(sel["mejores"], key=lambda k: sel["mejores"][k]["MAE_cv"])
        pq = None
        if alt != sel["final"]:
            ma = sel["mejores"][alt]
            pq = pipeline(alt, task, ma["balance"], **ma["params"]).fit(tr[columnas(task)], tr[t["y"]]).predict(X)
            r["alternativa_mejor_cv"] = {"modelo": NOMBRES[alt], "clave": alt, **met(y, pq), "R2": r2(y, pq),
                                         "m0": met_clase(y, pq, 0.0),
                                         "por_especie": {e: met(y[(te.Especie == e).to_numpy()], pq[(te.Especie == e).to_numpy()]) for e in ESPS}}
        res[task] = r
        preds.append(pd.DataFrame({"tarea": task, "Fecha": te.Fecha, "Especie": te.Especie, "real": y, "pred": p, "pred_alt": pq if pq is not None else np.nan, "B2": pb2, "B1": pb1}))
    (C.REP / "prueba_resultados.json").write_text(json.dumps(res, indent=1, default=float))
    pd.concat(preds).to_csv(C.REP / "prueba_predicciones.csv", index=False)
    lock.write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
    for k, v in res.items():
        if k == "variante_lab":
            continue
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if a in ("modelo_final", "n", "MAE_pp", "RMSE_pp", "sesgo_pp")},
              "B2", round(v["B2_media_especie"]["MAE_pp"], 2), "B1", round(v["B1_crecimiento_hace_12m"]["MAE_pp"], 2))


if __name__ == "__main__":
    main()
