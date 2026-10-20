# Proyección 2027 del mercado de salud animal (Colombia) y del laboratorio

Rama de trabajo: `claude/nifty-ritchie-baueku`. Simulador publicado: https://claude.ai/artifact/WpUvY3RBuvs6sNJ4LK84mc

## Pipeline (ejecutar en este orden)
1. `src/prepare_data.py`: limpia la base y completa julio-diciembre 2026 (ensamble estacional de 3 métodos).
2. `src/build_features.py`: variables de 12 meses móviles, one-hot, escalamiento y partición cronológica.
3. `src/train_models.py`: compara línea base, Ridge, Elastic Net, Random Forest, Gradient Boosting y Ridge por especie.
4. `src/lab_busqueda.py`: búsqueda de mejor modelo para el laboratorio (con mercado proyectado como entrada).
5. `src/final_model.py`: modelo final y escenario base 2027.
6. `src/export_simulador.py` y `src/build_simulador.py`: generan `simulador/index.html`.

## Decisiones del usuario
- Poultry −20% en 2026 y la participación alta de Swine son reales. Ventas negativas del laboratorio = devoluciones válidas.
- Se modela crecimiento nominal (el IPC es una variable del simulador). 2026 H2 se completa con modelo estacional.
- Precios jul-dic 2026 = valor de junio. Enfoque de 12 meses móviles por especie y mes.
- Perros y gatos se omiten. IPC con pendiente propia para CA (`ipc_yoy_CA`), solo lo que dice la data.
- Modelo final: Ridge por especie (mercado alpha 100, laboratorio alpha 50). El simulador solo muestra porcentajes.
- Variables generales del simulador mueven todas las especies a la vez.

## Valores base 2027
IPC 5,1% (analistas Banco de la República), PIB 2,3% (BBVA Research), PIB agro 2,7% y SMMLV 11,9% (promedios, sin pronóstico),
precios en su nivel de junio 2026.

## Pendientes / riesgos
- Laboratorio en Bovinos 2027 = 3,0% (poco confiable). Margen de error típico: mercado ±5 a 8 pts, laboratorio ±2 a 6 pts.
- No se pudo abrir las páginas de Porkcolombia ni del DANE desde el entorno: validar con cifras oficiales.
- `Crec Mercado Año` de la base no coincide con ninguna definición probada; no se usa.
- El simulador es una foto del modelo: regenerar si hay datos nuevos.
