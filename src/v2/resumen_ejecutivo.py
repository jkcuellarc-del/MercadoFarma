"""Genera el resumen ejecutivo (maximo 350 palabras) con las cifras finales del proyecto.

Lee reports/v2/proyeccion_2027_base.csv (proyeccion final) y reports/v2/prueba_resultados.json (examen unico de 2026).
Sin esos archivos produce un BORRADOR con cifras de ejemplo marcadas, para revisar el texto.
Uso: python -m src.v2.resumen_ejecutivo [--borrador]
"""
import json
import re
import sys

import pandas as pd

from . import config as C

NOM = {"CA": "mascotas", "Cattle": "bovinos", "Poultry": "aves", "Swine": "cerdos"}


def pct(v):
    return f"{v * 100:.1f}".replace(".", ",") + "%"


def n1(v):
    return f"{v:.1f}".replace(".", ",")


def veredicto(modelo, b1, b2):
    mejor_base = min(b1, b2)
    if modelo < mejor_base - 0.3:
        return "superó"
    if modelo <= mejor_base + 0.3:
        return "igualó"
    return "no superó"


def datos(borrador):
    if borrador:
        return {"mer": 0.159, "lab": 0.218, "esp": {"CA": 0.178, "Cattle": 0.148, "Poultry": 0.094, "Swine": 0.196},
                "e_mer": 8.4, "b_mer": 8.4, "e_lab": 3.8, "b_lab": 4.1, "r_mer": 6.2, "r_lab": 5.3, "borrador": True}
    p = pd.read_csv(C.REP / "proyeccion_2027_base.csv").set_index("Especie")
    t = json.loads((C.REP / "prueba_resultados.json").read_text())
    lab = t["variante_lab"]
    ban = json.loads((C.REP / "bandas_error.json").read_text())
    return {"mer": p.loc["Total", "crec_mercado"], "lab": p.loc["Total", "crec_lab"], "esp": {e: p.loc[e, "crec_mercado"] for e in NOM},
            "e_mer": t["mercado"]["MAE_pp"], "b_mer": min(t["mercado"]["B1_crecimiento_hace_12m"]["MAE_pp"], t["mercado"]["B2_media_especie"]["MAE_pp"]),
            "e_lab": t[lab]["MAE_pp"], "b_lab": min(t[lab]["B1_crecimiento_hace_12m"]["MAE_pp"], t[lab]["B2_media_especie"]["MAE_pp"]),
            "r_mer": ban["mercado"]["Total"], "r_lab": ban["lab"]["Total"], "borrador": False}


def texto(d):
    esp = sorted(d["esp"].items(), key=lambda kv: kv[1])
    alto, bajo = esp[-1], esp[0]
    v_mer = veredicto(d["e_mer"], d["b_mer"], d["b_mer"])
    v_lab = veredicto(d["e_lab"], d["b_lab"], d["b_lab"])
    return f"""# Resumen ejecutivo: el mercado de salud animal y el Laboratorio en 2027

**Contexto.** El Laboratorio vende medicinas y vacunas para mascotas, bovinos, cerdos y aves en Colombia. Para planear 2027 (metas, presupuesto e inventarios) necesita una idea de cuánto crecerá el mercado y cuánto crecerán sus propias ventas. Usamos las ventas mensuales de 2020 a junio de 2026, más precios de la carne, la leche, el huevo y el pollo, la inflación, el PIB y el salario mínimo.

**Cómo se hizo.** Probamos diez modelos estadísticos que aprenden cómo se movió el crecimiento anual y lo proyectan. Los comparamos por bloques de tiempo, siempre con datos que el modelo no había visto, y elegimos el más simple entre los de rendimiento parecido. Probamos también si el dólar ayudaba a explicar el mercado: no. Guardamos bajo llave el primer semestre de 2026 y lo usamos una sola vez, al final, como examen.

**El examen de 2026.** En el mercado, el modelo {v_mer} al método más sencillo (error de {n1(d['e_mer'])} puntos frente a {n1(d['b_mer'])}). En las ventas del Laboratorio {v_lab} (error de {n1(d['e_lab'])} puntos frente a {n1(d['b_lab'])}).

**Proyección 2027 (en pesos corrientes, incluye inflación).**
- Mercado total: crecerá cerca de **{pct(d['mer'])}**, con un margen de error típico de ±{n1(d['r_mer'])} puntos. {NOM[alto[0]].capitalize()} sería lo más dinámico ({pct(alto[1])}) y {NOM[bajo[0]]} lo menos ({pct(bajo[1])}).
- Ventas del Laboratorio: crecerán cerca de **{pct(d['lab'])}**, con ±{n1(d['r_lab'])} puntos.

**Qué significa.**
- Úsese como referencia con rango, no como meta exacta. Con solo cinco años de historia, el modelo se parece al promedio de lo ocurrido y no distingue bien escenarios de crecimiento bajo. Las cifras por especie son menos confiables que el total.
- Entre las variables, las que más ayudan a explicar las ventas del Laboratorio son los precios reales de la carne de cerdo y del huevo. El PIB, el salario mínimo y el dólar casi no aportan. El resultado muestra asociaciones del pasado, no efectos causales.
- Conviene revisar el modelo en 2027, cuando estén los datos de julio a diciembre de 2026.
""" + ("\n*BORRADOR con cifras de ejemplo: se actualiza solo con los resultados finales.*\n" if d["borrador"] else "")


def main():
    borrador = "--borrador" in sys.argv or not (C.REP / "proyeccion_2027_base.csv").exists()
    t = texto(datos(borrador))
    palabras = len(re.findall(r"\w+", re.sub(r"[#*]", "", t.split("*BORRADOR")[0])))
    assert palabras <= 350, f"El resumen tiene {palabras} palabras (maximo 350)"
    (C.ROOT / "resumen").mkdir(exist_ok=True)
    (C.ROOT / "resumen" / "resumen_ejecutivo.md").write_text(t)
    print(t)
    print(f"[{palabras} palabras]")


if __name__ == "__main__":
    main()
