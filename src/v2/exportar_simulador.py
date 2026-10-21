"""Exporta los DOS modelos (A: elegido por la regla; B: Gradient Boosting) al simulador web: simulador/modelo_v2.json.

A = Elastic Net comun (mercado) y Ridge por especie (laboratorio): lineales, se evaluan con coeficientes.
B = Gradient Boosting (mercado y laboratorio): se exportan los arboles y se evalua en el navegador.
Cada modelo usa su propia cadena: el laboratorio recibe el crecimiento del mercado que proyecta ese mismo modelo.
Se ejecuta DESPUES de la evaluacion unica de la prueba. Verifica que la evaluacion exportada coincide con scikit-learn.
"""
import json

import joblib
import numpy as np
import pandas as pd

from . import config as C
from . import datos, variables
from .despliegue import exportar_lineal
from .nucleo import *  # noqa: F401,F403
from .nucleo import PerEspecie
from .proyeccion import ESPS, PRECIO_DE, base_2027, filas

OUT = C.ROOT / "simulador" / "modelo_v2.json"


def exportar_gbm(pipe, task):
    pre, est = pipe.named_steps["pre"], pipe.named_steps["model"].est_
    sc = pre.named_transformers_["num"]
    cont = TASKS[task]["cont"]
    arboles = []
    for t in est.estimators_[:, 0]:
        tr = t.tree_
        arboles.append({"f": tr.feature.tolist(), "t": [round(float(x), 10) for x in tr.threshold], "l": tr.children_left.tolist(),
                        "r": tr.children_right.tolist(), "v": [float(x) for x in tr.value[:, 0, 0]]})
    return {"tipo": "gbm", "cont": cont, "mean": dict(zip(cont, map(float, sc.mean_))), "scale": dict(zip(cont, map(float, sc.scale_))),
            "init": float(est.init_.constant_.ravel()[0]), "lr": float(est.learning_rate), "arboles": arboles}


def evaluar(m, x_cont, esp):
    """Replica en Python lo que hara el navegador (x_cont: dict de variables continuas sin escalar)."""
    z = {k: (x_cont[k] - m["mean"][k]) / m["scale"][k] for k in m["cont"]}
    onehot = {f"esp_{e}": float(e == esp) for e in ESPS}
    if m["tipo"] == "por_especie":
        e = m["especies"][esp]
        return e["intercept"] + sum(e["coef"][k] * z[k] for k in m["cont"])
    if m["tipo"] == "comun":
        return m["intercept"] + sum(m["coef"][k] * z[k] for k in m["cont"]) + sum(m["coef"][k] * v for k, v in onehot.items())
    vec = [z[k] for k in m["cont"]] + [onehot[f"esp_{e}"] for e in ESPS]
    s = m["init"]
    for t in m["arboles"]:
        n = 0
        while t["l"][n] != -1:
            n = t["l"][n] if vec[t["f"][n]] <= t["t"][n] else t["r"][n]
        s += m["lr"] * t["v"][n]
    return s


def bandas_gbm(task, pesos, res):
    """MAE por especie de GBM: promedio de fuera de pliegue (desarrollo) y de prueba."""
    sel = json.loads((C.REP / f"seleccion_{task}.json").read_text())
    g = sel["mejores"]["gbm"]
    d = pd.read_csv(C.DATA / f"features_desarrollo_{task}.csv", parse_dates=["Fecha"]).sort_values(["Fecha", "Especie"]).reset_index(drop=True)
    cv = splits(mes_idx(d["Fecha"]), TASKS[task]["emb"])
    po, _ = oof(pipeline("gbm", task, g["balance"], **g["params"]), d, task, cv)
    err = pd.DataFrame({"e": d.Especie, "a": np.abs(po - d[TASKS[task]["y"]].to_numpy()) * 100}).groupby("e").a.mean()
    te = res[task]["alternativa_mejor_cv"]["por_especie"]
    return {e: float((err[e] + te[e]["MAE_pp"]) / 2) for e in ESPS}


