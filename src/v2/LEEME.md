# Lectura sellada (v2)

Objetivo: que ningún paso de desarrollo (limpieza, variables, escalamiento, selección de modelo) pueda ver
los datos de prueba (enero a junio de 2026).

| Paso | Comando | Qué hace | ¿Ve la prueba? |
|---|---|---|---|
| 1 | `python -m src.v2.sellar_base` | Parte la base por fecha: `data/v2/desarrollo.csv` (hasta dic-2025) y `data/v2/sellado/prueba.csv` (desde ene-2026). Guarda los hash SHA-256 en `data/v2/manifiesto.json`. | Solo para partir el archivo, sin interpretarlo |
| 2 | `python -m src.v2.variables` | Variables de 12 meses móviles solo con `desarrollo.csv`. | No |
| 3 | `python -m src.v2.desarrollo` | Validación cruzada con purga, selección, umbral y diagnósticos. | No |
| 4 | `python -m src.v2.verificar_sello` | Reemplaza las cifras de 2026 por 999999999 y repite 1 a 3: los resultados deben ser idénticos. | Copia alterada |
| 5 | `python -m src.v2.prueba` | Única evaluación en prueba (candado y registro de acceso). | Sí, es su función |

Reglas: `datos.leer_desarrollo()` falla si encuentra un mes posterior a dic-2025; `datos.leer_prueba()` verifica el
hash del archivo sellado y escribe cada acceso en `reports/v2/accesos_prueba.log`. Antes de la evaluación única el
registro debe estar vacío.
