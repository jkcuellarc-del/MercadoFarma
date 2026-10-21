"""Figuras del informe (protocolo v2). Salida: informe_v2/figuras/*.png"""
import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "reports" / "v2"
F = ROOT / "informe_v2" / "figuras"
F.mkdir(parents=True, exist_ok=True)
c = json.loads((ROOT / "informe_v2" / "cifras.json").read_text())
SP = {"CA": "#2a78d6", "Cattle": "#eb6834", "Poultry": "#1baf7a", "Swine": "#eda100"}
NOM = {"CA": "Animales de compañía", "Cattle": "Bovinos", "Poultry": "Aves", "Swine": "Cerdos"}
INK, GRID, MUTED = "#13201c", "#dfe5e3", "#6f7f7a"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": GRID, "grid.linewidth": .6, "text.color": INK, "figure.dpi": 200, "savefig.bbox": "tight"})
T = {"mercado": "Mercado", "lab_ym": "Laboratorio"}


def guardar(fig, n):
    fig.savefig(F / n, facecolor="white")
    plt.close(fig)


def historia():
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for i, (k, t) in enumerate((("mercado", "Mercado"), ("lab", "Laboratorio"))):
        for e in SP:
            h = c["historia"][k][e]
            xs = [x for x in h if x != "jun2026"] + ["jun2026"]
            ax[i].plot(range(len(xs)), [h[x] * 100 for x in xs], color=SP[e], lw=1.8, marker="o", ms=3.5, label=NOM[e]) if k == "mercado" else \
                ax[i].plot(range(4 - len(xs) + 3, 3 + 1 + 0)[:0] or [j + (6 - len(xs)) for j in range(len(xs))], [h[x] * 100 for x in xs], color=SP[e], lw=1.8, marker="o", ms=3.5, label=NOM[e])
        for th in (8, 15):
            ax[i].axhline(th, color=MUTED, lw=.8, ls=":")
        ax[i].set_xticks(range(6)); ax[i].set_xticklabels(["2021", "2022", "2023", "2024", "2025", "12 m a\njun-26"], fontsize=8)
        ax[i].set_title(t, loc="left", fontsize=10, fontweight="bold")
    ax[0].set_ylabel("Crecimiento de 12 meses (%)")
    ax[1].legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.tight_layout(); guardar(fig, "f1_historia.png")


def aprendizaje_y_umbral():
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7))
    for i, t in enumerate(("mercado", "lab_ym")):
        d = pd.DataFrame(c["tareas"][t]["curva_aprendizaje"])
        ax[i].plot(d.meses_entrenamiento, d.MAE_entrenamiento, color="#2a78d6", marker="o", ms=3.5, lw=1.8, label="Entrenamiento")
        ax[i].plot(d.meses_entrenamiento, d.MAE_retenido, color="#eb6834", marker="o", ms=3.5, lw=1.8, label="Meses retenidos")
        ax[i].set_title(T[t], loc="left", fontsize=10, fontweight="bold"); ax[i].set_xlabel("Meses usados para entrenar"); ax[i].set_ylim(0, None)
    ax[0].set_ylabel("MAE (puntos %)"); ax[0].legend(frameon=False, fontsize=8)
    fig.tight_layout(); guardar(fig, "f3_aprendizaje.png")
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.7))
    for i, t in enumerate(("mercado", "lab_ym")):
        u = pd.DataFrame(c["tareas"][t]["umbral"]); m = c["tareas"][t]["seleccion"]["m_umbral"] * 100
        ax[i].plot(u.m_pp, u.costo_medio, color="#2a78d6", lw=1.8)
        y0 = u.loc[(u.m_pp - m).abs().idxmin(), "costo_medio"]
        ax[i].scatter([m], [y0], color="#eb6834", zorder=3, s=30)
        ax[i].annotate(f"m = {m:+.1f} pp", (m, y0), textcoords="offset points", xytext=(10, 14), fontsize=8, arrowprops=dict(arrowstyle="-", color=MUTED, lw=.6))
        ax[i].set_title(T[t], loc="left", fontsize=10, fontweight="bold"); ax[i].set_xlabel("Descuento de prudencia m (puntos %)")
    ax[0].set_ylabel("Costo medio por observación")
    fig.tight_layout(); guardar(fig, "f4_umbral.png")


