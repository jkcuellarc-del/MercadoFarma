// ------------------------------------------------------------------ atajos de datos
const TM = C.tareas.mercado, TC = C.tareas.compite, TL = C.tareas.lab_ym, TLn = C.tareas.lab;
const PR = C.prueba, PC = C.prueba_compl, D = C.datos;
const cv = (T, m) => T.comparacion_cv.find(r => r.modelo === m);
const proy = (g, e) => C.proy[g].find(r => r.Especie === e);
const band = (g, k, e) => C.bandas[g][k][e];
const sensV = (n) => C.sens.find(r => r.variable.startsWith(n));
const NOM = { ols_esp: 'Regresión lineal por especie', ridge_esp: 'Ridge por especie', enet_esp: 'Elastic Net por especie', ols: 'Regresión lineal', ridge: 'Ridge común',
  enet: 'Elastic Net común', knn: 'K vecinos más cercanos', bagging: 'Bagging de árboles', rf: 'Random Forest', gbm: 'Gradient Boosting',
  B1_crecimiento_hace_12m: 'Base 1: crecimiento de hace 12 meses', B2_media_especie: 'Base 2: promedio histórico de la especie' };
const ESP = { CA: 'Animales de compañía', Cattle: 'Bovinos', Poultry: 'Aves', Swine: 'Cerdos', Total: 'Total' };
const EST = ['CA', 'Cattle', 'Poultry', 'Swine'];
const emb = (T, s) => T.sens_validacion.find(r => r.validacion.includes(s));
const imp = (t, cj, v) => C.importancia.find(r => r.tarea === t && r.conjunto === cj && r.variable === v);
const scr = (t, cj, o = 'nominal') => C.screening.find(r => r.tarea === t && r.conjunto === cj && r.objetivo === o);
const prm = o => Object.entries(o).map(([k, v]) => `${k.replace('estimator__', '').replace(/_/g, ' ')} = ${v === null ? 'sin límite' : (typeof v === 'number' ? f1(v, Number.isInteger(v) ? 0 : (v < 0.01 ? 3 : 2)) : v)}`).join('; ');
const hp = (T, m) => { const s = T.seleccion.mejores[m]; return s ? prm(s.params) + (s.balance ? '; con ponderación' : '') : '–'; };

const kids = [];

// ------------------------------------------------------------------ portada
kids.push(new Paragraph({ spacing: { before: 2200, after: 120 }, children: [new TextRun({ text: 'INFORME TÉCNICO', size: 22, bold: true, color: ACC, characterSpacing: 60 })] }));
kids.push(new Paragraph({ heading: HeadingLevel.TITLE, spacing: { after: 240 }, children: [new TextRun('Informe Técnico de Mercado Farmacéutico de Salud Animal en Colombia')] }));
kids.push(new Paragraph({ spacing: { after: 500 }, children: [new TextRun({ text: 'Proyección del crecimiento 2027 del mercado y de las ventas del Laboratorio, con simulador de escenarios', size: 26, color: MUTED })] }));
kids.push(table(['Campo', 'Detalle'], [
  ['Versión', 'Borrador 2, octubre de 2026 (protocolo experimental v2)'],
  ['Organización', 'Zoetis Colombia (en este informe, "el Laboratorio")'],
  ['Equipo', 'Juan Cuellar Chaparro (Jefe)\nOscar Hernandez Alomia (Líder)\nMariana Jaramillo Naranjo (Crack)'],
  ['Código, datos y cuaderno', 'github.com/jkcuellarc-del/MercadoFarma, rama claude/nifty-ritchie-baueku'],
  ['Simulador (versión web)', 'claude.ai/artifact/WpUvY3RBuvs6sNJ4LK84mc (privado; ver Sección 6.8)'],
  ['Convención', 'El texto resaltado en amarillo es información que solo el equipo puede confirmar.'],
], [2400, 6960], { boldFirst: true }));

