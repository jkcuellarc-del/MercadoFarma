# Prompts del desarrollo del modelo

Sesión del 20 al 22 de octubre de 2026. Se listan los mensajes del usuario (47) en orden, resumidos. "Aceptó" es lo que el equipo aprobó o decidió; "Descartó" es lo que el equipo rechazó o lo que no se ejecutó (con el motivo).

## A. Definición del problema y de los datos

| # | Prompt (resumen) | Aceptó | Descartó |
|---|---|---|---|
| 1 | Presenta a Zoetis (el Laboratorio), 4 especies (CA, Cattle, Swine, Poultry), segmentos, ventas del Laboratorio 2022-2026, mercado mensual, variables macro y escenarios regular/estable/optimista. Pide revisar si los datos permiten proyectar 2027 y un simulador con PIB, inflación, SMMLV y precios. | Diagnóstico de viabilidad con las bases cargadas; clasificación por umbrales de 8 % y 15 %. | — |
| 2-4 | Cómo cargar el archivo a GitHub; "ya lo subí"; "hecho". | Carga de `Base Mercado Salud Animal.csv`. | — |
| 5 | Decisiones: (1) Poultry cayó 20 %, la participación de Swine es real y el Laboratorio lidera; (2) las ventas negativas son devoluciones válidas; (3) modelar crecimiento nominal y documentar el efecto del IPC; (4) completar 2026 con modelo estacional. | Las cuatro: se conservaron las anomalías, las devoluciones y el crecimiento nominal; 2026 se completó con modelo estacional. | — |
| 6 | (1) Mantener en julio-diciembre de 2026 el precio de junio de carne, cerdo, pollo, leche y huevo; (2) enfoque mensual de 12 meses móviles. | Enfoque mensual de 12 meses móviles; precios de 2026 constantes en el nivel de junio, como supuesto. | — |
| 7 | Omitir el número de perros y gatos; relacionar CA con IPC/inflación (hogares priorizan gastos esenciales). Luego revisar el plan de modelos. | Se retiró la población como predictor; se creó `ipc_yoy_CA`. | La población de perros y gatos como variable del modelo. |
| 8 | Responde a mi pregunta: el efecto "inflación frena CA" no se agrega como ajuste manual; "deja solo lo que dice la data". Pide ejecutar el plan. | Solo lo que aprende de los datos; ejecución del plan. | El ajuste opcional y explícito de la hipótesis de inflación. |

## B. Modelos y protocolo

