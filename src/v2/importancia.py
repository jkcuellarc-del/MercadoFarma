"""Importancia de variables con controles de ruido, solo con datos de desarrollo.

Tres lecturas sobre las mismas filas y los mismos pliegues con purga:
 1) Importancia por permutacion fuera de pliegue (Random Forest y Gradient Boosting): cuanto sube el MAE de prueba del
    pliegue al barajar una columna. Se agregan 3 columnas de ruido (control): una variable "importa" solo si supera al mayor
    de los controles.
 2) Estabilidad de Lasso: fraccion de remuestreos por bloques de meses en que el coeficiente es distinto de cero (con controles).
 3) Importancia por impureza del bosque (referencia; esta sesgada hacia variables continuas con muchos valores distintos).
Importancia no implica causalidad: mide cuanto usa el modelo la variable para predecir fuera de muestra.
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Lasso
from sklearn.preprocessing import StandardScaler

from . import config as C
from . import predictores as P
from .nucleo import ESPS, ONEHOT, TASKS, mes_idx, splits
from .seleccion_predictores import EXTRA_LAB, YCOL, datos_tarea

SEED = 0
CTRL = ["ctrl_1", "ctrl_2", "ctrl_3"]
MODELOS = {"rf": dict(max_depth=5, min_samples_leaf=3, max_features=0.5), "gbm": dict(n_estimators=50, learning_rate=0.03, max_depth=3, min_samples_leaf=8)}


def correr(task, conjunto="S0_actual", reps=20):
    rng = np.random.default_rng(SEED)
    d = datos_tarea(task)
    y = YCOL[task]
    cols = P.conjuntos(y if task != "lab" else "y_compite")[conjunto] + (EXTRA_LAB if task == "lab" else [])
    d = d.dropna(subset=cols + [y]).reset_index(drop=True)
    for c in CTRL:
        d[c] = rng.normal(size=len(d))
    cont = cols + CTRL
    X = d[cont + ONEHOT]
    yv = d[y].to_numpy()
    cv = splits(mes_idx(d["Fecha"]), TASKS[task]["emb"])
    res = {m: np.zeros(len(cont)) for m in MODELOS}
    for m, prm in MODELOS.items():
        for tr, te in cv:
            mod = P.pipeline_cont(m, cont, **prm).fit(X.iloc[tr], yv[tr])
            base = np.abs(mod.predict(X.iloc[te]) - yv[te]).mean()
            for j, c in enumerate(cont):
                inc = []
                for _ in range(reps):
                    Xp = X.iloc[te].copy()
                    Xp[c] = rng.permutation(Xp[c].to_numpy())
                    inc.append(np.abs(mod.predict(Xp) - yv[te]).mean() - base)
                res[m][j] += np.mean(inc) * 100 / len(cv)
    # impureza (referencia)
    rf = P.pipeline_cont("rf", cont, **MODELOS["rf"]).fit(X, yv)
    imp = rf.named_steps["model"].est_.feature_importances_[: len(cont)]
    # estabilidad de Lasso con remuestreo por bloques de 6 meses
    meses = np.sort(d["Fecha"].unique())
    bloques = np.array_split(meses, int(np.ceil(len(meses) / 6)))
    sel = np.zeros(len(cont))
    B = 200
    Z = StandardScaler().fit_transform(d[cont])
    for _ in range(B):
        elegidos = [bloques[i] for i in rng.integers(0, len(bloques), len(bloques))]
        idx = np.where(d["Fecha"].isin(np.concatenate(elegidos)))[0]
        k = np.concatenate([np.where(d["Fecha"].isin(b))[0] for b in elegidos])
        l = Lasso(alpha=0.002, max_iter=20000).fit(np.c_[Z[k], d[ONEHOT].to_numpy()[k]], yv[k])
        sel += (np.abs(l.coef_[: len(cont)]) > 1e-9)
    t = pd.DataFrame({"variable": cont, "perm_rf_pp": res["rf"], "perm_gbm_pp": res["gbm"], "impureza_rf": imp, "estabilidad_lasso": sel / B})
    t["es_control"] = t.variable.isin(CTRL)
    for m in ("perm_rf_pp", "perm_gbm_pp"):
        t[m.replace("_pp", "") + "_supera_control"] = t[m] > t.loc[t.es_control, m].max()
    t.insert(0, "tarea", task)
    t.insert(1, "conjunto", conjunto)
    return t


def main():
    out = pd.concat([correr(t, cj) for t, cj in (("mercado", "S0_actual"), ("mercado", "S2_real"), ("compite", "S0_actual"), ("compite", "S2_real"), ("lab", "S0_actual"))], ignore_index=True)
    out.to_csv(C.REP / "importancia_variables.csv", index=False)
    pd.set_option("display.width", 220, "display.float_format", "{:,.3f}".format)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