kids.push(new Paragraph({ pageBreakBefore: true, heading: HeadingLevel.HEADING_1, children: [new TextRun('Resumen')] }));
kids.push(P(`Zoetis Colombia necesita una referencia de cuánto crecerá en 2027 el mercado farmacéutico de salud animal y cuánto crecerán sus propias ventas, por especie (animales de compañía, bovinos, cerdos y aves). Con las ventas mensuales de ${D.fecha_min} a ${D.fecha_max} (${f1(D.filas, 0)} filas, ${D.columnas} columnas) y variables económicas y de precios, se compararon diez modelos con validación cruzada por bloques de tiempo con purga, dentro de un Pipeline y con los datos de 2026 sellados durante todo el desarrollo.`));
kids.push(B(`**Proyección base 2027 (nominal):** mercado ${pct(proy('A', 'Total').crec_mercado)} con el modelo elegido por la regla de selección (A) y ${pct(proy('B', 'Total').crec_mercado)} con Gradient Boosting (B); ventas del Laboratorio ${pct(proy('A', 'Total').crec_lab)} (A) y ${pct(proy('B', 'Total').crec_lab)} (B). Margen de error típico: ±${f1(band('A', 'mercado', 'Total'))} puntos en el mercado y ±${f1(band('A', 'lab', 'Total'))} en el Laboratorio.`));
kids.push(B(`**Evidencia del examen (enero a junio de 2026):** el modelo A **no superó** a los métodos sencillos (mercado: ${f1(PR.mercado.MAE_pp)} pp frente a ${f1(PR.mercado.B2_media_especie.MAE_pp)} y ${f1(PR.mercado.B1_crecimiento_hace_12m.MAE_pp)}; Laboratorio: ${f1(PR.lab_ym.MAE_pp)} frente a ${f1(PR.lab_ym.B2_media_especie.MAE_pp)} y ${f1(PR.lab_ym.B1_crecimiento_hace_12m.MAE_pp)}). Gradient Boosting tuvo el menor error en validación y en el examen (${f1(PR.mercado.alternativa_mejor_cv.MAE_pp)} y ${f1(PR.lab_ym.alternativa_mejor_cv.MAE_pp)} pp), pero se incorporó después de ver el examen.`));
kids.push(B('**Límite central:** cinco años de historia y variables macroeconómicas anuales. Los precios reales de la carne de cerdo y del huevo son las variables con señal; el PIB, el salario mínimo y la TRM no aportan. Los efectos son pequeños y aproximados.'));
kids.push(B('**Recomendación:** usar la proyección como referencia con rango entre los modelos A y B, no como meta puntual; no usar la alerta de escenario "regular" como señal operativa; y revalidar con los datos de julio a diciembre de 2026.'));
kids.push(new Paragraph({ spacing: { before: 200, after: 80 }, children: [new TextRun({ text: 'Contenido', bold: true, size: 24, color: ACC })] }));
['1. Problema y decisión', '2. Datos', '3. Preparación y diseño experimental', '4. Modelado', '5. Evaluación', '6. Decisión, límites y gobernanza', '7. Roles y trabajo en equipo', 'Anexo A. Fuentes de datos (APA 7)', 'Anexo B. Reproducibilidad']
  .forEach(t => kids.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: t, size: 22 })] })));

