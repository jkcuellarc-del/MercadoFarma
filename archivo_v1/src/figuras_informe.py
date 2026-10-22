"""Figuras del informe tecnico (PNG) a partir de reports/protocolo y data/processed."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "reports" / "protocolo"
F = ROOT / "informe" / "figuras"
F.mkdir(parents=True, exist_ok=True)
SP = {"CA": "#2a78d6", "Cattle": "#eb6834", "Poultry": "#1baf7a", "Swine": "#eda100"}
NOM = {"CA": "Animales de compañía", "Cattle": "Bovinos", "Poultry": "Aves", "Swine": "Cerdos"}
INK, GRID, MUTED = "#13201c", "#dfe5e3", "#6f7f7a"
MOD = {"ridge_esp": "Ridge por especie", "ridge": "Ridge común", "enet": "Elastic Net", "rf": "Random Forest", "gbm": "Gradient Boosting",
       "B1_crecimiento_hace_12m": "Base 1: crecimiento hace 12 m", "B2_media_especie": "Base 2: promedio de la especie"}
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": .6,
                     "text.color": INK, "figure.dpi": 200, "savefig.bbox": "tight"})
TASK = {"mercado": "Mercado", "lab": "Laboratorio"}


def guardar(fig, nombre):
    fig.savefig(F / nombre, facecolor="white")
    plt.close(fig)


def f_historia():
    a = pd.read_csv(ROOT / "data" / "processed" / "annual_especie.csv")
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for i, (col, t) in enumerate((("Crec_Mercado", "Mercado"), ("Crec_Lab", "Laboratorio"))):
        for e in SP:
            d = a[(a.Especie == e) & (a.Año >= 2021)]
            d = d[d[col].notna()]
            ax[i].plot(d.Año, d[col] * 100, color=SP[e], lw=1.8, marker="o", ms=3.5, label=NOM[e])
        for th in (8, 15):
            ax[i].axhline(th, color=MUTED, lw=.8, ls=":")
        ax[i].set_title(t, loc="left", fontsize=10, fontweight="bold")
        ax[i].set_xticks(range(2021, 2027))
        ax[i].set_xlabel("Año (2026 con julio a diciembre estimado)")
    ax[0].set_ylabel("Crecimiento anual nominal (%)")
    ax[1].legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.tight_layout()
    guardar(fig, "f1_historia.png")


def f_cv():
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for i, t in enumerate(("mercado", "lab")):
        c = pd.read_csv(R / f"comparacion_cv_{t}.csv").set_index("modelo").loc[list(MOD)]
        y = np.arange(len(c))[::-1]
        col = ["#6f7f7a" if m.startswith("B") else "#2a78d6" for m in c.index]
        ax[i].barh(y, c.MAE_cv, xerr=c["sd"], color=col, height=.62, error_kw=dict(ecolor=INK, lw=.8, capsize=2))
        ax[i].set_yticks(y)
        ax[i].set_yticklabels([MOD[m] for m in c.index] if i == 0 else [""] * len(c))
        ax[i].set_title(TASK[t], loc="left", fontsize=10, fontweight="bold")
        ax[i].set_xlabel("MAE en validación cruzada (puntos %)")
        ax[i].grid(axis="y", visible=False)
        for yy, v in zip(y, c.MAE_cv):
            ax[i].text(v + .1, yy + .33, f"{v:.1f}", fontsize=7, color=MUTED, va="bottom")
    fig.tight_layout()
    guardar(fig, "f2_cv.png")


def f_aprendizaje():
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7))
    for i, t in enumerate(("mercado", "lab")):
        c = pd.read_csv(R / f"curva_aprendizaje_{t}.csv")
        ax[i].plot(c.meses_entrenamiento, c.MAE_entrenamiento, color="#2a78d6", marker="o", ms=3.5, lw=1.8, label="Entrenamiento")
        ax[i].plot(c.meses_entrenamiento, c.MAE_retenido, color="#eb6834", marker="o", ms=3.5, lw=1.8, label="Meses retenidos")
        ax[i].set_title(TASK[t], loc="left", fontsize=10, fontweight="bold")
        ax[i].set_xlabel("Meses usados para entrenar")
        ax[i].set_ylim(0, None)
    ax[0].set_ylabel("MAE (puntos %)")
    ax[0].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    guardar(fig, "f3_aprendizaje.png")


def f_umbral():
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7))
    for i, t in enumerate(("mercado", "lab")):
        u = pd.read_csv(R / f"umbral_{t}.csv")
        s = json.loads((R / f"seleccion_{t}.json").read_text())
        ax[i].plot(u.m_pp, u.costo_medio, color="#2a78d6", lw=1.8)
        m = s["m_umbral"] * 100
        ax[i].scatter([m], [u.loc[(u.m_pp - m).abs().idxmin(), "costo_medio"]], color="#eb6834", zorder=3, s=30)
        ax[i].annotate(f"m = {m:+.1f} pp", (m, u.loc[(u.m_pp - m).abs().idxmin(), "costo_medio"]), textcoords="offset points", xytext=(10, 14), fontsize=8, arrowprops=dict(arrowstyle="-", color=MUTED, lw=.6))
        ax[i].set_title(TASK[t], loc="left", fontsize=10, fontweight="bold")
        ax[i].set_xlabel("Descuento de prudencia m (puntos %)")
    ax[0].set_ylabel("Costo medio por observación")
    fig.tight_layout()
    guardar(fig, "f4_umbral.png")


def f_prueba():
    p = pd.read_csv(R / "prueba_predicciones.csv", parse_dates=["Fecha"])
    fig, ax = plt.subplots(2, 4, figsize=(7.2, 3.8), sharex=True)
    for r, t in enumerate(("mercado", "lab")):
        for c, e in enumerate(SP):
            d = p[(p.tarea == t) & (p.Especie == e)]
            ax[r, c].plot(d.Fecha, d.real * 100, color=SP[e], lw=1.8, marker="o", ms=3, label="Real")
            ax[r, c].plot(d.Fecha, d.pred * 100, color=INK, lw=1.2, ls="--", marker="s", ms=2.5, label="Predicho")
            for th in (8, 15):
                ax[r, c].axhline(th, color=MUTED, lw=.7, ls=":")
            if r == 0:
                ax[r, c].set_title(NOM[e].replace("Animales de compañía", "Compañía"), fontsize=8.5, fontweight="bold", loc="left")
            ax[r, c].set_xticks(d.Fecha)
            ax[r, c].set_xticklabels([x.strftime("%b") for x in d.Fecha], fontsize=7)
        ax[r, 0].set_ylabel(f"{TASK[t]}\ncrecimiento 12 m (%)", fontsize=8)
    h, l = ax[0, 3].get_legend_handles_labels()
    fig.tight_layout()
    fig.legend(h, l, frameon=False, fontsize=8, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.04))
    guardar(fig, "f5_prueba.png")


def f_embargo():
    s = pd.read_csv(R / "sensibilidad_validacion_mercado.csv")
    fig, ax = plt.subplots(figsize=(5.4, 2.6))
    lab = [v.replace("por bloques, embargo ", "Bloques\nembargo ").replace("estratificada por clase, grupos por año (sin purga)", "Estratificada\npor clase, sin\npurga") for v in s.validacion]
    ax.bar(range(len(s)), s.MAE_pp, color=["#2a78d6"] * 4 + ["#6f7f7a"], width=.62)
    ax.set_xticks(range(len(s)))
    ax.set_xticklabels(lab, fontsize=7)
    for i, v in enumerate(s.MAE_pp):
        ax.text(i, v + .08, f"{v:.1f}", ha="center", fontsize=8)
    ax.set_ylabel("MAE fuera de pliegue (puntos %)")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    guardar(fig, "f6_embargo.png")


if __name__ == "__main__":
    for f in (f_historia, f_cv, f_aprendizaje, f_umbral, f_prueba, f_embargo):
        f()
    print(sorted(p.name for p in F.glob("*.png")))
