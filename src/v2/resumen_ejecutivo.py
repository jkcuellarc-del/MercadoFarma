"""Genera el resumen ejecutivo (maximo 350 palabras) con las cifras finales del proyecto.

Lee reports/v2/proyeccion_2027_base.csv (proyeccion final) y reports/v2/prueba_resultados.json (examen unico de 2026).
Sin esos archivos (o con --borrador) produce un BORRADOR con cifras de ejemplo marcadas, para revisar el texto.
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
        return {"mer": 0.154, "lab": 0.206, "alt_mer": 0.137, "alt_lab": 0.223, "esp": {"CA": 0.141, "Cattle": 0.125, "Poultry": 0.097, "Swine": 0.208},
                "e_mer": 9.2, "b_mer": 8.4, "e_lab": 4.4, "b_lab": 4.1, "e_alt": 7.2, "r_mer": 5.6, "r_lab": 5.7, "borrador": True}
    p = pd.read_csv(C.REP / "proyeccion_2027_base.csv").set_index("Especie")
    q = pd.read_csv(C.REP / "proyeccion_2027_alt.csv").set_index("Especie")
    t = json.loads((C.REP / "prueba_resultados.json").read_text())
    lab = t["variante_lab"]
    ban = json.loads((C.REP / "bandas_error.json").read_text())
    mb = lambda x: min(x["B1_crecimiento_hace_12m"]["MAE_pp"], x["B2_media_especie"]["MAE_pp"])
    return {"mer": p.loc["Total", "crec_mercado"], "lab": p.loc["Total", "crec_lab"], "alt_mer": q.loc["Total", "crec_mercado"], "alt_lab": q.loc["Total", "crec_lab"],
            "esp": {e: q.loc[e, "crec_mercado"] for e in NOM}, "e_mer": t["mercado"]["MAE_pp"], "b_mer": mb(t["mercado"]),
            "e_lab": t[lab]["MAE_pp"], "b_lab": mb(t[lab]), "e_alt": t["mercado"]["alternativa_mejor_cv"]["MAE_pp"],
            "r_mer": ban["mercado"]["Total"], "r_lab": ban["lab"]["Total"], "borrador": False}


def texto(d):
    esp = sorted(d["esp"].items(), key=lambda kv: kv[1])
    alto, bajo = esp[-1], esp[0]
    v_mer = veredicto(d["e_mer"], d["b_mer"], d["b_mer"])
    v_lab = veredicto(d["e_lab"], d["b_lab"], d["b_lab"])
    return f"""# Resumen ejecutivo: el mercado de salud animal y el Laboratorio en 2027

**Contexto.** El Laboratorio vende medicinas y vacunas para mascotas, bovinos, cerdos y aves en Colombia. Para planear 2027 (metas, presupuesto, inventarios) necesita saber cuánto crecerán el mercado y sus propias ventas. Usamos ventas mensuales de 2020 a junio de 2026, precios de la carne, la leche, el huevo y el pollo, inflación, PIB, salario mínimo y dólar.

**Cómo se hizo.** Probamos diez modelos estadísticos, comparados por bloques de tiempo con datos que no habían visto, y elegimos el más simple entre los de rendimiento parecido. El primer semestre de 2026 se guardó bajo llave y se usó una sola vez, como examen.

**El examen.** En el mercado, el modelo elegido {v_mer} al método más sencillo (error de {n1(d['e_mer'])} frente a {n1(d['b_mer'])} puntos); en las ventas del Laboratorio, {v_lab} ({n1(d['e_lab'])} frente a {n1(d['b_lab'])}). Un modelo más flexible, que habíamos descartado por complejo, rindió mejor (mercado: {n1(d['e_alt'])} puntos). Como lo conocimos después de elegir, no lo adoptamos: se validará con los datos de julio a diciembre de 2026.

**Proyección 2027 (pesos corrientes, incluye inflación).**
- Mercado: cerca de **{pct(d['mer'])}** ({pct(d['alt_mer'])} con el modelo flexible), con margen de error típico de ±{n1(d['r_mer'])} puntos.
- Laboratorio: cerca de **{pct(d['lab'])}** ({pct(d['alt_lab'])}), con ±{n1(d['r_lab'])} puntos.
- Por especie, con el modelo flexible: {NOM[alto[0]]} lo más dinámico ({pct(alto[1])}) y {NOM[bajo[0]]} lo menos ({pct(bajo[1])}).

**Qué significa.**
- Úsese como referencia con rango, no como meta exacta: con solo cinco años de historia el modelo se parece al promedio de lo ocurrido y no anticipa caídas.
- Lo que más ayuda a explicar las ventas del Laboratorio son los precios reales de la carne de cerdo y del huevo. El PIB, el salario mínimo y el dólar casi no aportan.
- Las cifras por especie son menos confiables que el total. Los resultados muestran asociaciones del pasado, no causas.
- Recomendación: planear 2027 con el rango entre ambos modelos y revisar la proyección en el primer trimestre de 2027.
""" + ("\n*BORRADOR con cifras de ejemplo.*\n" if d["borrador"] else "")


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