// ------------------------------------------------------------------ 1
kids.push(H1('1. Problema y decisión', true));
kids.push(H2('1.1 Contexto'));
kids.push(P('Zoetis Colombia (en adelante, el Laboratorio) es la filial de una compañía multinacional de salud animal. En Colombia tiene portafolio para cuatro especies: animales de compañía (perros y gatos), bovinos, cerdos y aves. En cada una compite en segmentos como biológicos y vacunas, antimicrobianos, antiparasitarios, hormonales, analgésicos (pain), productos no farmacéuticos y otros farmacéuticos. La base contiene las ventas mensuales de cada segmento, el mercado total en pesos colombianos (incluidos los segmentos y subgrupos donde el Laboratorio no compite) y la participación del Laboratorio.'));
kids.push(H2('1.2 La decisión organizacional'));
kids.push(CALLOUT('**Decisión:** con qué crecimiento del mercado y de las ventas debe planear el Laboratorio el año 2027, por especie: metas comerciales, presupuesto, producción e inventario (los biológicos tienen vida útil limitada) y prioridades de inversión.'));
kids.push(table(['Pregunta', 'Respuesta'], [
  ['¿Quién decide?', '[[confirmar cargo: p. ej., Gerencia General de Zoetis Colombia con Dirección Comercial y Planeación Financiera]]. El equipo del proyecto prepara la evidencia y no toma la decisión.'],
  ['¿Cuándo?', '[[confirmar: fecha del ciclo de planeación 2027]]'],
  ['¿A quién afecta directamente?', 'Equipos comerciales de cada especie (metas y comisiones), cadena de suministro (inventarios), finanzas (presupuesto) y mercadeo (inversión por especie).'],
  ['¿A quién afecta indirectamente?', 'Veterinarios, distribuidores y productores, por la disponibilidad y el precio de los productos; y los animales atendidos, por el acceso a vacunas y tratamientos.'],
  ['¿Qué se hace hoy?', '[[confirmar el método actual de planeación]]. La línea base 1 de este informe reproduce la práctica de repetir el crecimiento de hace 12 meses.'],
], [2600, 6760], { boldFirst: true }));
kids.push(gap());
kids.push(P('La decisión se clasifica con tres escenarios definidos por el negocio: **regular** si el crecimiento es menor a 8%, **estable** si está entre 8% y 15%, y **optimista** si supera 15%.'));
kids.push(H2('1.3 Paradigma elegido y alternativas'));
kids.push(P('Se eligió **aprendizaje supervisado de tipo regresión**: predecir el crecimiento nominal de las ventas de 12 meses móviles (variable continua) a partir de variables económicas y de precios, y derivar el escenario aplicando los umbrales de 8% y 15%. Las alternativas se descartaron por las razones de la tabla.'));
kids.push(table(['Alternativa', 'Por qué no es la principal'], [
  ['Clasificación directa del escenario', `Desperdicia información (un 8,1% y un 14,9% serían iguales) y el desbalance es fuerte: solo ${f1(TM.desbalance[0].pct)}% de las observaciones de entrenamiento del mercado son "regular". Se usa como lectura derivada y se evalúa aparte.`],
  ['Series de tiempo clásicas (ARIMA, suavizado exponencial)', 'Proyectan con la propia historia, pero no permiten el objetivo de simular cambios en PIB, inflación, salario mínimo y precios.'],
  ['Aprendizaje no supervisado', 'No hay una variable objetivo que se pueda recuperar; no responde a la pregunta de proyección.'],
  ['Modelos causales o estructurales', 'Requerirían datos de precios y demanda por producto, y diseños que la base no tiene (Sección 6.6).'],
], [3000, 6360], { boldFirst: true }));
kids.push(H2('1.4 Pérdida técnica y métrica de éxito del negocio'));
kids.push(P('El modelo se entrena minimizando un error de predicción, pero el negocio no gana ni pierde por ese error sino por las decisiones que se toman con él. Por eso se separan dos niveles:'));
kids.push(table(['Nivel', 'Métrica', 'Para qué sirve'], [
  ['Pérdida técnica', 'Error absoluto medio (MAE) y raíz del error cuadrático medio (RMSE), en puntos porcentuales de crecimiento; R² como lectura de la varianza explicada.', 'Entrenar, ajustar hiperparámetros y comparar modelos.'],
  ['Métrica de éxito del negocio', 'Costo esperado por error de escenario: pronosticar un escenario por encima del real cuesta el doble que pronosticarlo por debajo. Se complementa con la proporción de escenarios acertados y la capacidad de detectar el escenario "regular".', 'Decidir si el modelo mejora la planeación frente a la práctica actual.'],
], [1900, 4700, 2760], { boldFirst: true }));
kids.push(gap());
kids.push(P('**Supuesto de costos (a validar con el negocio):** sobrestimar el crecimiento lleva a inventario excedente o vencido y a presupuestos y metas inalcanzables; subestimarlo lleva a desabastecimiento y ventas perdidas. Se asumió que lo primero es dos veces más costoso por cada nivel de escenario de diferencia. [[Confirmar la proporción 2:1 con Finanzas o Cadena de Suministro]].'));
kids.push(P('**Criterio de éxito:** el modelo agrega valor solo si supera a las dos líneas base (repetir el crecimiento de hace 12 meses y usar el promedio histórico de la especie) tanto en validación cruzada como en el examen. [[Confirmar el error máximo tolerable, por ejemplo ±5 pp]].'));
kids.push(H2('1.5 Riesgos éticos iniciales'));
[
  '**Presión sobre personas.** Si una proyección puntual se convierte en meta o base de comisiones, los equipos comerciales cargan el error del modelo. Mitigación: usar rangos y no atar compensaciones a una cifra puntual.',
  '**Uso responsable de antimicrobianos.** Proyectar crecimiento del segmento antimicrobiano puede incentivar un empuje comercial que contradiga las prácticas de uso prudente y la resistencia antimicrobiana. Mitigación: tratar el pronóstico como insumo de abastecimiento, no como meta de promoción.',
  '**Información privilegiada de mercado.** Los datos de SIMVET son información privilegiada, aunque no confidencial, y su uso está amparado por la licencia. Los reportes no muestran nombres de laboratorios ni de marcas; el análisis debe mantenerse agregado y no intentar identificar a competidores. Las ventas del Laboratorio son internas: debe limitarse la difusión del repositorio y del simulador.',
  '**Representatividad.** Las series cubren el agregado nacional, el sell-in de los laboratorios que reportan y solo algunos segmentos por especie (Sección 2.3). El modelo no describe a pequeños productores, regiones o clínicas específicas.',
  '**Sobreconfianza.** Con cinco años de historia, una cifra con decimales transmite una precisión que el modelo no tiene.',
  '**Transparencia sobre el uso de IA.** El código y el análisis se desarrollaron con apoyo de un asistente de inteligencia artificial; las decisiones de negocio y de tratamiento de datos las tomó el equipo (Sección 7).',
].forEach(t => kids.push(B(t)));

