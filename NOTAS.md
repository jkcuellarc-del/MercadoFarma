# Proyección 2027 del mercado de salud animal (Colombia) y del laboratorio: notas de traspaso

Rama de trabajo: `claude/nifty-ritchie-baueku`. Simulador (privado): https://claude.ai/artifact/WpUvY3RBuvs6sNJ4LK84mc

## Estado actual (v2, con datos de prueba sellados)
- Datos: `Base Mercado Salud Animal.csv` (nueva, con columna `Compite Laboraorio`) y `TRM.csv`. Se sellan por fecha: desarrollo hasta dic-2025, prueba ene-jun 2026 (`src/v2/sellar_base.py`).
- Pipeline: `src/v2/` (ver `src/v2/LEEME.md`). Desarrollo: variables, validación cruzada por bloques con purga, 10 modelos, curvas, cribado de predictores, importancia de variables.
- Predictores finales: inflación, PIB, PIB agro, salario mínimo y precios en términos reales. La TRM no aportó.
- Verificación del sello (canario con cifras de 2026 alteradas): `reports/v2/verificacion_sello.txt`.
- Examen de 2026: consulta principal una sola vez (`reports/v2/prueba_resultados.json`) y consulta complementaria posterior, solo informativa (`reports/v2/prueba_complementaria.json`: K vecinos, Random Forest, regresión lineal). Las dos quedan en `reports/v2/accesos_prueba.log`.
- Resultado: el modelo elegido por la regla (A: Elastic Net en mercado, Ridge por especie en laboratorio) no superó a los métodos sencillos en el examen. Gradient Boosting (B) fue el mejor en validación y examen, pero se incorporó después de ver el examen.
- Proyección base 2027: mercado 15,4% (A) y 13,7% (B); laboratorio 20,6% (A) y 22,3% (B).
- Entregables: `resumen/resumen_ejecutivo.md` (349 palabras), `cuaderno/pipeline_completo.ipynb` (modo reducido) y `cuaderno/pipeline_completo_modo_completo_ejecutado.ipynb`, `simulador/index.html` (dos modelos, íconos por especie, logo).

## Pendientes
1. **Rehacer el informe** (`informe/`, `.docx`) con el protocolo v2: la versión actual usa el protocolo v1 (base anterior, sin `Compite Laboraorio`, sin TRM, sin precios reales). Debe describir la consulta complementaria del examen en la sección 3.
2. Completar lo resaltado en amarillo del informe: quién decide, autorización de datos, fechas de consulta de las fuentes, roles del equipo.
3. Validar con los datos de julio a diciembre de 2026 (la prueba realmente nueva) y revisar el modelo B.
4. Confirmar con el negocio los costos del error (supuesto 2:1) y las cifras oficiales de inflación, PIB y salario mínimo de 2027.
5. Revisar con el equipo comercial la proyección del laboratorio en bovinos.

## Regla para no contaminar la prueba
No ejecutar `python -m src.v2.prueba` otra vez (candado en `reports/v2/prueba_consultada.lock`). Cualquier nueva medición sobre ene-jun 2026 es una consulta adicional y debe declararse.