def embargo():
    s = pd.DataFrame(c["tareas"]["mercado"]["sens_validacion"])
    lab = [v.replace("por bloques, embargo ", "Bloques\nembargo ").replace("estratificada por clase, grupos por año (sin purga)", "Estratificada\npor clase, sin\npurga") for v in s.validacion]
    fig, ax = plt.subplots(figsize=(5.4, 2.6))
    ax.bar(range(len(s)), s.MAE_pp, color=["#2a78d6"] * 4 + ["#6f7f7a"], width=.62)
    ax.set_xticks(range(len(s))); ax.set_xticklabels(lab, fontsize=7)
    for i, v in enumerate(s.MAE_pp):
        ax.text(i, v + .08, f"{v:.1f}", ha="center", fontsize=8)
    ax.set_ylabel("MAE fuera de pliegue (puntos %)"); ax.grid(axis="x", visible=False)
    fig.tight_layout(); guardar(fig, "f6_embargo.png")


def prueba():
    p = pd.read_csv(R / "prueba_predicciones.csv", parse_dates=["Fecha"])
    for tarea, nombre in (("mercado", "mercado"), ("lab_ym", "lab")):
        fig, ax = plt.subplots(1, 4, figsize=(7.2, 2.3), sharex=True)
        for j, e in enumerate(SP):
            d = p[(p.tarea == tarea) & (p.Especie == e)]
            ax[j].plot(d.Fecha, d.real * 100, color=SP[e], lw=1.8, marker="o", ms=3, label="Real")
            ax[j].plot(d.Fecha, d.pred * 100, color=INK, lw=1.2, ls="--", marker="s", ms=2.5, label="Modelo A")
            ax[j].plot(d.Fecha, d.pred_alt * 100, color="#6250d6", lw=1.2, ls="-.", marker="D", ms=2.5, label="Modelo B")
            for th in (8, 15):
                ax[j].axhline(th, color=MUTED, lw=.7, ls=":")
            ax[j].set_title(NOM[e].replace("Animales de compañía", "Compañía"), fontsize=8.5, fontweight="bold", loc="left")
            ax[j].set_xticks(d.Fecha); ax[j].set_xticklabels([x.strftime("%b") for x in d.Fecha], fontsize=7)
        ax[0].set_ylabel("Crecimiento de 12 m (%)", fontsize=8)
        h, l = ax[0].get_legend_handles_labels()
        fig.tight_layout(); fig.legend(h, l, frameon=False, fontsize=8, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.1))
        guardar(fig, f"f5_prueba_{nombre}.png")


def importancia():
    t = pd.DataFrame(c["importancia"])
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.2))
    for i, (tarea, cj, titulo) in enumerate((("mercado", "S7_real_trm", "Mercado"), ("lab", "S7_real_trm", "Laboratorio"))):
        d = t[(t.tarea == tarea) & (t.conjunto == cj)].copy()
        ctrl = d[d.es_control].perm_gbm_pp.max()
        d = d[~d.es_control].sort_values("perm_gbm_pp").tail(8)
        ax[i].barh(range(len(d)), d.perm_gbm_pp, color="#2a78d6", height=.62)
        ax[i].axvline(ctrl, color="#eb6834", lw=1.2, ls="--", label="Mayor control de ruido")
        ax[i].set_yticks(range(len(d))); ax[i].set_yticklabels(d.variable.str.replace("real_var_", "precio real ").str.replace("_", " "), fontsize=7.5)
        ax[i].set_title(titulo, loc="left", fontsize=9.5, fontweight="bold"); ax[i].set_xlabel("Aumento del error al barajar (pp)"); ax[i].grid(axis="y", visible=False)
    ax[0].legend(frameon=False, fontsize=7.5, loc="lower right")
    fig.tight_layout(); guardar(fig, "f7_importancia.png")


def cribado():
    s = pd.DataFrame(c["screening"]); s = s[(s.objetivo == "nominal") & (s.conjunto != "base")]
    fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.8), sharex=False)
    for i, (t, ti) in enumerate((("mercado", "Mercado"), ("compite", "Mercado donde compite"), ("lab", "Laboratorio"))):
        d = s[s.tarea == t].sort_values("MAE_cv", ascending=False)
        ax[i].barh(range(len(d)), d.MAE_cv, color=["#2a78d6" if x in ("S2_real", "S7_real_trm") else "#6f7f7a" for x in d.conjunto], height=.62)
        ax[i].set_yticks(range(len(d))); ax[i].set_yticklabels(d.conjunto, fontsize=7); ax[i].set_title(ti, loc="left", fontsize=9, fontweight="bold")
        ax[i].set_xlabel("MAE de CV (pp)"); ax[i].grid(axis="y", visible=False)
    fig.tight_layout(); guardar(fig, "f8_cribado.png")


if __name__ == "__main__":
    for n in ("comparacion_mercado.png", "comparacion_lab_ym.png", "curvas_validacion_mercado.png", "curvas_validacion_lab_ym.png"):
        shutil.copy(R / "figuras" / n, F / n)
    historia(); aprendizaje_y_umbral(); embargo(); prueba(); importancia(); cribado()
    print(sorted(p.name for p in F.glob("*.png")))