// ------------------------------------------------------------------ 2
kids.push(H1('2. Datos'));
kids.push(H2('2.1 Ficha de datos'));
kids.push(table(['Atributo', 'Descripción'], [
  ['Nombre del conjunto', 'Base Mercado Salud Animal.csv (formato largo: un registro por especie, segmento, subgrupo y mes), más TRM.csv (Banco de la República).'],
  ['Fuente: mercado', 'SIMVET (plataforma-simvet.com), a la que se accede con una cuenta con licencia. Reporta la venta de productos farmacéuticos (**sell-in**) de **31 laboratorios** nacionales y multinacionales. Los reportes no muestran nombres de laboratorios ni de marcas. Cobertura: enero de 2020 a junio de 2026.'],
  ['Fuente: ventas del Laboratorio', 'Interna de Zoetis Colombia, por especie, segmento y subgrupo.'],
  ['Fuente: población de perros y gatos', 'Ministerio de Salud y Protección Social (Minsalud): reporte de vacunación antirrábica 2017 y consolidado nacional 2019 (6.403.444 perros y 1.938.517 gatos). Crecimiento anual 2020 a 2026: Euromonitor International (Pet Healthcare, Historic growth, Pet population). La serie de la base es la población de 2019 multiplicada por esos crecimientos (2020: factor 1,0534, igual para perros y gatos). No se usa en el modelo (Sección 2.3).'],
  ['Otras fuentes', 'Precios (DANE-SIPSA, Fedegán, Porkcolombia, Fenavi), IPC y PIB (DANE), salario mínimo (Siigo) y TRM (Banco de la República). Ver Anexo A.'],
  ['Licencia o autorización', 'SIMVET: información privilegiada pero no confidencial; el equipo tiene permiso de uso por la licencia contratada. Ventas del Laboratorio: propiedad de Zoetis Colombia. Fuentes públicas: sujetas a los términos de uso de cada entidad. Euromonitor: licencia de la compañía [[confirmar alcance de la licencia para citar cifras]].'],
  ['Fecha de acceso', '18 de octubre de 2026 para todas las fuentes. Nota: el archivo TRM.csv indica en su pie que se descargó el 21 de octubre de 2026 [[confirmar cuál fecha se debe citar]]. El archivo se cargó al repositorio y se analizó entre el 20 y el 21 de octubre de 2026.'],
  ['Filas y columnas', `${f1(D.filas, 0)} filas y ${D.columnas} columnas (sin filas vacías ni duplicadas); TRM: 81 meses.`],
  ['Periodo', `Enero de 2020 a junio de 2026 (${D.meses} meses).`],
  ['Granularidad', `${D.series} series de mercado (especie × segmento × subgrupo), con ${D.subgrupos} nombres de subgrupo.`],
  ['Cobertura por especie', 'Animales de compañía: 6 segmentos. Bovinos: 5. Cerdos: 2 (antimicrobiano y vacunas). Aves: 1 (solo vacunas).'],
  ['Marca "Compite Laboraorio"', `Columna SI/NO que indica si el Laboratorio compite en la serie (el encabezado del archivo trae un error de ortografía). Es SI en ${f1(D.compite_filas_si, 0)} filas y en ellas está toda la venta del Laboratorio. [[Confirmar la definición de la marca]].`],
  ['Formato', 'CSV con codificación UTF-8 con BOM; números con coma de miles; los crecimientos vienen como fracciones.'],
], [2300, 7060], { boldFirst: true }));
kids.push(CAPT('Tabla 1. Columnas, tipos y faltantes'));
const notas = { 'Precio Leche': 'Solo bovinos (faltante por diseño)', 'Precio Carne Res': 'Solo bovinos (por diseño)', 'Precio carne cerdo': 'Solo cerdos (por diseño)', 'Precio huevo': 'Solo aves (por diseño)', 'Precio Pollo': 'Solo aves (por diseño)',
  'Perros': 'Solo animales de compañía; no se usa en el modelo', 'Gatos': 'Solo animales de compañía; no se usa en el modelo', 'Crec Mercado Q movil': 'Vacío al inicio de cada serie', 'Crec Mercado Año': 'Definición no reconciliable; no se usa',
  'Crec Laboratorio año': 'Vacío antes de que existan 12 meses de venta', 'Compite Laboraorio': 'Se usa para definir el mercado donde compite', 'Venta Laboratorio': 'Cero antes de 2022; incluye devoluciones negativas',
  'Share Laboratorio': 'Puede superar 1 (ver Tabla 2)', 'PIB': 'Un valor por año', 'PIB Agro': 'Un valor por año', 'Porc Crec SMMLV': 'Un valor por año', 'Mercado': `Incluye ${D.mercado_cero} meses con valor cero` };
