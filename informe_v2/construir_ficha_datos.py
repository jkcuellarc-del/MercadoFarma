"""Genera ficha_datos.md (Sección 2.1 y Tabla 1 del informe) desde cifras.json."""
import json
from pathlib import Path

AQUI = Path(__file__).parent
C = json.loads((AQUI / "cifras.json").read_text())
D = C["datos"]
n = lambda x: f"{x:,.0f}".replace(",", ".")
p = lambda x: f"{x:.1f}".replace(".", ",")
PEND = lambda t: f"⚠️ *[Por confirmar: {t}]*"

notas = {
    "Precio Leche": "Solo bovinos (faltante por diseño)", "Precio Carne Res": "Solo bovinos (por diseño); es el precio del ganado en pie",
    "Precio carne cerdo": "Solo cerdos (por diseño); es el precio del cerdo en pie", "Precio huevo": "Solo aves (por diseño)",
    "Precio Pollo": "Solo aves (por diseño); es el precio del pollo vivo",
    "Perros": "Solo animales de compañía; no se usa en el modelo", "Gatos": "Solo animales de compañía; no se usa en el modelo",
    "Crec Mercado Q movil": "Vacío al inicio de cada serie", "Crec Mercado Año": "Definición no reconciliable; no se usa",
    "Crec Laboratorio año": "Vacío antes de que existan 12 meses de venta", "Compite Laboraorio": "Se usa para definir el mercado donde compite",
    "Venta Laboratorio": "Cero antes de 2022; incluye devoluciones negativas", "Share Laboratorio": "Puede superar 1",
    "PIB": "Un valor por año", "PIB Agro": "Un valor por año", "Porc Crec SMMLV": "Un valor por año",
    "Mercado": f"Incluye {D['mercado_cero']} meses con valor cero",
}

ficha = [
    ("Nombre del conjunto", "`Base Mercado Salud Animal.csv` (formato largo: un registro por especie, segmento, subgrupo y mes), más `TRM.csv` (Banco de la República)."),
    ("Fuente: mercado", "SIMVET (<https://plataforma-simvet.com/>), con cuenta y licencia. Reporta la venta de productos farmacéuticos (**sell-in**) de **31 laboratorios** nacionales y multinacionales. Los reportes no muestran nombres de laboratorios ni de marcas. Cobertura: enero de 2020 a junio de 2026."),
    ("Fuente: ventas del Laboratorio", "Interna de Zoetis Colombia, por especie, segmento y subgrupo."),
    ("Fuente: población de perros y gatos", "Minsalud: reporte de vacunación antirrábica 2017 y consolidado nacional 2019 (6.403.444 perros y 1.938.517 gatos). Crecimiento anual 2020 a 2026: Euromonitor International (Pet Healthcare, Historic growth, Pet population). La serie de la base es la población de 2019 multiplicada por esos crecimientos. No se usa en el modelo."),
    ("Otras fuentes", "Precios en pie y de leche y huevo (DANE-SIPSA, Fedegán, Porkcolombia, Fenavi), IPC y PIB (DANE), salario mínimo (Siigo) y TRM (Banco de la República). Ver Anexo A del informe."),
    ("Licencia o autorización", f"SIMVET: información privilegiada pero no confidencial; uso permitido por la licencia contratada. Ventas del Laboratorio: propiedad de Zoetis Colombia. Fuentes públicas: términos de uso de cada entidad. Euromonitor: licencia de la compañía. {PEND('alcance de la licencia de Euromonitor para citar cifras')}"),
    ("Fecha de acceso", f"18 de octubre de 2026 para todas las fuentes. {PEND('el pie de TRM.csv indica descarga el 21 de octubre de 2026; definir cuál fecha citar')}"),
    ("Filas y columnas", f"{n(D['filas'])} filas y {D['columnas']} columnas (sin filas vacías ni duplicadas); TRM: 81 meses."),
    ("Periodo", f"Enero de 2020 a junio de 2026 ({D['meses']} meses)."),
    ("Granularidad", f"{D['series']} series de mercado (especie × segmento × subgrupo), con {D['subgrupos']} nombres de subgrupo."),
    ("Cobertura por especie", "Animales de compañía: 6 segmentos. Bovinos: 5. Cerdos: 2 (antimicrobiano y vacunas). Aves: 1 (solo vacunas)."),
    ('Marca "Compite Laboraorio"', f"Columna SI/NO que indica si el Laboratorio compite en la serie (el encabezado del archivo trae un error de ortografía). Es SI en {n(D['compite_filas_si'])} filas y en ellas está toda la venta del Laboratorio. {PEND('definición de la marca')}"),
    ("Formato", "CSV con codificación UTF-8 con BOM; números con coma de miles; los crecimientos vienen como fracciones."),
]

o = ["# Ficha de datos", "",
     "Informe Técnico de Mercado Farmacéutico de Salud Animal en Colombia · Zoetis Colombia · Sección 2.1. "
     "Los textos con ⚠️ están pendientes de confirmación por el equipo.", "",
     "| Atributo | Descripción |", "|---|---|"]
o += [f"| **{a}** | {d} |" for a, d in ficha]
o += ["", "## Columnas, tipos y faltantes", "",
      "| Columna | Tipo | Faltantes | Observación |", "|---|---|--:|---|"]
o += [f"| {r['columna']} | {r['tipo']} | {n(r['faltantes'])} ({p(r['pct'])}%) | {notas.get(r['columna'], '')} |" for r in C["ficha"]]
o += ["", "Los faltantes de precios y de población son estructurales: cada precio solo aplica a una especie. No son datos perdidos y no se imputaron.", ""]
(AQUI / "ficha_datos.md").write_text("\n".join(o), encoding="utf-8")
print("ok")