| # | Prompt (resumen) | Aceptó | Descartó |
|---|---|---|---|
| 9 | De acuerdo con el modelo del mercado; buscar un modelo más preciso para el Laboratorio. Simulador después. | Modelo del mercado; búsqueda de mejor modelo para el Laboratorio (se agregó el mercado donde compite como entrada). | — |
| 10 | De acuerdo con el modelo; hablar del simulador. | Modelos de la v1 (luego reemplazados en el rediseño, ver #19). | — |
| 11 | Simulador: (1) página web; (2) solo porcentajes; (3) pronósticos de Porkcolombia, IPC y PIB del DANE; (4) controles generales mueven todas las especies. | Página web; solo porcentajes; fuentes indicadas; controles generales para todas las especies. | — |
| 12-14 | Si la conversación y el artefacto se conservan; despedida. | — | — |
| 15 | Retomar: revisar y modificar desde el inicio para documentar y crear un informe. | Rediseño documentado. | — |
| 16 | Especificación del informe .docx: título, 7 secciones y anexo con fuentes APA 7 (contenido detallado por sección). | Estructura de 7 secciones + Anexo A (fuentes APA 7) + Anexo B. | — |
| 17 | Validar si se usaron: regresión logística, KNN, Naive Bayes, ROC-AUC, exactitud/exhaustividad, SVM (C, gamma, núcleo), Pipeline, árboles y poda, bosque/boosting/importancias, redes neuronales, ARIMA/SARIMA, etc. | Se usó: línea base lineal, Pipeline, validación sin mirar la prueba, árboles, boosting; el resto se aclaró. | Pendiente de ver el resultado; ver #18 y #20. |
| 18 | Por qué no se usaron KNN, Naive Bayes y SVM. | La explicación. | — |
| 19 | No cambiar el informe hasta terminar el modelo; cambió el archivo fuente; repetir la lectura desde cero asegurando que no se usen los datos de prueba. | Protocolo v2: separación por fecha, sello SHA-256, lectura controlada, prueba de canario. | Cambios al informe en ese momento (se pospusieron). |
| 20 | (1) Incorporar `Compite Laboraorio`; (2) usar regresión lineal con R², Elastic Net, KNN, Bagging/Random Forest, Boosting, con curvas y cálculo de parámetros en cada modelo. | Los diez modelos con búsqueda de hiperparámetros, curvas, R²; mercado donde compite como objetivo adicional. | Naive Bayes, SVM y regresión logística (no son aptos para un objetivo continuo; no se pidieron). |
| 21 | Mejorar el resultado: modificar predictores o usar un método que identifique variables importantes. | Importancia por permutación y cribado de conjuntos de predictores (S0 a S7). | — |
| 22 | Cargó `TRM.csv`; los precios de carnes explican el Laboratorio; probar si la TRM explica el mercado. | Prueba de la TRM como predictor. | La TRM: el resultado no mostró señal, no entró al modelo final. |
| 23 | Qué es la verificación del sello. | La explicación. | — |
| 24 | (1) Precios reales (cerdo, huevo, res, leche, pollo) sin TRM; (2) repetir comparación completa, curvas y regla de selección; (3) ejecutar la prueba una sola vez y retomar el simulador. | Los tres puntos: precios reales (conjunto S7), repetición, prueba una sola vez. | TRM como predictor. |

## C. Entregables

| # | Prompt (resumen) | Aceptó | Descartó |
|---|---|---|---|
| 25 | Mientras corre: resumen ejecutivo de 350 palabras; cuaderno .ipynb que ejecuta de principio a fin con semilla, versiones y rutas relativas. | Resumen de 349 palabras; cuaderno ejecutado (modo rápido y modo completo). | — |
| 26 | Para el simulador usar ambos modelos. | Modelos A y B como rango. | — |
| 27 | Usar imágenes de especies y logo en el simulador; agregar 2 modelos a la tabla de comparación. | Imágenes, logo, tabla de 4 modelos. | — |
| 28 | Qué significa "elegido por la regla". | La explicación. | — |
| 29 | Mencionar que el modelo A es Elastic Net y Ridge; agregar la base (regresión lineal). | Ambos cambios. | — |
| 30 | Para K vecinos, Random Forest y regresión lineal, poner los resultados del examen sin mencionar que ya se habían ejecutado. | Resultados del examen de los tres modelos en el simulador. | No mencionar que ya se habían ejecutado: se rechazó la omisión; se rotuló como "consulta posterior, informativa" (por trazabilidad). |
| 31 | Pausa. | — | — |
| 32 | Retomar: integrantes y roles, Zoetis Colombia, fuentes (SIMVET, interna, Minsalud, Euromonitor) y fecha de consulta. | Rehacer el informe con el protocolo v2 y esos datos. | — |
| 33 | (Resumen automático de contexto, no es un prompt del usuario.) | — | — |

## D. Despliegue, documentación y consultas

| # | Prompt (resumen) | Aceptó | Descartó |
|---|---|---|---|
| 34 | Mostrar el cuaderno .ipynb. | Envío del cuaderno. | — |
| 35 | Qué es la semilla, para qué sirve, por qué 0. | La explicación (convención, sin razón estadística). | La repetición con otras semillas (ofrecida, no pedida). |
| 36-37 | Qué se necesita para desplegar en GitHub; generar `src/v2`, `models/v2`, `reports/v2` y `data/v2` para regenerar el simulador. | Verificación: ya estaban versionadas; el simulador se regeneró idéntico. | — |
| 38-39 | Mover archivos sobrantes; luego, todo lo que no sea de la v2. | Todo lo de la v1 en `archivo_v1/`. | — |
| 40 | Qué se necesita para desplegar en GitHub. | Explicación de GitHub Pages (`/docs`, visibilidad, licencias). | Aún no se ha publicado nada. |
| 41 | Término correcto para precios antes del sacrificio. | "Precio en pie" (ganado gordo, cerdo en pie, pollo vivo). | — |
| 42 | Qué es un archivo .md. | La explicación. | — |
| 43-45 | Ficha de datos en .md (`ficha_datos`); licencia Euromonitor pagada por Zoetis; TRM consultada el 21 de octubre; sin la definición de `Compite Laboraorio`; quitar la fila completa. | `ficha_datos.md` con esos cambios. | La definición y la fila de `Compite Laboraorio`. |
| 46 | Gracias. | — | — |
| 47 | Este reporte. | — | — |

## Notas
- El informe .docx todavía no incluye los cambios de #43-45 (licencia, fecha de la TRM).
- Los puntos de #17 sobre regresión logística, Naive Bayes, SVM, ROC-AUC, redes neuronales y ARIMA no se incorporaron: el objetivo es un crecimiento continuo y con 78 meses de historia.