kids.push(table(['Columna', 'Tipo', 'Faltantes', 'Observación'], C.ficha.map(r => [r.columna, r.tipo, `${f1(r.faltantes, 0)} (${f1(r.pct)}%)`, notas[r.columna] || '']), [2000, 2900, 1400, 3060], { right: [2] }));
kids.push(CAP('Los faltantes de precios y de población son estructurales: cada precio solo aplica a una especie. No son datos perdidos y no se imputaron.'));
kids.push(H2('2.2 Diagnóstico de calidad'));
kids.push(P('Los hallazgos se ordenan por su efecto sobre la validez del modelo. P1 limita la conclusión; P2 exige un tratamiento explícito; P3 es de orden técnico.'));
kids.push(CAPT('Tabla 2. Hallazgos de calidad priorizados'));
kids.push(table(['Prioridad', 'Hallazgo', 'Evidencia', 'Tratamiento'], [
  ['P1', 'Historia corta', `Mercado: ${D.meses} meses (cinco años completos y seis meses de 2026). Variables macro: un valor por año (siete valores distintos de PIB, PIB agro y salario mínimo).`, 'Modelos muy regularizados; validación por bloques de tiempo; límites explícitos en la Sección 6.'],
  ['P1', 'Ventas del Laboratorio desde 2022', `Cero en 2020; solo ${D.lab_filas_con_venta['2021']} registros con venta en 2021; ${D.lab_filas_con_venta['2022']} en 2022. Primer crecimiento de 12 meses disponible: diciembre de 2023.`, 'El modelo del Laboratorio se entrena con 25 meses por especie (100 filas); validación con embargo reducido.'],
  ['P1', 'Venta del Laboratorio mayor que el mercado', `${D.lab_mayor_mercado} filas con venta mayor que el mercado y ${D.share_mayor_1} con participación mayor a 1 (hasta 96 veces), casi todas en cerdos (macrólidos, 2021 a 2023).`, 'Se conservan: el equipo confirmó que el Laboratorio lidera el mercado de cerdos. Posible diferencia de medición entre la venta interna y el sell-in de SIMVET [[confirmar si Zoetis es uno de los 31 laboratorios y si ambas mediciones tienen la misma definición]].'],
  ['P2', 'Mercado y laboratorio hasta junio de 2026', 'El año 2026 solo tiene seis meses.', 'No se completó: el crecimiento se mide con 12 meses móviles, y el de 2027 lo proyecta el modelo con las variables del escenario.'],
  ['P2', 'Meses con mercado en cero', `${f1(D.mercado_cero, 0)} filas (${f1(D.mercado_cero / D.filas * 100)}%).`, 'Se conservan; se agregan a nivel de especie.'],
  ['P2', 'Ventas negativas del Laboratorio', `${D.lab_negativas} filas.`, 'Son devoluciones válidas (confirmado por el equipo); se conservan.'],
  ['P2', 'Caída de aves en 2026', 'Crecimiento de 12 meses de aproximadamente −6% a junio de 2026 en aves.', 'Es real (confirmado). Es el principal desafío del examen.'],
  ['P3', 'Marca "Compite Laboraorio"', `En ${D.compite_series_cambian} series la marca cambia mes a mes y coincide con los meses con venta del Laboratorio.`, 'Se fija una vez por serie con datos de desarrollo (36 series), para no meter la venta propia en la definición del mercado.'],
  ['P3', 'Crecimiento anual de la base', '"Crec Mercado Q movil" coincide con el cálculo propio; "Crec Mercado Año" no coincide con crecimiento interanual, acumulado ni 12 meses móviles.', 'Se recalculan todos los crecimientos; "Crec Mercado Año" no se usa.'],
  ['P3', 'Formatos', 'Números con comas de miles; encabezado con error de ortografía.', 'Conversión al leer el archivo.'],
], [1000, 1800, 3500, 3060]));
kids.push(img('f1_historia.png', 590));
kids.push(CAP('Figura 1. Crecimiento de 12 meses por especie al cierre de cada año y a junio de 2026. Líneas punteadas: umbrales de 8% y 15%.'));
kids.push(H2('2.3 Sesgo y representatividad'));
[
  '**Cobertura de SIMVET.** Mide el sell-in (venta del laboratorio al canal) de los 31 laboratorios que reportan, no el consumo final (sell-out) ni a los laboratorios que no reportan. Como no se ven nombres ni marcas, no se puede comprobar cuánto del mercado total cubre.',
  '**Cobertura por segmento.** Aves solo tiene vacunas y cerdos solo antimicrobianos y vacunas. El "mercado" de esas especies es el de esos segmentos, no el mercado farmacéutico completo. [[Confirmar el criterio de cobertura de la base]].',
  `**Mercado donde compite el Laboratorio.** Pesa entre ${f1(D.pct_mercado_compite.Cattle, 0)}% (bovinos) y ${f1(D.pct_mercado_compite.CA, 0)}% (animales de compañía) del mercado de cada especie, y no crece igual que el total. Por eso se modela como objetivo aparte.`,
  '**Agregado nacional.** Las series y los precios son promedios nacionales. No representan diferencias regionales, tamaño de productor ni canal.',
  '**Efecto del ciclo 2020-2026.** El periodo incluye la recuperación posterior a la pandemia, una inflación de dos dígitos en 2022 y 2023 y shocks sanitarios o de precios. Esas condiciones pueden no repetirse en 2027.',
  '**Crecimiento nominal.** Las ventas están en pesos corrientes. Parte del crecimiento es inflación; por decisión del equipo se modela el crecimiento nominal y se documenta esa dependencia. Los precios entran como cambio real (deflactados por el IPC).',
  '**Posición del Laboratorio.** El Laboratorio lidera el mercado de cerdos (participación de 40% a 50%) y tiene una participación baja en bovinos (alrededor de 4%). El modelo del Laboratorio aprende más de las especies donde pesa más.',
  `**Perros y gatos.** La serie de población viene de Minsalud (2019) proyectada con crecimientos de Euromonitor, es decir, es una estimación. Por decisión del equipo se excluyó del modelo; el efecto del ingreso de los hogares sobre animales de compañía se representa solo con la inflación.`,
].forEach(t => kids.push(B(t)));

