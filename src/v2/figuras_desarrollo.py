"""Figuras de la etapa de desarrollo (curvas de validacion, boosting, arboles, aprendizaje, R2). Salida: reports/v2/figuras."""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import config as C  # noqa: E402
from .nucleo import NOMBRES, TASKS  # noqa: E402

F = C.REP / "figuras"
F.mkdir(parents=True, exist_ok=True)
INK, GRID, MUTED = "#13201c", "#dfe5e3", "#6f7f7a"
AZ, NA, VE, AM = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": .6, "figure.dpi": 170, "savefig.bbox": "tight", "text.color": INK,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})


def grid(task):
    g = pd.read_csv(C.REP / f"cv_grid_{task}.csv")
    P = g.params.apply(json.loads).apply(pd.Series)
    return pd.concat([g.drop(columns="params"), P], axis=1)


def curvas_validacion(task):
    g = grid(task)
    fig, ax = plt.subplots(2, 3, figsize=(8.6, 5.2))
    a = ax[0, 0]
    for k, c in (("ridge_esp", AZ), ("ridge", NA)):
        d = g[g.modelo == k].groupby("est__alpha").MAE_cv.min()
        a.plot(d.index, d.values, marker="o", ms=3, color=c, label=NOMBRES[k])
    a.set_xscale("log"); a.set_title("Ridge: alpha", fontsize=9, loc="left"); a.legend(frameon=False, fontsize=7)
    a = ax[0, 1]
    d = g[g.modelo == "enet_esp"]
    for l1, c in zip(sorted(d.est__l1_ratio.unique()), (AZ, VE, AM, NA)):
        x = d[d.est__l1_ratio == l1].groupby("est__alpha").MAE_cv.min()
        a.plot(x.index, x.values, marker="o", ms=3, color=c, label=f"l1_ratio {l1}")
    a.set_xscale("log"); a.set_title("Elastic Net por especie: alpha", fontsize=9, loc="left"); a.legend(frameon=False, fontsize=6.5)
    a = ax[0, 2]
    d = g[g.modelo == "knn"]
    for w, c in (("uniform", AZ), ("distance", NA)):
        x = d[d.est__weights == w].groupby("est__n_neighbors").MAE_cv.min()
        a.plot(x.index, x.values, marker="o", ms=3, color=c, label=w)
    a.set_title("K vecinos: k", fontsize=9, loc="left"); a.legend(frameon=False, fontsize=7)
    a = ax[1, 0]
    for k, c in (("rf", AZ), ("bagging", NA)):
        d = g[g.modelo == k]
        col = "est__max_depth" if k == "rf" else "est__estimator__max_depth"
        x = d.assign(m=d[col].fillna(99)).groupby("m").MAE_cv.min()
        a.plot([str(int(i)) if i < 99 else "sin límite" for i in x.index], x.values, marker="o", ms=3, color=c, label=NOMBRES[k])
    a.set_title("Árboles: profundidad máxima", fontsize=9, loc="left"); a.legend(frameon=False, fontsize=7)
    b = pd.read_csv(C.REP / f"curva_boosting_{task}.csv")
    a = ax[1, 1]
    a.plot(b.iteracion, b.MAE_entrenamiento, color=AZ, label="Entrenamiento"); a.plot(b.iteracion, b.MAE_cv, color=NA, label="Validación cruzada")
    a.set_title("Boosting: iteraciones", fontsize=9, loc="left"); a.legend(frameon=False, fontsize=7)
    t = pd.read_csv(C.REP / f"curva_arboles_{task}.csv")
    a = ax[1, 2]
    for k, c in (("rf", AZ), ("bagging", NA)):
        x = t[t.modelo == k]; a.plot(x.n_arboles, x.MAE_cv, marker="o", ms=3, color=c, label=NOMBRES[k])
    a.set_xscale("log"); a.set_title("Bagging y bosque: número de árboles", fontsize=9, loc="left"); a.legend(frameon=False, fontsize=7)
    for a in ax.flat:
        a.set_ylabel("MAE (pp)", fontsize=8)
    fig.suptitle(f"Curvas de validación, tarea: {task}", fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(F / f"curvas_validacion_{task}.png", facecolor="white"); plt.close(fig)


def comparacion(task):
    c = pd.read_csv(C.REP / f"comparacion_cv_{task}.csv").sort_values("MAE_cv", ascending=False)
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    y = np.arange(len(c))
    ax.barh(y, c.MAE_cv, xerr=c["sd"], color=[MUTED if m.startswith("B") else AZ for m in c.modelo], height=.62, error_kw=dict(ecolor=INK, lw=.8, capsize=2))
    ax.set_yticks(y); ax.set_yticklabels([NOMBRES.get(m, m) for m in c.modelo], fontsize=8)
    for yy, (m, r2) in enumerate(zip(c.MAE_cv, c.R2_oof)):
        ax.text(m + .1, yy + .33, f"{m:.1f}" + ("" if pd.isna(r2) else f" · R² {r2:.2f}"), fontsize=7, color=MUTED, va="bottom")
    ax.set_xlabel("MAE en validación cruzada (pp) · R² fuera de pliegue"); ax.grid(axis="y", visible=False)
    ax.set_title(f"Comparación de modelos, tarea: {task}", loc="left", fontsize=10)
    fig.tight_layout(); fig.savefig(F / f"comparacion_{task}.png", facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    for t in TASKS:
        curvas_validacion(t); comparacion(t)
    print(sorted(p.name for p in F.glob("*.png")))
