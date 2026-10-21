"""Cribado de conjuntos de predictores y del tipo de objetivo (nominal o real), solo con datos de desarrollo.

Mismas filas, mismos pliegues con purga y mismos 5 modelos (rejillas reducidas) para todas las combinaciones.
Regla declarada: un conjunto/objetivo mejora a S0 nominal solo si la diferencia de MAE entre pliegues (pareada) favorece
al nuevo en mas de 1 error estandar de la diferencia.
"""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV

from . import config as C
from . import datos, predictores as P, variables as V
from .nucleo import TASKS, ESPS, ONEHOT, mes_idx, r2, splits  # noqa: F401

RAP = {"ridge": {"alpha": [10, 100, 1000, 10000]},
       "enet_esp": {"alpha": [0.01, 0.1, 1], "l1_ratio": [0.5, 1.0]},
       "knn": {"n_neighbors": [10, 20, 30], "weights": ["distance"]},
       "rf": {"max_depth": [3, 8], "min_samples_leaf": [3], "max_features": [0.5]},
       "gbm": {"n_estimators": [50, 150], "learning_rate": [0.03], "max_depth": [1, 3], "min_samples_leaf": [8]}}
INI = {"mercado": "2022-12-01", "compite": "2022-12-01", "lab": "2023-12-01"}
YCOL = {"mercado": "y_mercado", "compite": "y_compite", "lab": "y_lab"}
EXTRA_LAB = ["y_compite"]


def datos_tarea(task):
    df = datos.leer_desarrollo()
    comp = pd.read_csv(C.DATA / "series_compite.csv")
    d = P.ampliar(V.construir(df, comp), P.extra(df, comp, datos.leer_trm_desarrollo()))
    d = d[(d.Fecha >= INI[task]) & (d.Fecha <= C.CORTE)].copy()
    for e in ESPS:
        d[f"esp_{e}"] = (d.Especie == e).astype(int)
    return d.reset_index(drop=True)


def main(tasks=("mercado", "compite", "lab")):
    filas = []
    for task in tasks:
        d0 = datos_tarea(task)
        y = YCOL[task]
        cv = splits(mes_idx(d0["Fecha"]), TASKS[task]["emb"])
        conjs = P.conjuntos(y if task != "lab" else "y_compite")
        for obj in ("nominal", "real"):
            for cj, cols in conjs.items():
                if task == "lab" and cj in ("S1_ar", "S5_todo"):
                    continue  # el laboratorio no tiene 12 meses previos de crecimiento en el entrenamiento
                cont = cols + (EXTRA_LAB if task == "lab" else [])
                d = d0.dropna(subset=cont + [y]).reset_index(drop=True)
                if len(d) != len(d0):
                    print("aviso: filas perdidas", task, cj, len(d0) - len(d))
                cvl = splits(mes_idx(d["Fecha"]), TASKS[task]["emb"])
                yn = d[y].to_numpy()
                ipcm = d["ipcm_yoy"].to_numpy()
                yt = yn if obj == "nominal" else ((1 + yn) / (1 + ipcm) - 1)
                X = d[cont + ONEHOT]
                mejores = {}
                for kind, grid in RAP.items():
                    gs = GridSearchCV(P.pipeline_cont(kind, cont), {f"model__est__{k}": v for k, v in grid.items()}, cv=cvl,
                                      scoring="neg_mean_absolute_error", n_jobs=4, refit=False).fit(X, yt)
                    j = int(np.argmax(gs.cv_results_["mean_test_score"]))
                    prm = {k.replace("model__est__", ""): v for k, v in gs.cv_results_["params"][j].items()}
                    oofp = np.full(len(d), np.nan)
                    for tr, te in cvl:
                        oofp[te] = P.pipeline_cont(kind, cont, **prm).fit(X.iloc[tr], yt[tr]).predict(X.iloc[te])
                    pn = oofp if obj == "nominal" else (1 + oofp) * (1 + ipcm) - 1
                    folds = [float(np.abs(pn[te] - yn[te]).mean() * 100) for _, te in cvl]
                    mejores[kind] = dict(folds=folds, params=prm)
                    filas.append({"tarea": task, "objetivo": obj, "conjunto": cj, "modelo": kind, "n_features": len(cont), "n_filas": len(d),
                                  "MAE_cv": float(np.mean(folds)), "sd": float(np.std(folds, ddof=1)), "R2_oof": r2(yn, pn), "params": json.dumps(prm), "folds": json.dumps(folds)})
                print(task, obj, cj, "mejor:", min(((k, np.mean(v["folds"])) for k, v in mejores.items()), key=lambda t: t[1]), flush=True)
        # lineas base en las mismas filas
        d = d0.dropna(subset=[y]).reset_index(drop=True)
        cvl = splits(mes_idx(d["Fecha"]), TASKS[task]["emb"])
        yn = d[y].to_numpy()
        for nm, fn in (("B0_media_global", lambda tr, te: np.full(len(te), yn[tr].mean())),
                       ("B2_media_especie", lambda tr, te: d.Especie.iloc[te].map(d.iloc[tr].groupby("Especie")[y].mean()).to_numpy())):
            folds, po = [], np.full(len(d), np.nan)
            for tr, te in cvl:
                po[te] = fn(tr, te)
                folds.append(float(np.abs(po[te] - yn[te]).mean() * 100))
            filas.append({"tarea": task, "objetivo": "nominal", "conjunto": "base", "modelo": nm, "n_features": 0, "n_filas": len(d),
                          "MAE_cv": float(np.mean(folds)), "sd": float(np.std(folds, ddof=1)), "R2_oof": r2(yn, po), "params": "", "folds": json.dumps(folds)})
    out = pd.DataFrame(filas)
    out.to_csv(C.REP / "screening_predictores.csv", index=False)
    return out


if __name__ == "__main__":
    main()