// ------------------------------------------------------------------ 3
kids.push(H1('3. Preparación y diseño experimental'));
kids.push(H2('3.1 Unidad de análisis y variables'));
kids.push(P('Cada observación es una especie en un mes t. Hay tres variables objetivo, todas definidas como el crecimiento nominal de la venta acumulada de los 12 meses que terminan en t frente a los 12 meses anteriores: el mercado de la especie, el mercado donde compite el Laboratorio y las ventas del Laboratorio. En t = diciembre de 2027 es el crecimiento anual de 2027, que es lo que se quiere proyectar. Hay 49 meses por especie en el mercado (196 filas) y 25 en el Laboratorio (100 filas).'));
kids.push(P('**Predictores** (con información disponible hasta t): inflación de 12 meses (IPC); PIB, PIB agropecuario y aumento del salario mínimo (promedios de 12 meses); cambio **real** del precio promedio de 12 meses de la leche, la carne de res, la carne de cerdo, el huevo y el pollo (cada uno solo para su especie, cero para las demás); un término propio de inflación para animales de compañía; y la especie en codificación one-hot. El modelo del Laboratorio agrega el crecimiento del mercado de la especie. El cambio real es el nominal descontada la inflación: (1 + nominal) / (1 + inflación) − 1.'));
kids.push(H2('3.2 Sello de los datos y partición antes de cualquier transformación'));
kids.push(P(`Antes de leer ninguna cifra se parte la base por fecha, con un script que solo copia texto: **desarrollo** (hasta diciembre de 2025, ${f1(C.manifiesto.filas_desarrollo, 0)} filas) y **sellado** (enero a junio de 2026, ${f1(C.manifiesto.filas_sellado, 0)} filas). La TRM se parte igual. Cada archivo queda registrado con su huella digital (SHA-256) y todo el desarrollo, desde las variables hasta la selección del modelo, solo lee el archivo de desarrollo. El archivo sellado solo lo abre el script del examen, que deja una línea en un registro de accesos.`));
kids.push(CAPT('Tabla 3. Partición (por mes t de la ventana de 12 meses)'));
kids.push(table(['Conjunto', 'Periodo (mes t)', 'Mercado (filas)', 'Laboratorio (filas)', 'Uso'], [
  ['Entrenamiento', 'Mercado: dic-2021 a dic-2025\nLaboratorio: dic-2023 a dic-2025', f1(TM.seleccion.n_train, 0), f1(TL.seleccion.n_train, 0), 'Validación cruzada, ajuste de hiperparámetros y selección'],
  ['Examen', 'ene-2026 a jun-2026', '24', '24', 'Consulta principal y una consulta complementaria (Sección 3.6)'],
], [1500, 2500, 1300, 1400, 2660]));
kids.push(H2('3.3 Flujo encapsulado en un Pipeline'));
kids.push(P('Toda transformación ajustada vive dentro de un Pipeline de scikit-learn, de modo que se ajusta solo con los datos de entrenamiento de cada pliegue:'));
kids.push(table(['Paso', 'Componente', 'Qué aprende y de dónde'], [
  ['1', 'ColumnTransformer: StandardScaler en las variables continuas; la especie (one-hot) pasa sin escalar', 'Media y desviación de las filas de entrenamiento del pliegue'],
  ['2', 'Ponderación por clase de escenario (opcional)', 'Frecuencias de clase de las filas de entrenamiento del pliegue'],
  ['3', 'Modelo (diez candidatos; Sección 4)', 'Coeficientes, vecinos o árboles con las filas de entrenamiento del pliegue'],
], [800, 5000, 3560]));
kids.push(H2('3.4 Validación cruzada con purga'));
kids.push(P(`La validación cruzada divide el entrenamiento en bloques consecutivos de 6 meses (${TM.seleccion.n_pliegues} pliegues en el mercado y ${TL.seleccion.n_pliegues} en el Laboratorio). Como las ventanas de 12 meses de meses vecinos comparten hasta 11 meses de datos, se elimina del entrenamiento un **embargo** de ${TM.seleccion.embargo} meses a cada lado del bloque evaluado (${TL.seleccion.embargo} en el Laboratorio, cuya historia es más corta). Los pliegues son los mismos para todos los modelos.`));
kids.push(img('f6_embargo.png', 440));
kids.push(CAP(`Figura 2. Error fuera de pliegue del modelo elegido del mercado según el embargo. Sin purga el error parece ${f1(emb(TM, 'embargo 11').MAE_pp - emb(TM, 'embargo 0').MAE_pp)} pp menor que con 11 meses de purga: ese es el optimismo que se evita.`));
kids.push(P(`Como contraste se corrió una validación estratificada por clase con grupos por año en el mercado (${f1(emb(TM, 'estratificada').MAE_pp)} pp, sin purga). En el Laboratorio no es viable: solo hay tres años como grupos. La estratificación no es el diseño principal porque mezclar años distintos en entrenamiento y evaluación repite el problema de solapamiento.`));
kids.push(H2('3.5 Desbalance de clases'));
kids.push(table(['Escenario', `Mercado (n=${TM.seleccion.n_train})`, `Laboratorio (n=${TL.seleccion.n_train})`], ['regular', 'estable', 'optimista'].map((c, i) => [c, `${TM.desbalance[i].n} (${f1(TM.desbalance[i].pct)}%)`, `${TL.desbalance[i].n} (${f1(TL.desbalance[i].pct)}%)`]), [3000, 3180, 3180]));
kids.push(gap());
kids.push(P(`**Tratamiento:** solo en entrenamiento. Se probó ponderar cada muestra por la frecuencia inversa de su clase, calculada dentro de cada pliegue de entrenamiento (no se rellena ni se remuestrea el conjunto de evaluación), tratada como un hiperparámetro más. Con el mejor modelo del mercado, la ponderación cambia el MAE de ${f1(TM.efecto_balance[0].MAE_pp)} a ${f1(TM.efecto_balance[1].MAE_pp)} pp y la detección de "regular" sigue en ${f1(TM.efecto_balance[1].recall_regular * 100, 0)}%: no resuelve el problema. No se usó remuestreo sintético (SMOTE): con 9 observaciones "regular" y filas solapadas en el tiempo, generaría observaciones casi idénticas y una falsa sensación de aprendizaje.`));
kids.push(H2('3.6 Examen: consulta principal y consulta complementaria'));
kids.push(P(`El examen (enero a junio de 2026) se consultó **primero una vez** (${C.locks.principal}), después de registrar en el repositorio la selección de modelos y de verificar el sello. En esa consulta se midieron el modelo elegido por la regla, el de menor error de validación (declarado de antemano como referencia informativa) y los dos métodos sencillos.`));
kids.push(P(`Después se hizo una **consulta complementaria** (${C.locks.complementaria}) para medir K vecinos, Random Forest y la regresión lineal, a pedido del equipo, que quería completar la comparación de modelos. Es una segunda consulta: no se usó para seleccionar nada, pero con cinco modelos mirados sobre el mismo examen, sus resultados son más optimistas que los de un examen sin tocar. Ambas consultas quedan en el registro de accesos (${C.accesos.length} líneas, que incluyen las lecturas posteriores para el reajuste, la proyección y el simulador).`));
kids.push(CALLOUT('**Limitación que debe conocerse.** En una fase exploratoria previa a este protocolo se compararon modelos y se vieron resultados de 2026; la elección de variables y de la línea base se hizo con ese conocimiento. El sello garantiza que el **código** de desarrollo no tocó el examen, pero no borra lo que el equipo ya sabía. La prueba realmente nueva serán los datos de julio a diciembre de 2026.', 'FFF6E0'));
kids.push(H2('3.7 Resumen: cómo se evitaron la fuga, el desbalance y el uso indebido del examen'));
kids.push(table(['Riesgo', 'Qué se hizo', 'Justificación'], [
  ['Fuga por escalamiento', 'El StandardScaler está dentro del Pipeline y se ajusta en cada pliegue con su entrenamiento.', 'Media y desviación calculadas con datos de evaluación filtrarían su información al modelo.'],
  ['Fuga temporal', 'Partición cronológica; variables solo con información hasta t; bloques con embargo de 6 y 3 meses.', `Las ventanas de 12 meses se solapan; sin purga el error se subestima hasta ${f1(emb(TM, 'embargo 11').MAE_pp - emb(TM, 'embargo 0').MAE_pp)} pp (Figura 2).`],
  ['Fuga por lectura de los datos', 'Los datos de 2026 se separan antes de cualquier cálculo. Verificación con un "canario": se reemplazan todas las cifras de 2026 por 999999999 y se repite todo el desarrollo; los 48 archivos de resultados salen idénticos byte a byte.', 'Prueba que el desarrollo no depende de las cifras del examen.'],
  ['Fuga por variables', 'No se usan crecimientos con datos futuros. En el Laboratorio, el crecimiento del mercado entra observado en el entrenamiento y proyectado por el modelo de mercado en el examen.', 'En 2027 solo habrá proyección del mercado.'],
  ['Desbalance', 'Ponderación por clase solo dentro del entrenamiento de cada pliegue, tratada como hiperparámetro; sin remuestreo sintético.', 'Evita modificar la distribución de evaluación y respeta que las clases raras son pocas y correlacionadas en el tiempo.'],
  ['Uso indebido del examen', 'Selección por validación cruzada con criterio declarado de antemano; candado en el script; registro de cada acceso; segunda consulta declarada como informativa.', 'Elegir el modelo con el examen lo convertiría en un conjunto de validación y haría optimista el resultado final.'],
], [1800, 4200, 3360]));
