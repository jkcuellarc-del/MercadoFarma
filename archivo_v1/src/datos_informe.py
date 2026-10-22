"""Cifras de la ficha de datos y del diagnostico de calidad para el informe (informe/datos_informe.json)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
raw = pd.read_csv(ROOT / "Base Mercado Salud Animal.csv", encoding="utf-8-sig", dtype=str)
n_raw = len(raw)
blank = raw.isna().all(axis=1)
d = raw[~blank]
dup = int(d.duplicated().sum())
v = d.drop_duplicates()
num = lambda c: pd.to_numeric(v[c].str.replace(",", "").str.rstrip("%"), errors="coerce")
tipos = {"Especie": "Categórica", "Segmento": "Categórica", "Año": "Entera", "Subgrupo": "Categórica", "Mes": "Categórica (nombre del mes)",
         "Mercado": "Numérica (COP; texto con comas)", "Crec Mercado Q movil": "Porcentaje (texto con %)", "Crec Mercado Año": "Porcentaje (texto con %)",
         "Fecha": "Fecha (dd/mm/aaaa)", "Grupo Empresa": "Categórica (etiqueta ambigua)", "Precio Leche": "Numérica (COP/litro)",
         "Precio Carne Res": "Numérica (COP/kg)", "Precio carne cerdo": "Numérica (COP/kg)", "Precio huevo": "Numérica (COP)",
         "Precio Pollo": "Numérica (COP/kg)", "Perros": "Entera (texto con comas)", "Gatos": "Entera (texto con comas)", "IPC": "Numérica (índice)",
         "Inflación Mensual": "Numérica (fracción)", "PIB": "Numérica (% anual)", "PIB Agro": "Numérica (% anual)", "Porc Crec SMMLV": "Numérica (fracción)",
         "Venta Laboratorio": "Numérica (COP; con comas)", "Share Laboratorio": "Numérica (fracción)", "Crec Laboratorio año": "Porcentaje (texto con %)"}
ficha = [{"columna": c, "tipo": tipos[c], "faltantes": int(d[c].isna().sum()), "pct": float(d[c].isna().mean() * 100), "unicos": int(d[c].nunique())} for c in raw.columns]
f = pd.to_datetime(v.Fecha, format="%d/%m/%Y")
m, vl, sh = num("Mercado"), num("Venta Laboratorio"), num("Share Laboratorio")
out = {
    "filas_brutas": n_raw, "filas_vacias": int(blank.sum()), "filas_validas": int(len(d)), "duplicadas": dup, "filas_analisis": int(len(v)),
    "columnas": int(raw.shape[1]), "fecha_min": f.min().strftime("%Y-%m"), "fecha_max": f.max().strftime("%Y-%m"),
    "subgrupos": int(v.Subgrupo.nunique()), "series": int(v.groupby(["Especie", "Segmento", "Subgrupo"]).ngroups),
    "mercado_cero": int((m == 0).sum()), "lab_negativas": int((vl < 0).sum()), "lab_mayor_mercado": int((vl > m).sum()), "share_mayor_1": int((sh > 1).sum()),
    "lab_filas_con_venta": {int(y): int(((vl != 0) & (v.Año.astype(float) == y)).sum()) for y in range(2020, 2027)},
    "grupo_empresa_valores": int(v["Grupo Empresa"].nunique()), "grupo_empresa_nulos": int(v["Grupo Empresa"].isna().sum()),
    "segmentos_por_especie": {e: sorted(g.Segmento.unique().tolist()) for e, g in v.groupby("Especie")},
    "filas_por_especie": v.Especie.value_counts().to_dict(),
    "ficha": ficha,
}
(ROOT / "informe").mkdir(exist_ok=True)
(ROOT / "informe" / "datos_informe.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in out.items() if k != "ficha"}, indent=1, ensure_ascii=False))
print(pd.DataFrame(ficha).to_string())