def main():
    res = json.loads((C.REP / "prueba_resultados.json").read_text())
    lv = res["variante_lab"]
    todo = pd.concat([datos.leer_desarrollo(), datos.leer_prueba("exportacion al simulador (posterior a la evaluacion unica)")], ignore_index=True)
    comp = pd.read_csv(C.DATA / "series_compite.csv")
    base = base_2027(todo, comp)
    L = lambda n: joblib.load(C.MODELOS / f"pipeline_{n}.joblib")["pipeline"]
    A = {"mercado": exportar_lineal(L("final_mercado"), "mercado"), "lab": exportar_lineal(L("final_" + lv), lv)}
    B = {"mercado": exportar_gbm(L("alt_mercado"), "mercado"), "lab": exportar_gbm(L("alt_" + lv), lv)}
    # verificacion contra scikit-learn
    pipes = {("A", "mercado"): L("final_mercado"), ("A", "lab"): L("final_" + lv), ("B", "mercado"): L("alt_mercado"), ("B", "lab"): L("alt_" + lv)}
    mods = {("A", "mercado"): A["mercado"], ("A", "lab"): A["lab"], ("B", "mercado"): B["mercado"], ("B", "lab"): B["lab"]}
    maxdif = 0.0
    rng = np.random.default_rng(0)
    for (g, k), m in mods.items():
        task = "mercado" if k == "mercado" else lv
        for esp in ESPS:
            for _ in range(25):
                r = filas(base, esp)
                for key in ("ipc_yoy", "pib", "pib_agro", "smmlv"):
                    r[key] = r[key] * (1 + rng.normal(0, .3))
                r["ipc_yoy_CA"] = r["ipc_yoy"] if esp == "CA" else 0.0
                for key in list(r):
                    if key.startswith("real_"):
                        r[key] = r[key] + rng.normal(0, .08) * (r[key] != 0.0 or PRECIO_DE.get(key[5:]) == esp)
                r["y_mercado"] = rng.normal(0.14, 0.05)
                x = pd.DataFrame([r])[columnas(task)]
                maxdif = max(maxdif, abs(float(pipes[(g, k)].predict(x)[0]) - evaluar(m, r, esp)))
    print("maxima diferencia JSON vs scikit-learn:", maxdif)
    assert maxdif < 1e-8
    # rangos de entrenamiento por especie
    f = variables.construir(todo, comp)
    rangos = {}
    for e in ESPS:
        d = variables.tabla(f, "mercado", TASKS["mercado"]["ini"], C.PRUEBA_FIN)
        d = d[d.Especie == e]
        rangos[e] = {c: [float(d[c].min()), float(d[c].max())] for c in TASKS["mercado"]["cont"]}
    # historia: crecimiento de 12 meses a diciembre de cada anio y a junio de 2026
    pnl = variables.panel(todo, comp).sort_values("Fecha")
    hist = {"mercado": {}, "lab": {}}
    for e in ESPS + ["Total"]:
        g = pnl.groupby("Fecha")[["Mercado", "Venta Laboratorio"]].sum() if e == "Total" else pnl[pnl.Especie == e].set_index("Fecha")[["Mercado", "Venta Laboratorio"]]
        for k, c in (("mercado", "Mercado"), ("lab", "Venta Laboratorio")):
            r12 = g[c].rolling(12).sum()
            y = (r12 / r12.shift(12) - 1)
            h = {str(a): float(y.loc[f"{a}-12-01"]) for a in range(2021 if k == "mercado" else 2023, 2026) if not np.isnan(y.loc[f"{a}-12-01"])}
            h["jun2026"] = float(y.loc["2026-06-01"])
            hist[k][e] = h
    ban = json.loads((C.REP / "bandas_error.json").read_text())
    w = base["pesos"]
    bB = {"mercado": bandas_gbm("mercado", w, res), "lab": bandas_gbm(lv, w, res)}
    for k in bB:
        bB[k]["Total"] = float(sum(w[k][e] * bB[k][e] for e in ESPS))
    prueba = {"mercado": {"A": res["mercado"]["MAE_pp"], "B": res["mercado"]["alternativa_mejor_cv"]["MAE_pp"], "prom_especie": res["mercado"]["B2_media_especie"]["MAE_pp"],
                          "anio_anterior": res["mercado"]["B1_crecimiento_hace_12m"]["MAE_pp"]},
              "lab": {"A": res[lv]["MAE_pp"], "B": res[lv]["alternativa_mejor_cv"]["MAE_pp"], "prom_especie": res[lv]["B2_media_especie"]["MAE_pp"],
                      "anio_anterior": res[lv]["B1_crecimiento_hace_12m"]["MAE_pp"]}}
    cm = pd.read_csv(C.REP / "comparacion_cv_mercado.csv").set_index("modelo")["MAE_cv"]
    cl = pd.read_csv(C.REP / f"comparacion_cv_{lv}.csv").set_index("modelo")["MAE_cv"]
    fm = json.loads((C.REP / "seleccion_mercado.json").read_text())["final"]
    fl = json.loads((C.REP / f"seleccion_{lv}.json").read_text())["final"]
    pm, pl = prueba["mercado"], prueba["lab"]
    cpl = json.loads((C.REP / "prueba_complementaria.json").read_text())  # segunda consulta, informativa
    ex = lambda k, t: float(cpl[k][t]["MAE_pp"])
    fila = lambda n, cmv, clv, em, el, sep=False: {"nombre": n, "cv_mercado": float(cmv), "cv_lab": float(clv), "ex_mercado": em, "ex_lab": el, "sep": sep}
    comparacion = [
        fila("Modelo A (elegido por la regla): Elastic Net en el mercado y Ridge por especie en el laboratorio", cm[fm], cl[fl], pm["A"], pl["A"]),
        fila("Modelo B: Gradient Boosting", cm["gbm"], cl["gbm"], pm["B"], pl["B"]),
        fila("K vecinos más cercanos", cm["knn"], cl["knn"], ex("knn", "mercado"), ex("knn", "lab")),
        fila("Random Forest", cm["rf"], cl["rf"], ex("rf", "mercado"), ex("rf", "lab")),
        fila("Modelo base: regresión lineal (sin regularizar)", cm["ols"], cl["ols"], ex("ols", "mercado"), ex("ols", "lab")),
        fila("Método sencillo: promedio de la especie", cm["B2_media_especie"], cl["B2_media_especie"], pm["prom_especie"], pl["prom_especie"], True),
        fila("Método sencillo: crecimiento del año anterior", cm["B1_crecimiento_hace_12m"], cl["B1_crecimiento_hace_12m"], pm["anio_anterior"], pl["anio_anterior"]),
    ]
    out = {"comparacion": comparacion, "especies": ESPS, "base": {k: v for k, v in base.items() if k != "pesos"}, "pesos": base["pesos"], "modelos": {"A": A, "B": B},
           "bandas": {"A": ban, "B": bB}, "rangos": rangos, "historia": hist, "prueba": prueba, "variante_lab": lv}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print("escrito", OUT, round(OUT.stat().st_size / 1024), "KB")


if __name__ == "__main__":
    main()
