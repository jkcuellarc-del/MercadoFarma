# Ficha de datos

Informe Técnico de Mercado Farmacéutico de Salud Animal en Colombia · Zoetis Colombia · Sección 2.1. Los textos con ⚠️ están pendientes de confirmación por el equipo.

| Atributo | Descripción |
|---|---|
| **Nombre del conjunto** | `Base Mercado Salud Animal.csv` (formato largo: un registro por especie, segmento, subgrupo y mes), más `TRM.csv` (Banco de la República). |
| **Fuente: mercado** | SIMVET (<https://plataforma-simvet.com/>), con cuenta y licencia. Reporta la venta de productos farmacéuticos (**sell-in**) de **31 laboratorios** nacionales y multinacionales. Los reportes no muestran nombres de laboratorios ni de marcas. Cobertura: enero de 2020 a junio de 2026. |
| **Fuente: ventas del Laboratorio** | Interna de Zoetis Colombia, por especie, segmento y subgrupo. |
| **Fuente: población de perros y gatos** | Minsalud: reporte de vacunación antirrábica 2017 y consolidado nacional 2019 (6.403.444 perros y 1.938.517 gatos). Crecimiento anual 2020 a 2026: Euromonitor International (Pet Healthcare, Historic growth, Pet population). La serie de la base es la población de 2019 multiplicada por esos crecimientos. No se usa en el modelo. |
| **Otras fuentes** | Precios en pie y de leche y huevo (DANE-SIPSA, Fedegán, Porkcolombia, Fenavi), IPC y PIB (DANE), salario mínimo (Siigo) y TRM (Banco de la República). Ver Anexo A del informe. |
| **Licencia o autorización** | SIMVET: información privilegiada pero no confidencial; uso permitido por la licencia contratada. Ventas del Laboratorio: propiedad de Zoetis Colombia. Fuentes públicas: términos de uso de cada entidad. Euromonitor: licencia de la compañía. ⚠️ *[Por confirmar: alcance de la licencia de Euromonitor para citar cifras]* |
| **Fecha de acceso** | 18 de octubre de 2026 para todas las fuentes. ⚠️ *[Por confirmar: el pie de TRM.csv indica descarga el 21 de octubre de 2026; definir cuál fecha citar]* |
| **Filas y columnas** | 8.268 filas y 25 columnas (sin filas vacías ni duplicadas); TRM: 81 meses. |
| **Periodo** | Enero de 2020 a junio de 2026 (78 meses). |
| **Granularidad** | 106 series de mercado (especie × segmento × subgrupo), con 83 nombres de subgrupo. |
| **Cobertura por especie** | Animales de compañía: 6 segmentos. Bovinos: 5. Cerdos: 2 (antimicrobiano y vacunas). Aves: 1 (solo vacunas). |
| **Marca "Compite Laboraorio"** | Columna SI/NO que indica si el Laboratorio compite en la serie (el encabezado del archivo trae un error de ortografía). Es SI en 2.589 filas y en ellas está toda la venta del Laboratorio. ⚠️ *[Por confirmar: definición de la marca]* |
| **Formato** | CSV con codificación UTF-8 con BOM; números con coma de miles; los crecimientos vienen como fracciones. |

## Columnas, tipos y faltantes

| Columna | Tipo | Faltantes | Observación |
|---|---|--:|---|
| Especie | Categórica | 0 (0,0%) |  |
| Segmento | Categórica | 0 (0,0%) |  |
| Año | Entera | 0 (0,0%) |  |
| Subgrupo | Categórica | 0 (0,0%) |  |
| Mes | Categórica (nombre del mes) | 0 (0,0%) |  |
| Mercado | Numérica (COP; texto con comas) | 0 (0,0%) | Incluye 429 meses con valor cero |
| Crec Mercado Q movil | Fracción (crecimiento 12 meses sobre trimestre móvil) | 1.683 (20,4%) | Vacío al inicio de cada serie |
| Crec Mercado Año | Fracción (definición no reconciliable) | 1.428 (17,3%) | Definición no reconciliable; no se usa |
| Fecha | Fecha (dd/mm/aaaa) | 0 (0,0%) |  |
| Compite Laboraorio | Categórica binaria (SI/NO) | 0 (0,0%) | Se usa para definir el mercado donde compite |
| Precio Leche | Numérica (COP/litro) | 5.616 (67,9%) | Solo bovinos (faltante por diseño) |
| Precio Carne Res | Numérica (COP/kg, ganado en pie) | 5.616 (67,9%) | Solo bovinos (por diseño); es el precio del ganado en pie |
| Precio carne cerdo | Numérica (COP/kg, cerdo en pie) | 7.020 (84,9%) | Solo cerdos (por diseño); es el precio del cerdo en pie |
| Precio huevo | Numérica (COP) | 6.396 (77,4%) | Solo aves (por diseño) |
| Precio Pollo | Numérica (COP/kg) | 6.396 (77,4%) | Solo aves (por diseño); es el precio del pollo vivo |
| Perros | Entera (texto con comas) | 5.772 (69,8%) | Solo animales de compañía; no se usa en el modelo |
| Gatos | Entera (texto con comas) | 5.772 (69,8%) | Solo animales de compañía; no se usa en el modelo |
| IPC | Numérica (índice) | 0 (0,0%) |  |
| Inflación Mensual | Numérica (fracción) | 0 (0,0%) |  |
| PIB | Numérica (% anual) | 0 (0,0%) | Un valor por año |
| PIB Agro | Numérica (% anual) | 0 (0,0%) | Un valor por año |
| Porc Crec SMMLV | Numérica (fracción) | 0 (0,0%) | Un valor por año |
| Venta Laboratorio | Numérica (COP; texto con comas) | 0 (0,0%) | Cero antes de 2022; incluye devoluciones negativas |
| Share Laboratorio | Numérica (fracción) | 0 (0,0%) | Puede superar 1 |
| Crec Laboratorio año | Fracción (crecimiento anual de la venta) | 6.618 (80,0%) | Vacío antes de que existan 12 meses de venta |

Los faltantes de precios y de población son estructurales: cada precio solo aplica a una especie. No son datos perdidos y no se imputaron.
