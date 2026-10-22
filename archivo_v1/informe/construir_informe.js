// Construye informe/Informe_Tecnico_Mercado_Farmaceutico_Salud_Animal_Colombia.docx
// Todas las cifras salen de informe/cifras.json (generado por src/cifras_informe.py).
// Marcado de texto: **negrita**, [[pendiente por confirmar]] (resaltado en amarillo).
const fs = require('fs');
const path = require('path');
const D = require('docx');
const C = JSON.parse(fs.readFileSync(path.join(__dirname, 'cifras.json'), 'utf8'));

const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, AlignmentType,
  HeadingLevel, LevelFormat, ImageRun, Footer, Header, PageNumber, PageBreak } = D;

const f1 = (v, d = 1) => Number(v).toLocaleString('es-CO', { minimumFractionDigits: d, maximumFractionDigits: d });
const pct = (v, d = 1) => f1(v * 100, d) + '%';
const sg = (v, d = 1) => (v >= 0 ? '+' : '−') + f1(Math.abs(v), d);
const INK = '13201C', ACC = '0B5D4F', MUTED = '5E6E69', LINE = 'C9D5D1', HEAD = 'E4EEEB';
const W = 9360; // ancho útil en DXA (Carta, márgenes de 1")

function runs(text, base = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\[\[[^\]]+\]\])/g;
  text.split(re).forEach(t => {
    if (!t) return;
    if (t.startsWith('**')) out.push(new TextRun({ ...base, text: t.slice(2, -2), bold: true }));
    else if (t.startsWith('[[')) out.push(new TextRun({ ...base, text: '[' + t.slice(2, -2) + ']', highlight: 'yellow' }));
    else out.push(new TextRun({ ...base, text: t }));
  });
  return out;
}
const P = (text, o = {}) => new Paragraph({ spacing: { after: 120, line: 276 }, alignment: o.align, keepNext: o.keepNext, children: runs(text, o.run || {}) });
const H1 = (t, brk = false) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: brk, spacing: { before: brk ? 120 : 480, after: 200 }, children: [new TextRun(t)] });
const H1n = t => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const H2 = t => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const B = (text, lvl = 0) => new Paragraph({ numbering: { reference: 'vin', level: lvl }, spacing: { after: 60, line: 264 }, children: runs(text) });
const NUM = (text, ref = 'num') => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 60, line: 264 }, children: runs(text) });
const CAP = t => new Paragraph({ spacing: { before: 60, after: 200 }, children: [new TextRun({ text: t, italics: true, size: 18, color: MUTED })] });
const CAPT = t => new Paragraph({ keepNext: true, spacing: { before: 160, after: 60 }, children: [new TextRun({ text: t, bold: true, size: 19, color: INK })] });
const CALLOUT = (text, fill = 'EEF5F3') => new Paragraph({
  spacing: { before: 80, after: 160, line: 276 }, shading: { type: ShadingType.CLEAR, fill, color: 'auto' },
  border: { left: { style: BorderStyle.SINGLE, size: 24, color: ACC, space: 8 } }, indent: { left: 160, right: 80 }, children: runs(text) });

function cell(text, w, o = {}) {
  const paras = String(text).split('\n').map(t => new Paragraph({ alignment: o.align, spacing: { after: 20 }, children: runs(t, { size: o.size || 18, bold: o.bold, color: o.color }) }));
  return new TableCell({ width: { size: w, type: WidthType.DXA }, verticalAlign: 'center',
    shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 }, children: paras });
}
function table(headers, rows, widths, o = {}) {
  const bd = { style: BorderStyle.SINGLE, size: 4, color: LINE };
  const borders = { top: bd, bottom: bd, left: bd, right: bd, insideHorizontal: bd, insideVertical: bd };
  const al = (j) => (o.right && o.right.includes(j) ? AlignmentType.RIGHT : AlignmentType.LEFT);
  const head = new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((h, j) => cell(h, widths[j], { bold: true, fill: HEAD, align: al(j) })) });
  const body = rows.map(r => new TableRow({ cantSplit: true, children: r.map((c, j) => cell(c, widths[j], { align: al(j), bold: o.boldFirst && j === 0 })) }));
  return new Table({ width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths, borders, rows: [head, ...body] });
}
function img(name, wpx = 600) {
  const buf = fs.readFileSync(path.join(__dirname, 'figuras', name));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  return new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 80, after: 40 },
    children: [new ImageRun({ type: 'png', data: buf, transformation: { width: wpx, height: Math.round(wpx * h / w) }, altText: { title: name, description: name, name } })] });
}
const gap = () => new Paragraph({ spacing: { after: 100 }, children: [] });

// ------------------------------------------------------------------ atajos de datos
const M = C.mercado, L = C.lab, T = C.prueba;
const cvr = (t, m) => C[t].comparacion_cv.find(r => r.modelo === m);
const NOM = { ridge_esp: 'Ridge por especie', ridge: 'Ridge común', enet: 'Elastic Net', rf: 'Random Forest', gbm: 'Gradient Boosting',
  B1_crecimiento_hace_12m: 'Base 1: crecimiento de hace 12 meses', B2_media_especie: 'Base 2: promedio histórico de la especie' };
const ESP = { CA: 'Animales de compañía', Cattle: 'Bovinos', Poultry: 'Aves', Swine: 'Cerdos', Total: 'Total' };
const proy = e => C.proyeccion.find(r => r.Especie === e);
const sens = v => C.sens2027.find(r => r.variable === v);
const emb = (t, s) => C[t].sens_validacion.find(r => r.validacion.includes(s));
const ESC = { regular: 'regular', estable: 'estable', optimista: 'optimista' };
const PR = C.prueba_recalculada, BA = C.banda;
const bmin = t => Math.min(...['CA', 'Cattle', 'Poultry', 'Swine'].map(e => BA[t][e])), bmax = t => Math.max(...['CA', 'Cattle', 'Poultry', 'Swine'].map(e => BA[t][e]));

const kids = [];

// ------------------------------------------------------------------ portada
kids.push(new Paragraph({ spacing: { before: 2400, after: 120 }, children: [new TextRun({ text: 'INFORME TÉCNICO', size: 22, bold: true, color: ACC, characterSpacing: 60 })] }));
kids.push(new Paragraph({ heading: HeadingLevel.TITLE, spacing: { after: 240 }, children: [new TextRun('Informe Técnico de Mercado Farmacéutico de Salud Animal en Colombia')] }));
kids.push(new Paragraph({ spacing: { after: 600 }, children: [new TextRun({ text: 'Proyección del crecimiento 2027 del mercado y del laboratorio, con simulador de escenarios', size: 26, color: MUTED })] }));
kids.push(table(['Campo', 'Detalle'], [
  ['Versión', 'Borrador 1, octubre de 2026'],
  ['Equipo', '[[nombres y cargos del equipo]]'],
  ['Organización', '[[nombre del Laboratorio / área solicitante]]'],
  ['Código y datos', 'github.com/jkcuellarc-del/MercadoFarma, rama claude/nifty-ritchie-baueku'],
  ['Simulador (versión web)', 'claude.ai/artifact/WpUvY3RBuvs6sNJ4LK84mc (privado; ver Sección 6.8)'],
  ['Convención', 'El texto resaltado en amarillo es información que solo el equipo puede confirmar.'],
], [2400, 6960], { boldFirst: true }));

kids.push(new Paragraph({ pageBreakBefore: true, heading: HeadingLevel.HEADING_1, children: [new TextRun('Resumen')] }));
kids.push(P(`El Laboratorio necesita una referencia de cuánto crecerá en 2027 el mercado farmacéutico de salud animal en Colombia y cuánto crecerá su propia venta, por especie (animales de compañía, bovinos, cerdos y aves). Con ventas mensuales de ${C.fecha_min} a ${C.fecha_max} (${f1(C.filas_analisis, 0)} filas, ${C.columnas} columnas) y variables económicas y de precios, se construyó un modelo de regresión regularizada (Ridge por especie) dentro de un Pipeline, con hiperparámetros elegidos por validación cruzada con purga temporal y una única consulta del conjunto de prueba.`));
kids.push(B(`**Proyección base 2027:** mercado total ${pct(proy('Total').crec_mercado)} y laboratorio ${pct(proy('Total').crec_lab)} (nominal). Los márgenes de error típicos son de ±${f1(bmin('mercado'))} a ±${f1(bmax('mercado'))} puntos porcentuales en el mercado y de ±${f1(bmin('lab'))} a ±${f1(bmax('lab'))} en el laboratorio, según la especie.`));
kids.push(B(`**Evidencia:** en validación cruzada el modelo supera las dos líneas base (mercado: ${f1(M.seleccion.MAE_cv_final)} pp frente a ${f1(cvr('mercado', 'B2_media_especie').MAE_cv)} y ${f1(cvr('mercado', 'B1_crecimiento_hace_12m').MAE_cv)}). En la prueba de 2026 el mercado **no mejora** a las líneas base (${f1(T.mercado.MAE_pp)} pp frente a ${f1(T.mercado.B2_media_especie.MAE_pp)} y ${f1(T.mercado.B1_crecimiento_hace_12m.MAE_pp)}), mientras que el laboratorio sí (${f1(T.lab.con_mercado_proyectado.MAE_pp)} pp frente a ${f1(T.lab.B2_media_especie.MAE_pp)} y ${f1(T.lab.B1_crecimiento_hace_12m.MAE_pp)}).`));
kids.push(B('**Límite central:** hay entre cinco y seis años de historia y variables macroeconómicas anuales. El modelo no estima efectos fiables del PIB, la inflación ni los precios. Con la regularización elegida, el crecimiento proyectado se parece al promedio histórico de cada especie con ajustes pequeños.'));
kids.push(B('**Recomendación:** usar la proyección como referencia central con rango, no como compromiso; no usar la alerta de escenario "regular" del modelo como señal operativa; y revalidar el modelo cuando estén los datos de julio a diciembre de 2026.'));

kids.push(new Paragraph({ spacing: { before: 200, after: 80 }, children: [new TextRun({ text: 'Contenido', bold: true, size: 24, color: ACC })] }));
['1. Problema y decisión', '2. Datos', '3. Preparación y diseño experimental', '4. Modelado', '5. Evaluación', '6. Decisión, límites y gobernanza', '7. Roles y trabajo en equipo', 'Anexo A. Fuentes de datos (APA 7)', 'Anexo B. Reproducibilidad']
  .forEach(t => kids.push(new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: t, size: 22 })] })));

// ------------------------------------------------------------------ 1
kids.push(H1('1. Problema y decisión', true));
kids.push(H2('1.1 Contexto'));
kids.push(P('El Laboratorio es una compañía farmacéutica multinacional de salud animal con portafolio en Colombia para cuatro especies: animales de compañía (perros y gatos), bovinos, cerdos y aves. En cada especie participa en segmentos como biológicos y vacunas, antimicrobianos, antiparasitarios, hormonales, analgésicos (pain), productos no farmacéuticos y otros farmacéuticos. La base contiene las ventas mensuales de cada segmento, el mercado total en pesos colombianos (incluidos los segmentos y subgrupos donde el Laboratorio no compite) y la participación del Laboratorio.'));
kids.push(H2('1.2 La decisión organizacional'));
kids.push(CALLOUT('**Decisión:** con qué crecimiento del mercado y de las ventas debe planear el Laboratorio el año 2027, por especie: metas comerciales, presupuesto, producción e inventario (los biológicos tienen vida útil limitada) y prioridades de inversión.'));
kids.push(table(['Pregunta', 'Respuesta'], [
  ['¿Quién decide?', '[[confirmar: p. ej., Gerencia General con Dirección Comercial y Planeación Financiera; nombrar cargo y responsable]]'],
  ['¿Cuándo?', '[[confirmar: fecha del ciclo de planeación 2027]]'],
  ['¿A quién afecta directamente?', 'Equipos comerciales de cada especie (metas y comisiones), cadena de suministro (inventarios), finanzas (presupuesto) y mercadeo (inversión por especie).'],
  ['¿A quién afecta indirectamente?', 'Veterinarios, distribuidores y productores, por la disponibilidad y el precio de los productos; y los animales atendidos, por el acceso a vacunas y tratamientos.'],
  ['¿Qué se hace hoy?', '[[confirmar: método actual de planeación, p. ej., repetir el crecimiento del año anterior o ajuste por juicio de expertos]]. La línea base 1 de este informe reproduce la práctica de repetir el crecimiento de hace 12 meses.'],
], [2600, 6760], { boldFirst: true }));
kids.push(gap());
kids.push(P('La decisión se clasifica con tres escenarios definidos por el negocio: **regular** si el crecimiento es menor a 8%, **estable** si está entre 8% y 15%, y **optimista** si supera 15%.'));
kids.push(H2('1.3 Paradigma elegido y alternativas'));
kids.push(P('Se eligió **aprendizaje supervisado de tipo regresión**: predecir el crecimiento nominal de las ventas de 12 meses móviles (variable continua) a partir de variables económicas y de precios, y derivar el escenario aplicando los umbrales de 8% y 15%. Las alternativas se descartaron por las razones de la tabla.'));
kids.push(table(['Alternativa', 'Por qué no es la principal'], [
  ['Clasificación directa del escenario', `Desperdicia información (un 8,1% y un 14,9% serían iguales) y el desbalance es fuerte: solo ${f1(M.desbalance[0].pct)}% de las observaciones de entrenamiento del mercado son "regular". Se usa como lectura derivada y se evalúa aparte.`],
  ['Series de tiempo clásicas (ARIMA, suavizado exponencial)', 'Proyectan con la propia historia, pero no permiten el objetivo de simular cambios en PIB, inflación, salario mínimo y precios. Se usan solo para completar julio a diciembre de 2026.'],
  ['Aprendizaje no supervisado', 'No hay una variable objetivo que se pueda recuperar; no responde a la pregunta de proyección.'],
  ['Modelos causales o estructurales', 'Requerirían datos de precios y demanda por producto, y diseños que la base no tiene (Sección 6.6).'],
], [3000, 6360], { boldFirst: true }));
kids.push(H2('1.4 Pérdida técnica y métrica de éxito del negocio'));
kids.push(P('El modelo se entrena minimizando un error de predicción, pero el negocio no gana ni pierde por ese error sino por las decisiones que se toman con él. Por eso se separan dos niveles:'));
kids.push(table(['Nivel', 'Métrica', 'Para qué sirve'], [
  ['Pérdida técnica', 'Error absoluto medio (MAE) y raíz del error cuadrático medio (RMSE), en puntos porcentuales de crecimiento.', 'Entrenar, ajustar hiperparámetros y comparar modelos.'],
  ['Métrica de éxito del negocio', 'Costo esperado por error de escenario, con dos reglas: pronosticar un escenario por encima del real cuesta el doble que pronosticarlo por debajo. Complementada con la proporción de escenarios acertados y la capacidad de detectar el escenario "regular".', 'Decidir si el modelo mejora la planeación frente a la práctica actual.'],
], [1900, 4700, 2760], { boldFirst: true }));
kids.push(gap());
kids.push(P('**Supuesto de costos (a validar con el negocio):** sobrestimar el crecimiento lleva a inventario excedente o vencido y a presupuestos y metas inalcanzables; subestimarlo lleva a desabastecimiento y ventas perdidas. Se asumió que lo primero es dos veces más costoso por cada nivel de escenario de diferencia. [[Confirmar la proporción 2:1 y el costo de cada tipo de error con Finanzas o Cadena de Suministro]].'));
kids.push(P('**Criterio de éxito:** el modelo agrega valor solo si supera a las dos líneas base (repetir el crecimiento de hace 12 meses y usar el promedio histórico de la especie) tanto en validación cruzada como en la prueba. [[Confirmar con el negocio el error máximo tolerable, por ejemplo ±5 pp]].'));
kids.push(H2('1.5 Riesgos éticos iniciales'));
[
  '**Presión sobre personas.** Si una proyección puntual se convierte en meta o base de comisiones, los equipos comerciales cargan el error del modelo. Mitigación: usar rangos y no atar compensaciones a una cifra puntual.',
  '**Uso responsable de antimicrobianos.** Proyectar crecimiento del segmento antimicrobiano puede incentivar un empuje comercial que contradiga las prácticas de uso prudente y la resistencia antimicrobiana. Mitigación: tratar el pronóstico como insumo de abastecimiento, no como meta de promoción.',
  '**Confidencialidad y uso autorizado de datos.** La base mezcla ventas internas con datos de mercado de terceros. Debe verificarse la autorización de uso y limitar la difusión del simulador y del repositorio. [[Confirmar la autorización de uso de los datos de mercado]].',
  '**Representatividad.** Las series cubren el agregado nacional y solo algunos segmentos por especie (Sección 2.3). El modelo no describe a pequeños productores, regiones o clínicas específicas.',
  '**Sobreconfianza.** Con cinco años de historia, una cifra con decimales transmite una precisión que el modelo no tiene.',
  '**Transparencia sobre el uso de IA.** El código y el análisis se desarrollaron con apoyo de un asistente de inteligencia artificial; las decisiones de negocio y de tratamiento de datos las tomó el equipo (Sección 7).',
].forEach(t => kids.push(B(t)));

// ------------------------------------------------------------------ 2
kids.push(H1('2. Datos'));
kids.push(H2('2.1 Ficha de datos'));
kids.push(table(['Atributo', 'Descripción'], [
  ['Nombre del conjunto', 'Base Mercado Salud Animal.csv (formato largo: un registro por especie, segmento, subgrupo y mes)'],
  ['Fuente', `Ventas de mercado y del Laboratorio: [[confirmar proveedor y área que entregó la base]]. Variables externas (precios, IPC, PIB, salario mínimo): fuentes públicas del Anexo A. Población de perros y gatos: [[confirmar fuente; no figura en el Anexo A]].`],
  ['Licencia o autorización', '[[confirmar autorización interna para usar las ventas y los datos de mercado de terceros]]. Fuentes públicas: sujetas a los términos de uso de cada entidad (DANE, Fedegán, Porkcolombia, Fenavi).'],
  ['Fecha de acceso', 'El archivo se cargó al repositorio y se analizó el 20 de octubre de 2026. [[confirmar fecha de consulta de cada fuente pública]].'],
  ['Filas y columnas', `${f1(C.filas_brutas, 0)} filas leídas (${C.filas_vacias} vacías al final del archivo) y ${C.columnas} columnas. Filas útiles: ${f1(C.filas_analisis, 0)}.`],
  ['Periodo', `Enero de 2020 a junio de 2026 (${C.fecha_min} a ${C.fecha_max}); 78 meses.`],
  ['Granularidad', `${C.series} series de mercado (especie × segmento × subgrupo), con ${C.subgrupos} nombres de subgrupo.`],
  ['Cobertura por especie', 'Animales de compañía: 6 segmentos. Bovinos: 5. Cerdos: 2 (antimicrobiano y vacunas). Aves: 1 (solo vacunas).'],
  ['Formato', 'CSV con codificación UTF-8 con BOM; números con coma de miles; crecimientos como texto con signo %.'],
], [2300, 7060], { boldFirst: true }));
kids.push(CAPT('Tabla 1. Columnas, tipos y faltantes (sobre las filas útiles)'));
const notas = { 'Precio Leche': 'Solo bovinos (faltante por diseño)', 'Precio Carne Res': 'Solo bovinos (faltante por diseño)', 'Precio carne cerdo': 'Solo cerdos (faltante por diseño)',
  'Precio huevo': 'Solo aves (faltante por diseño)', 'Precio Pollo': 'Solo aves (faltante por diseño)', 'Perros': 'Solo animales de compañía (por diseño); no se usa en el modelo',
  'Gatos': 'Solo animales de compañía (por diseño); no se usa en el modelo', 'Crec Mercado Q movil': 'Vacío al inicio de cada serie', 'Crec Mercado Año': 'Definición no reconciliable; no se usa',
  'Crec Laboratorio año': 'Vacío antes de que existan 12 meses de venta', 'Grupo Empresa': 'Etiqueta ambigua; no se usa', 'Venta Laboratorio': 'Cero antes de 2022; incluye devoluciones negativas',
  'Share Laboratorio': 'Puede superar 1 (ver Tabla 2)', 'PIB': 'Un valor por año', 'PIB Agro': 'Un valor por año', 'Porc Crec SMMLV': 'Un valor por año', 'Mercado': 'Incluye 429 meses con valor cero' };
kids.push(table(['Columna', 'Tipo', 'Faltantes', 'Observación'],
  C.ficha.map(r => [r.columna, r.tipo, `${f1(r.faltantes, 0)} (${f1(r.pct)}%)`, notas[r.columna] || '']), [2100, 2700, 1400, 3160], { right: [2] }));
kids.push(CAP('Los faltantes de precios y de población son estructurales: cada precio solo aplica a una especie. No son datos perdidos y no se imputaron.'));
kids.push(H2('2.2 Diagnóstico de calidad'));
kids.push(P('Los hallazgos se ordenan por su efecto sobre la validez del modelo. P1 limita la conclusión; P2 exige un tratamiento explícito; P3 es de orden técnico.'));
kids.push(CAPT('Tabla 2. Hallazgos de calidad priorizados'));
kids.push(table(['Prioridad', 'Hallazgo', 'Evidencia', 'Tratamiento'], [
  ['P1', 'Historia corta', 'Mercado: 78 meses (cinco años completos y seis meses de 2026). Variables macro: un valor por año (7 valores distintos de PIB, PIB agro y salario mínimo).', 'Modelo muy regularizado; validación con bloques temporales; límites explícitos en la Sección 6.'],
  ['P1', 'Ventas del Laboratorio desde 2022', `Cero en 2020; solo ${C.lab_filas_con_venta['2021']} registros con venta en 2021; ${C.lab_filas_con_venta['2022']} en 2022. Primer crecimiento de 12 meses disponible: diciembre de 2023.`, 'El modelo del laboratorio se entrena con 25 meses por especie (100 filas); CV con embargo reducido.'],
  ['P1', 'Venta del Laboratorio mayor que el mercado', `${C.lab_mayor_mercado} filas con venta mayor que el mercado y ${C.share_mayor_1} con participación mayor a 1 (hasta 96 veces), casi todas en cerdos (macrólidos, 2021 a 2023).`, 'Se conservan: el equipo confirmó que el Laboratorio lidera el mercado de cerdos. Posible cobertura incompleta del mercado en ese subgrupo.'],
  ['P2', '2026 incompleto', 'Datos hasta junio de 2026.', 'Julio a diciembre se completa con un promedio de tres métodos estacionales (error de 1% a 5% en el total del segundo semestre en el mercado y hasta 20% en el laboratorio). No entra al entrenamiento ni a la prueba.'],
  ['P2', 'Meses con mercado en cero', `${f1(C.mercado_cero, 0)} filas (${f1(C.mercado_cero / C.filas_analisis * 100)}%).`, 'Se conservan; se agregan a nivel de especie.'],
  ['P2', 'Ventas negativas del Laboratorio', `${C.lab_negativas} filas.`, 'Son devoluciones válidas (confirmado por el equipo); se conservan.'],
  ['P2', 'Caída de aves en 2026', 'Crecimiento de 12 meses de aproximadamente −6% a junio de 2026 en aves.', 'Es real (confirmado). Es el principal desafío de la prueba.'],
  ['P3', 'Columna "Grupo Empresa" ambigua', `${C.grupo_empresa_valores} valores (mayoría "Other") y ${C.grupo_empresa_nulos} vacíos; mezcla nombres de empresa y de segmento.`, 'No se usa.'],
  ['P3', 'Crecimiento anual de la base', '"Crec Mercado Q movil" coincide al 100% con el cálculo propio; "Crec Mercado Año" no coincide con crecimiento interanual, acumulado del año ni 12 meses móviles.', 'Se recalculan todos los crecimientos; "Crec Mercado Año" no se usa.'],
  ['P3', 'Formatos de texto y filas vacías', 'Números con comas, porcentajes con signo %, 2 filas vacías al final.', 'Conversión al leer el archivo.'],
], [1000, 1800, 3500, 3060]));
kids.push(img('f1_historia.png', 590));
kids.push(CAP('Figura 1. Crecimiento anual nominal por especie, 2021 a 2026 (2026 con julio a diciembre estimado). Líneas punteadas: umbrales de 8% y 15%.'));
kids.push(H2('2.3 Sesgo y representatividad'));
[
  '**Cobertura por segmento.** Aves solo tiene vacunas y cerdos solo antimicrobianos y vacunas. El "mercado" de esas especies es el de esos segmentos, no el mercado farmacéutico completo. La proyección no debe leerse como el mercado total de aves o cerdos. [[Confirmar el criterio de cobertura de la base]].',
  '**Agregado nacional.** Las series y los precios son promedios nacionales. No representan diferencias regionales, tamaño de productor (grande o pequeño) ni canal (clínica, distribuidor, finca).',
  '**Efecto del ciclo 2020-2026.** El periodo incluye la recuperación posterior a la pandemia, una inflación de dos dígitos en 2022 y 2023 y shocks sanitarios o de precios. Esas condiciones pueden no repetirse en 2027.',
  '**Crecimiento nominal.** Las ventas están en pesos corrientes. Parte del crecimiento es inflación; por decisión del equipo se modela el crecimiento nominal y se documenta esa dependencia.',
  '**Sesgo por posición del Laboratorio.** El Laboratorio lidera el mercado de cerdos (participación de 40% a 50%) y tiene una participación baja en bovinos (alrededor de 4%). El modelo del laboratorio aprende mucho más de las especies donde pesa más y puede ser poco confiable donde su peso es bajo.',
  '**Ventas internas frente a mercado de terceros.** Si las fuentes miden cosas distintas (por ejemplo ventas a distribuidor y ventas al usuario final), las participaciones mayores a 1 reflejan esa diferencia. [[Confirmar la definición de cada medición]].',
  '**Perros y gatos.** La población de mascotas existe en la base, pero se excluyó del modelo por decisión del equipo; el efecto del ingreso de los hogares sobre animales de compañía se representa solo con la inflación.',
].forEach(t => kids.push(B(t)));

// ------------------------------------------------------------------ 3
kids.push(H1('3. Preparación y diseño experimental'));
kids.push(H2('3.1 Unidad de análisis y variables'));
kids.push(P('Cada observación es una especie en un mes t. La variable objetivo es el crecimiento nominal de la venta acumulada de los 12 meses que terminan en t frente a los 12 meses anteriores. En t = diciembre de 2027 es el crecimiento anual de 2027, que es lo que se quiere proyectar. Esto produce unas 49 observaciones por especie en el mercado y 25 en el laboratorio.'));
kids.push(P('**Variables explicativas** (todas calculadas con información disponible hasta t): inflación de 12 meses (IPC), PIB, PIB agropecuario y aumento del salario mínimo (promedios de los 12 meses), cambio del precio promedio de 12 meses de la leche, la carne de res, la carne de cerdo, el huevo y el pollo (cada una solo para su especie, cero para las demás), un término propio de inflación para animales de compañía y la especie en codificación one-hot. El modelo del laboratorio agrega el crecimiento del mercado de la especie.'));
kids.push(H2('3.2 Partición antes de cualquier transformación'));
kids.push(P('La partición es temporal y se define sobre el mes t, antes de ajustar cualquier escalador o modelo. Se descarta la partición aleatoria porque mezclaría meses vecinos cuyas ventanas de 12 meses se solapan.'));
kids.push(CAPT('Tabla 3. Partición'));
kids.push(table(['Conjunto', 'Periodo (mes t)', 'Mercado (filas)', 'Laboratorio (filas)', 'Uso'], [
  ['Entrenamiento', 'Mercado: dic-2021 a dic-2025\nLab.: dic-2023 a dic-2025', f1(M.seleccion.n_train, 0), f1(L.seleccion.n_train, 0), 'Validación cruzada, ajuste de hiperparámetros y selección'],
  ['Prueba', 'ene-2026 a jun-2026', '24', '24', 'Una sola evaluación al final'],
  ['Excluido', 'jul-2026 a dic-2026', '24', '24', 'Ventanas con meses completados; no se usa para ajustar ni evaluar'],
], [1500, 2500, 1300, 1400, 2660]));
kids.push(H2('3.3 Flujo encapsulado en un Pipeline'));
kids.push(P('Toda transformación ajustada vive dentro de un Pipeline de scikit-learn, de modo que se ajusta solo con los datos de entrenamiento de cada pliegue:'));
kids.push(table(['Paso', 'Componente', 'Qué aprende y de dónde'], [
  ['1', 'ColumnTransformer: StandardScaler en las variables continuas; la especie (one-hot) pasa sin escalar', 'Media y desviación de las filas de entrenamiento del pliegue'],
  ['2', 'Ponderación por clase de escenario (opcional)', 'Frecuencias de clase de las filas de entrenamiento del pliegue'],
  ['3', 'Modelo (Ridge por especie, Ridge común, Elastic Net, Random Forest o Gradient Boosting)', 'Coeficientes o árboles con las filas de entrenamiento del pliegue'],
], [800, 5000, 3560]));
kids.push(H2('3.4 Validación cruzada con purga'));
kids.push(P(`La validación cruzada divide el entrenamiento en bloques consecutivos de 6 meses (${M.seleccion.n_pliegues} pliegues en el mercado y ${L.seleccion.n_pliegues} en el laboratorio). Como las ventanas de 12 meses de meses vecinos comparten hasta 11 meses de datos, se elimina del entrenamiento un **embargo** de ${M.seleccion.embargo} meses a cada lado del bloque evaluado (${L.seleccion.embargo} en el laboratorio, cuya historia es más corta). Los pliegues son los mismos para todos los modelos.`));
kids.push(img('f6_embargo.png', 440));
kids.push(CAP(`Figura 2. Error fuera de pliegue del modelo final del mercado según el embargo. Sin purga el error parece ${f1(emb('mercado', 'embargo 11').MAE_pp - emb('mercado', 'embargo 0').MAE_pp)} pp menor que con 11 meses de purga: ese es el optimismo que se evita.`));
kids.push(P(`Como verificación adicional, se corrió una validación estratificada por clase con grupos por año en el mercado (${f1(emb('mercado', 'estratificada').MAE_pp)} pp, sin purga). En el laboratorio no es viable: solo hay tres años como grupos. La estratificación se usa como contraste, no como diseño principal, porque mezclar años distintos en entrenamiento y evaluación repite el problema de solapamiento.`));
kids.push(H2('3.5 Desbalance de clases'));
kids.push(P('El desbalance aparece en los escenarios, no en la variable continua:'));
kids.push(table(['Escenario', `Mercado (n=${M.seleccion.n_train})`, `Laboratorio (n=${L.seleccion.n_train})`], [
  ...['regular', 'estable', 'optimista'].map((c, i) => [c, `${M.desbalance[i].n} (${f1(M.desbalance[i].pct)}%)`, `${L.desbalance[i].n} (${f1(L.desbalance[i].pct)}%)`]),
], [3000, 3180, 3180]));
kids.push(gap());
kids.push(P(`**Tratamiento:** solo en entrenamiento. Se probó ponderar cada muestra por la frecuencia inversa de su clase, calculada dentro de cada pliegue de entrenamiento (no se rellena ni se remuestrea el conjunto de evaluación). La ponderación se trató como un hiperparámetro más. Resultado en el mercado: con ponderación el MAE sube de ${f1(M.efecto_balance[0].MAE_pp)} a ${f1(M.efecto_balance[1].MAE_pp)} pp, el acierto de escenario baja de ${pct(M.efecto_balance[0].acierto, 0)} a ${pct(M.efecto_balance[1].acierto, 0)} y la detección de "regular" sigue en ${f1(M.efecto_balance[1].recall_regular * 100, 0)}%. En el laboratorio es indiferente. El modelo final no usa ponderación.`));
kids.push(P('No se usó remuestreo sintético (por ejemplo SMOTE): con 9 observaciones "regular" en el mercado y filas solapadas en el tiempo, generaría observaciones artificiales casi idénticas entre sí y daría una falsa sensación de aprendizaje.'));
kids.push(H2('3.6 Conjunto de prueba: una sola consulta'));
kids.push(P(`La prueba se evaluó una única vez, después de registrar en el repositorio la selección del modelo (commit f30319a). El script bloquea una segunda consulta con un archivo de candado fechado ${C.lock}. Las líneas base y el modelo final se evaluaron en esa misma consulta.`));
kids.push(CALLOUT('**Limitación que debe conocerse.** Antes de este protocolo hubo una fase exploratoria en la que se compararon modelos y se vieron resultados de 2026, y la elección de variables y de la línea base se hizo con ese conocimiento. El protocolo formal aísla la selección del modelo de la prueba, pero la prueba no es completamente "virgen". Los resultados de prueba deben leerse con esa cautela, y la revalidación con julio a diciembre de 2026 será la prueba realmente nueva.', 'FFF6E0'));
kids.push(H2('3.7 Resumen: cómo se evitaron la fuga, el desbalance y el uso indebido de la prueba'));
kids.push(table(['Riesgo', 'Qué se hizo', 'Justificación'], [
  ['Fuga por escalamiento', 'El StandardScaler está dentro del Pipeline y se ajusta en cada pliegue con su entrenamiento.', 'Media y desviación calculadas con datos de evaluación filtrarían su información al modelo.'],
  ['Fuga temporal', 'Partición cronológica; variables solo con información hasta t; bloques con embargo de 6 y 3 meses; meses completados (jul-dic 2026) excluidos del ajuste y la evaluación.', 'Las ventanas de 12 meses se solapan; sin purga el error se subestima hasta 1,3 pp (Figura 2).'],
  ['Fuga por variables', 'No se usan crecimientos calculados con datos futuros. En el laboratorio, el crecimiento del mercado entra observado en el entrenamiento y proyectado en la prueba.', 'En 2027 solo habrá proyección del mercado; evaluar con el valor observado sería optimista.'],
  ['Desbalance', 'Ponderación por clase solo dentro del entrenamiento de cada pliegue, tratada como hiperparámetro; sin remuestreo sintético.', 'Evita modificar la distribución de evaluación y respeta que las clases raras son pocas y correlacionadas en el tiempo.'],
  ['Uso indebido de la prueba', 'Selección por validación cruzada con criterio declarado de antemano; una sola consulta; candado en el script; selección registrada en el repositorio antes de consultar.', 'Elegir el modelo con la prueba la convertiría en un conjunto de validación y haría optimista el resultado final.'],
], [1800, 4200, 3360]));

// ------------------------------------------------------------------ 4
kids.push(H1('4. Modelado'));
kids.push(H2('4.1 Líneas base'));
kids.push(B('**Base 1: crecimiento de hace 12 meses.** Predice que el crecimiento de 12 meses será igual al observado un año antes. Reproduce la práctica de planear con el crecimiento del año anterior.'));
kids.push(B('**Base 2: promedio histórico de la especie.** Predice el crecimiento medio de la especie en el entrenamiento del pliegue. Es el punto de referencia de un modelo que no usa ninguna variable explicativa.'));
kids.push(H2('4.2 Familias de modelos y búsqueda de hiperparámetros'));
kids.push(P('Se compararon cinco modelos de tres familias, con el mismo Pipeline, los mismos pliegues y la misma métrica (MAE), usando búsqueda en rejilla (GridSearchCV) con cada pliegue de la validación cruzada del entrenamiento.'));
kids.push(table(['Familia', 'Modelo', 'Hiperparámetros explorados'], [
  ['Lineal regularizada', 'Ridge por especie (un Ridge por especie)', 'alpha ∈ {0,1; 1; 10; 100; 1.000}'],
  ['Lineal regularizada', 'Ridge común (especie como variable)', 'alpha ∈ {0,1; 1; 10; 100; 1.000}'],
  ['Lineal regularizada', 'Elastic Net', 'alpha ∈ {0,001; 0,01; 0,1}, l1_ratio ∈ {0,2; 0,5; 0,8}'],
  ['Agregación (bagging)', 'Random Forest (300 árboles)', 'profundidad ∈ {2; 3; 5}, hojas mínimas ∈ {3; 5; 10}'],
  ['Refuerzo (boosting)', 'Gradient Boosting (100 árboles)', 'profundidad ∈ {1; 2; 3}, hojas mínimas ∈ {3; 8}'],
  ['Todos', 'Ponderación por clase', '{sí, no}'],
], [2200, 3400, 3760]));
kids.push(H2('4.3 Criterio de selección declarado antes de ejecutar'));
kids.push(NUM('El mejor ajuste de cada modelo se define por el menor MAE medio de validación cruzada.'));
kids.push(NUM('Son elegibles los modelos cuyo MAE medio está a menos de un error estándar del mejor.'));
kids.push(NUM('Entre los elegibles se escoge el de menor complejidad: Ridge por especie, luego Ridge común y Elastic Net, luego Random Forest y por último Gradient Boosting. El simulador necesita efectos propios por especie y una respuesta suave.'));
kids.push(NUM('El modelo elegido debe superar las dos líneas base en validación cruzada. Si no lo hace, se declara que no agrega valor.'));
kids.push(P('La prueba de 2026 no interviene en ninguno de estos pasos.'));
kids.push(H2('4.4 Resultados de validación cruzada'));
const cvRows = (t) => ['ridge_esp', 'ridge', 'enet', 'rf', 'gbm', 'B2_media_especie', 'B1_crecimiento_hace_12m'].map(m => {
  const r = cvr(t, m), s = C[t].seleccion.mejores[m];
  return [NOM[m], `${f1(r.MAE_cv)} ± ${f1(r.sd)}`, s ? `${JSON.stringify(s.params).replace(/[{}"]/g, '').replace(/:/g, ' = ').replace(/,/g, '; ').replace(/(\d)\.(\d)/g, '$1,$2')}${s.balance ? '; con ponderación' : ''}` : '–'];
});
kids.push(CAPT(`Tabla 4. MAE de validación cruzada, mercado (${M.seleccion.n_pliegues} pliegues; media ± desviación entre pliegues)`));
kids.push(table(['Modelo', 'MAE (pp)', 'Mejores hiperparámetros'], cvRows('mercado'), [3300, 1700, 4360], { right: [1] }));
kids.push(CAPT(`Tabla 5. MAE de validación cruzada, laboratorio (${L.seleccion.n_pliegues} pliegues)`));
kids.push(table(['Modelo', 'MAE (pp)', 'Mejores hiperparámetros'], cvRows('lab'), [3300, 1700, 4360], { right: [1] }));
kids.push(CAP('La base 1 solo puede evaluarse donde existe el crecimiento de hace 12 meses. En esas mismas filas, el MAE del mercado es de ' + f1(M.seleccion.base_B1) + ' pp para la base 1 y de ' + f1(cvr('mercado', 'ridge_esp').MAE_oof_subconjunto_lag) + ' pp para el modelo final.'));
kids.push(img('f2_cv.png', 600));
kids.push(CAP('Figura 3. MAE de validación cruzada por modelo. Las barras de error son la desviación estándar entre pliegues.'));
kids.push(H2('4.5 Modelo final y lectura honesta de los resultados'));
kids.push(CALLOUT(`**Modelo final: Ridge por especie.** Mercado: alpha = ${M.seleccion.params.alpha}, sin ponderación. Laboratorio: alpha = ${L.seleccion.params.alpha}, sin ponderación. En ambos casos los cinco modelos quedaron dentro de un error estándar del mejor, por lo que la regla de menor complejidad eligió el Ridge por especie.`));
kids.push(B(`**Las diferencias entre modelos no son concluyentes.** En el mercado el mejor MAE medio es ${f1(cvr('mercado', 'ridge').MAE_cv)} pp (Ridge común) y el elegido tiene ${f1(cvr('mercado', 'ridge_esp').MAE_cv)} pp; la desviación entre pliegues es de 1,3 a 1,9 pp, mayor que esas diferencias.`));
kids.push(B(`**El mercado casi no mejora al promedio por especie.** El modelo final tiene ${f1(cvr('mercado', 'ridge_esp').MAE_cv)} pp frente a ${f1(cvr('mercado', 'B2_media_especie').MAE_cv)} pp de la base 2. Con alpha = ${M.seleccion.params.alpha}, el extremo superior de la rejilla, el modelo se acerca al promedio de cada especie con ajustes pequeños. Esto es coherente con la poca historia y se discute en la Sección 5.4.`));
kids.push(B(`**En el laboratorio la mejora es mayor.** ${f1(cvr('lab', 'ridge_esp').MAE_cv)} pp frente a ${f1(cvr('lab', 'B2_media_especie').MAE_cv)} pp (base 2) y ${f1(cvr('lab', 'B1_crecimiento_hace_12m').MAE_cv)} pp (base 1).`));
kids.push(B('**Los modelos de árboles no fueron mejores** pese a poder capturar relaciones no lineales, y su respuesta a cambios en las variables es a saltos. Se mantuvieron como comparación.'));

// ------------------------------------------------------------------ 5
kids.push(H1('5. Evaluación'));
kids.push(H2('5.1 Métricas según el costo del error'));
kids.push(table(['Métrica', 'Qué mide', 'Por qué se eligió'], [
  ['MAE (pp)', 'Error medio absoluto del crecimiento, en puntos porcentuales.', 'Costo lineal en la distancia al valor real y fácil de explicar al negocio. Principal métrica técnica.'],
  ['RMSE (pp) y sesgo (pp)', 'Penaliza errores grandes; el sesgo indica si el modelo sobrestima (positivo) o subestima.', 'Un sesgo positivo sostenido es el error más costoso en el supuesto de costos.'],
  ['Costo medio por escenario', 'Costo promedio del escenario asignado: 2 por nivel de sobrestimación y 1 por nivel de subestimación.', 'Es la métrica de éxito del negocio (Sección 1.4).'],
  ['Acierto y F1 macro de escenario', 'Proporción de escenarios correctos y promedio del F1 por clase.', 'El acierto solo engaña con clases raras; el F1 macro da el mismo peso a cada escenario.'],
  ['Recall de "regular"', 'De los casos realmente "regulares", cuántos detecta el modelo.', 'Es el escenario más costoso de no ver: llega con meta e inventario que no se vende.'],
], [2300, 3600, 3460], { boldFirst: true }));
kids.push(H2('5.2 Estabilidad de la validación cruzada'));
const fo = (t) => C[t].seleccion.mejores[C[t].seleccion.final].folds;
kids.push(P(`El MAE del modelo final en el mercado va de ${f1(Math.min(...fo('mercado')))} a ${f1(Math.max(...fo('mercado')))} pp entre los ${M.seleccion.n_pliegues} pliegues (media ${f1(M.seleccion.MAE_cv_final)}, desviación ${f1(M.seleccion.sd_cv_final)}). En el laboratorio va de ${f1(Math.min(...fo('lab')))} a ${f1(Math.max(...fo('lab')))} pp entre ${L.seleccion.n_pliegues} pliegues (media ${f1(L.seleccion.MAE_cv_final)}, desviación ${f1(L.seleccion.sd_cv_final)}). La variabilidad es alta frente al tamaño de las mejoras sobre las líneas base.`));
kids.push(CAPT('Tabla 6. Error fuera de pliegue por especie del modelo final (MAE en pp, media y desviación)'));
kids.push(table(['Especie', 'Mercado', 'Laboratorio'], ['CA', 'Cattle', 'Poultry', 'Swine'].map(e => {
  const a = M.oof_especie.find(r => r.Especie === e), b = L.oof_especie.find(r => r.Especie === e);
  return [ESP[e], `${f1(a['mean'])} ± ${f1(a['std'])}`, `${f1(b['mean'])} ± ${f1(b['std'])}`];
}), [3360, 3000, 3000], { right: [1, 2] }));
kids.push(gap());
kids.push(H2('5.3 Umbral de decisión recomendado'));
kids.push(P('Los umbrales de escenario (8% y 15%) son del negocio y no se modifican. Lo que sí se puede ajustar es cuánta prudencia se aplica antes de clasificar: se resta un descuento m a la predicción y luego se aplican los umbrales. El valor de m se eligió con las predicciones fuera de pliegue para minimizar el costo esperado.'));
kids.push(img('f4_umbral.png', 560));
kids.push(CAP('Figura 4. Costo medio por observación según el descuento de prudencia m (predicciones fuera de pliegue del entrenamiento).'));
const um = (t, m) => C[t].umbral.reduce((a, r) => Math.abs(r.m_pp - m) < Math.abs(a.m_pp - m) ? r : a);
kids.push(table(['', 'Mercado', 'Laboratorio'], [
  ['m recomendado por validación cruzada', `${sg(M.seleccion.m_umbral * 100)} pp`, `${sg(L.seleccion.m_umbral * 100)} pp`],
  ['Costo medio con m = 0', f1(um('mercado', 0).costo_medio, 2), f1(um('lab', 0).costo_medio, 2)],
  ['Costo medio con el m recomendado', f1(um('mercado', M.seleccion.m_umbral * 100).costo_medio, 2), f1(um('lab', L.seleccion.m_umbral * 100).costo_medio, 2)],
  ['Detección de "regular" con m = 0', pct(um('mercado', 0).recall_regular || 0, 0), pct(um('lab', 0).recall_regular || 0, 0)],
  ['Detección de "regular" con el m recomendado', pct(um('mercado', M.seleccion.m_umbral * 100).recall_regular || 0, 0), pct(um('lab', L.seleccion.m_umbral * 100).recall_regular || 0, 0)],
], [4500, 2430, 2430], { right: [1, 2], boldFirst: true }));
kids.push(gap());
kids.push(P(`**Recomendación sobre el umbral.** La mejora esperada por m es pequeña en el mercado (${f1(um('mercado', 0).costo_medio, 2)} a ${f1(um('mercado', M.seleccion.m_umbral * 100).costo_medio, 2)}), y en el mercado el modelo no detecta ningún caso "regular" con ningún m razonable. En la prueba (Sección 5.5) el m del laboratorio resultó perjudicial: el acierto bajó de ${pct(PR.lab.modelo_m0.acierto, 0)} a ${pct(PR.lab.modelo_mstar.acierto, 0)} y el costo subió de ${f1(PR.lab.modelo_m0.costo, 2)} a ${f1(PR.lab.modelo_mstar.costo, 2)}. Por eso **no se recomienda adoptar un descuento de prudencia por ahora**: se mantienen los umbrales de 8% y 15% y se muestra siempre el margen de error junto a cada escenario. El valor de m debe recalcularse con los datos de julio a diciembre de 2026. Esta recomendación se apoya en la prueba solo como advertencia; no se usó para modificar el protocolo.`));
kids.push(H2('5.4 Diagnóstico de sesgo y varianza'));
kids.push(img('f3_aprendizaje.png', 560));
kids.push(CAP('Figura 5. Curvas de aprendizaje del modelo final: error en los meses de entrenamiento y en meses retenidos, según la cantidad de meses usados para entrenar.'));
const lcm = M.curva_aprendizaje, lcl = L.curva_aprendizaje;
const rg = (t, a) => C[t].curva_regularizacion.find(r => r.alpha === a);
kids.push(B(`**Varianza alta en el mercado.** Con 36 meses de entrenamiento el error en entrenamiento es ${f1(lcm[lcm.length - 1].MAE_entrenamiento)} pp y en meses retenidos ${f1(lcm[lcm.length - 1].MAE_retenido)} pp. La brecha de ${f1(lcm[lcm.length - 1].MAE_retenido - lcm[lcm.length - 1].MAE_entrenamiento)} pp persiste y el error retenido sigue bajando al agregar meses: más datos ayudarían.`));
kids.push(B(`**La regularización compensa la varianza a costa de sesgo.** Con alpha = 0,1 el mercado tiene ${f1(rg('mercado', 0.1).MAE_entrenamiento)} pp en entrenamiento y ${f1(rg('mercado', 0.1).MAE_cv)} pp en validación cruzada (sobreajuste); con alpha = 1.000 ${f1(rg('mercado', 1000).MAE_entrenamiento)} y ${f1(rg('mercado', 1000).MAE_cv)} pp. El modelo final renuncia a ajustar la historia para no memorizarla.`));
kids.push(B(`**Laboratorio.** Entrenamiento ${f1(lcl[lcl.length - 1].MAE_entrenamiento)} pp y meses retenidos ${f1(lcl[lcl.length - 1].MAE_retenido)} pp con 16 meses de entrenamiento; la curva no se estabiliza con tan pocos meses, así que el diagnóstico es menos confiable.`));
kids.push(B(`**Sesgo estructural.** Un error de ${f1(lcm[lcm.length - 1].MAE_entrenamiento)} pp en entrenamiento muestra que el modelo no captura toda la variación. La caída de aves en 2026 queda fuera de lo que las variables explican.`));
kids.push(H2('5.5 Resultados en la prueba (consulta única, enero a junio de 2026)'));
const tm = T.mercado, tl = T.lab;
kids.push(table(['Métrica', 'Mercado: modelo', 'Mercado: base 2', 'Mercado: base 1', 'Lab.: modelo', 'Lab.: base 2', 'Lab.: base 1'], [
  ['MAE (pp)', f1(tm.MAE_pp), f1(tm.B2_media_especie.MAE_pp), f1(tm.B1_crecimiento_hace_12m.MAE_pp), f1(tl.con_mercado_proyectado.MAE_pp), f1(tl.B2_media_especie.MAE_pp), f1(tl.B1_crecimiento_hace_12m.MAE_pp)],
  ['RMSE (pp)', f1(tm.RMSE_pp), f1(tm.B2_media_especie.RMSE_pp), f1(tm.B1_crecimiento_hace_12m.RMSE_pp), f1(tl.con_mercado_proyectado.RMSE_pp), f1(tl.B2_media_especie.RMSE_pp), f1(tl.B1_crecimiento_hace_12m.RMSE_pp)],
  ['Sesgo (pp)', sg(tm.sesgo_pp), sg(tm.B2_media_especie.sesgo_pp), sg(tm.B1_crecimiento_hace_12m.sesgo_pp), sg(tl.con_mercado_proyectado.sesgo_pp), sg(tl.B2_media_especie.sesgo_pp), sg(tl.B1_crecimiento_hace_12m.sesgo_pp)],
  ['Acierto de escenario*', pct(PR.mercado.modelo_m0.acierto, 0), pct(PR.mercado.B2_m0.acierto, 0), '–', pct(PR.lab.modelo_m0.acierto, 0), pct(PR.lab.B2_m0.acierto, 0), '–'],
  ['Costo medio*', f1(PR.mercado.modelo_m0.costo, 2), f1(PR.mercado.B2_m0.costo, 2), '–', f1(PR.lab.modelo_m0.costo, 2), f1(PR.lab.B2_m0.costo, 2), '–'],
], [1900, 1250, 1250, 1250, 1250, 1230, 1230], { right: [1, 2, 3, 4, 5, 6], boldFirst: true }));
kids.push(CAP(`*Escenario asignado sin descuento de prudencia (m = 0). Laboratorio evaluado con el crecimiento del mercado proyectado por el modelo de mercado (no el observado). n = 24 por tarea (6 meses × 4 especies), con ventanas solapadas: el número efectivo de observaciones independientes es mucho menor. Con el descuento m recomendado por validación el laboratorio obtuvo acierto de ${pct(PR.lab.modelo_mstar.acierto, 0)} y costo ${f1(PR.lab.modelo_mstar.costo, 2)}.`));
kids.push(img('f5_prueba.png', 600));
kids.push(CAP('Figura 6. Crecimiento de 12 meses real y predicho en la prueba, por especie y tarea. Líneas punteadas grises: umbrales de 8% y 15%.'));
const pe = t => ['CA', 'Cattle', 'Poultry', 'Swine'].map(e => `${ESP[e]} ${f1(PR[t].por_especie[e])}`).join('; ');
kids.push(B(`**Mercado.** El modelo (${f1(tm.MAE_pp)} pp) no mejora a las líneas base (${f1(tm.B2_media_especie.MAE_pp)} y ${f1(tm.B1_crecimiento_hace_12m.MAE_pp)} pp), y el error es casi el doble del de validación cruzada (${f1(M.seleccion.MAE_cv_final)} pp). Por especie: ${pe('mercado')} pp. Aves explica la mayor parte: el modelo predice crecimiento positivo y el mercado cayó. La predicción es casi plana, mientras que la realidad de 2026 cambió de tendencia dentro del semestre.`));
kids.push(B(`**Detección de escenarios.** En el mercado, el modelo y la base 2 dan exactamente la misma clasificación: ${pct(PR.mercado.modelo_m0.acierto, 0)} de aciertos y ninguno de los ${PR.mercado.modelo_m0.n_regular} casos "regular" detectado (seis de ellos son aves). El modelo no debe usarse como alarma de bajo crecimiento.`));
kids.push(B(`**Laboratorio.** El modelo (${f1(tl.con_mercado_proyectado.MAE_pp)} pp) mejora a las dos bases en MAE (${f1(tl.B2_media_especie.MAE_pp)} y ${f1(tl.B1_crecimiento_hace_12m.MAE_pp)} pp), con sesgo positivo de ${f1(tl.con_mercado_proyectado.sesgo_pp)} pp. La mejora sobre la base 2 es pequeña (${f1(tl.B2_media_especie.MAE_pp - tl.con_mercado_proyectado.MAE_pp)} pp) y en la clasificación de escenarios empata con ella (acierto ${pct(PR.lab.modelo_m0.acierto, 0)}, costo ${f1(PR.lab.modelo_m0.costo, 2)}); solo la mejora sobre la base 1 es clara. Error por especie: ${pe('lab')} pp.`));
kids.push(B(`**Usar el mercado proyectado en lugar del observado casi no cambia el resultado del laboratorio** (${f1(tl.con_mercado_proyectado.MAE_pp)} pp frente a ${f1(tl.MAE_pp)} pp), lo que indica que el modelo del laboratorio depende poco del crecimiento del mercado.`));

// ------------------------------------------------------------------ 6
kids.push(H1('6. Decisión, límites y gobernanza'));
kids.push(H2('6.1 Recomendación'));
kids.push(CALLOUT(`**Recomendación para quien decide:** usar la proyección 2027 como **referencia central con rango** para el presupuesto y la planeación de inventarios, y no como meta ni como base de compensación. Probar el plan en un rango de ±${f1(BA.mercado.Total, 0)} pp alrededor de la proyección del mercado y de ±${f1(BA.lab.Total, 0)} pp alrededor de la del laboratorio (margen típico de error). No fijar metas por especie con los números sin revisarlos con el equipo comercial, sobre todo en bovinos.`));
kids.push(NUM('**Aprobar el uso como insumo, no como compromiso.** El modelo mejora a las prácticas simples en el laboratorio (sobre todo frente a repetir el crecimiento del año anterior) y las iguala en el mercado.', 'num2'));
kids.push(NUM('**No actuar sobre la alerta de escenario "regular".** El modelo no la detecta en el mercado (0 de 7 casos en la prueba y 0 de 9 en validación cruzada).', 'num2'));
kids.push(NUM('**Revalidar en el primer trimestre de 2027** con los datos reales de julio a diciembre de 2026, que son la prueba verdaderamente nueva, y recalcular el descuento de prudencia.', 'num2'));
kids.push(NUM('**Alimentar el simulador con pronósticos oficiales** de inflación, PIB y salario mínimo 2027 y actualizarlos cuando cambien.', 'num2'));
kids.push(NUM('**Reunir más historia y más variables** (precios por producto, canales, eventos sanitarios) antes de pedirle al modelo efectos causales.', 'num2'));
kids.push(H2('6.2 Proyección 2027, escenario base'));
kids.push(P('Valores base de 2027: inflación 5,1% (mediana de la encuesta de analistas del Banco de la República para diciembre de 2027; el equipo técnico del Banco proyecta 4,3% y el Gobierno 4,8%), PIB 2,3% (BBVA Research; consenso de analistas entre 1,8% y 2,6%), PIB agropecuario 2,7% y salario mínimo 11,9% (promedios históricos, sin pronóstico público), y precios en su nivel de junio de 2026 durante todo 2027. Las cifras de inflación y PIB provienen de reportes de prensa y de análisis; no pudieron verificarse en las páginas oficiales del DANE ni de Porkcolombia desde el entorno de trabajo. [[Confirmar contra fuentes oficiales]].'));
kids.push(CAPT('Tabla 7. Crecimiento nominal proyectado 2027 (modelo final, escenario base)'));
kids.push(table(['Especie', 'Mercado', 'Escenario', 'Laboratorio', 'Escenario', 'Error típico mercado / lab. (pp)'],
  ['CA', 'Cattle', 'Poultry', 'Swine', 'Total'].map(e => { const r = proy(e); return [ESP[e], pct(r.crec_mercado), r.escenario_mercado, pct(r.crec_lab), r.escenario_lab, `±${f1(BA.mercado[e])} / ±${f1(BA.lab[e])}`];
  }), [2100, 1200, 1300, 1300, 1300, 2160], { right: [1, 3], boldFirst: true }));
kids.push(CAP(`El error típico es el promedio del MAE fuera de pliegue (entrenamiento) y del MAE de prueba por especie; el del total es un promedio ponderado por ventas de 2026. El total del mercado (${pct(proy('Total').crec_mercado)}) y aves (${pct(proy('Poultry').crec_mercado)}) están cerca de un umbral: el margen de error cubre más de un escenario.`));
kids.push(H2('6.3 Condiciones que invalidan la recomendación'));
kids.push(table(['Condición', 'Señal de alerta', 'Acción'], [
  ['Error de seguimiento alto', 'MAE trimestral del crecimiento real frente al proyectado mayor a 8 pp en el mercado o 6 pp en el laboratorio.', 'Detener el uso del simulador y reentrenar.'],
  ['Cambio de régimen', 'Inflación, PIB o precios fuera del rango visto en 2021-2026 (el simulador lo advierte).', 'Tratar el resultado como extrapolación.'],
  ['Evento sanitario o regulatorio', 'Brotes (por ejemplo influenza aviar, Newcastle, fiebre aftosa, peste porcina), cambios de registro o de política de antimicrobianos.', 'Reemplazar la proyección por escenarios específicos de la especie.'],
  ['Cambios de portafolio o competencia', 'Lanzamientos, descontinuaciones o entrada de competidores relevantes.', 'Ajustar la proyección del laboratorio con juicio experto.'],
  ['Cambio de la fuente', 'Cambio metodológico en las series de ventas, mercado o precios.', 'Revalidar la serie completa.'],
  ['Cierre real de 2026 distinto al completado', 'Crecimiento 2026 observado con diferencia mayor a 3 pp frente al estimado.', 'Recalcular la base de 2027.'],
], [2300, 4200, 2860], { boldFirst: true }));
kids.push(H2('6.4 Límites del modelo'));
[
  `**Poca historia:** ${M.seleccion.n_train} observaciones de entrenamiento en el mercado y ${L.seleccion.n_train} en el laboratorio, con ventanas solapadas.`,
  `**Poca sensibilidad a las variables.** En el escenario base, subir 1 punto el PIB cambia el crecimiento total del mercado en ${sg(sens('pib').d_mercado_pp, 2)} pp y subir 1 punto la inflación en ${sg(sens('ipc_yoy').d_mercado_pp, 2)} pp; un aumento de 10% en el precio de la carne de res, en ${sg(sens('var_res').d_mercado_pp, 2)} pp. Son efectos mucho menores que el error del modelo: **el simulador no puede cuantificar con confianza qué pasa al mover esas variables.** Para el laboratorio, el efecto mayor es el precio del cerdo (${sg(sens('var_cerdo').d_lab_pp, 2)} pp por +10%), también menor al error.`,
  '**Sin capacidad de detectar escenarios bajos.** No identifica el escenario "regular" en el mercado.',
  '**Crecimiento nominal.** Incluye inflación; una inflación más alta tiende a subir el crecimiento nominal por el efecto de precios, no por mayor demanda.',
  '**Bovinos en el laboratorio.** La proyección de 2027 (4,2%) contrasta con 14% en 2026 y con la historia de 1% a 14%; requiere revisión del equipo comercial.',
  '**Supuestos de 2027.** La proyección depende de pronósticos de terceros y de supuestos propios (PIB agropecuario, salario mínimo y precios constantes).',
].forEach(t => kids.push(B(t)));
kids.push(H2('6.5 A quiénes podría perjudicar'));
[
  '**Equipos comerciales:** metas basadas en una cifra puntual pueden penalizar a quienes no la alcancen por razones ajenas.',
  '**Especies pequeñas o de baja participación del Laboratorio (bovinos, aves):** proyecciones de menor calidad pueden llevar a subinvertir o a sobrestockear.',
  '**Productores y clínicas:** el desabastecimiento por subestimación afecta la salud de animales y la producción; el exceso de inventario puede presionar los precios o los descuentos.',
  '**Uso prudente de antimicrobianos:** una meta de crecimiento en ese segmento choca con políticas de reducción de uso.',
  '**Quien lea el simulador sin contexto:** puede interpretar un efecto causal donde solo hay asociación (Sección 6.6).',
].forEach(t => kids.push(B(t)));
kids.push(H2('6.6 Correlación y causalidad'));
kids.push(P('Los coeficientes del modelo describen asociaciones entre series de pocos años; no demuestran que cambiar una variable cause el cambio en el crecimiento. Tres ejemplos:'));
kids.push(B('**Inflación y animales de compañía.** El equipo planteó que con más inflación los hogares priorizan gastos esenciales sobre la salud de la mascota. En la base, el crecimiento nominal de animales de compañía se mueve junto con la inflación (correlación de 0,43), porque las ventas están en pesos corrientes. Al descontar la inflación, la correlación es de 0,04: no hay evidencia a favor ni en contra de la hipótesis. Probarla exigiría datos de unidades vendidas o de ingresos de los hogares.'));
kids.push(B('**Precio de la carne de cerdo y ventas de cerdos.** La caída del precio en 2026 coincide con un cambio en las ventas, pero ambas pudieron responder a la oferta, a la demanda o a un tercer factor.'));
kids.push(B('**Simulador como "qué pasaría si".** Cambiar un control muestra cómo responde el modelo, no qué pasaría en el mercado si esa variable cambiara. Para efectos causales harían falta experimentos o variaciones exógenas (por ejemplo, cambios de política) y datos más finos.'));
kids.push(H2('6.7 Plan de seguimiento'));
kids.push(table(['Indicador', 'Frecuencia', 'Umbral de alerta', 'Responsable'], [
  ['MAE del crecimiento de 12 meses real frente al proyectado, por especie', 'Mensual', '> 8 pp mercado; > 6 pp laboratorio', '[[confirmar]]'],
  ['Sesgo (proyectado menos real)', 'Trimestral', 'Mayor a ±3 pp durante dos trimestres', '[[confirmar]]'],
  ['Variables del simulador frente al rango de entrenamiento', 'Cada uso', 'Cualquier variable fuera de rango', '[[confirmar]]'],
  ['Disponibilidad de pronósticos oficiales 2027', 'Trimestral', 'Cambio de más de 1 pp en inflación o PIB', '[[confirmar]]'],
  ['Reentrenamiento y revalidación', 'Primer trimestre de 2027 y luego semestral', 'Nueva consulta de prueba sobre el semestre nuevo', '[[confirmar]]'],
  ['Eventos sanitarios y de portafolio', 'Continuo', 'Cualquier evento relevante', '[[confirmar]]'],
], [3700, 1500, 2700, 1460]));
kids.push(H2('6.8 Estado del simulador'));
kids.push(CALLOUT(`**Pendiente de decisión del equipo.** El simulador publicado (versión web) se construyó con una versión anterior del modelo (alpha 100 en el mercado y 50 en el laboratorio, elegida en una fase exploratoria). El modelo final de este informe usa alpha ${f1(M.seleccion.params.alpha, 0)} y ${f1(L.seleccion.params.alpha, 0)}, y es aún menos sensible a las variables. Para que informe y simulador coincidan hay que regenerar el simulador con el modelo final. Con el modelo final los resultados base son mercado ${pct(proy('Total').crec_mercado)} y laboratorio ${pct(proy('Total').crec_lab)}; con el publicado son 15,7% y 21,5%.`, 'FFF6E0'));

// ------------------------------------------------------------------ 7
kids.push(H1('7. Roles y trabajo en equipo'));
kids.push(P('Esta sección debe ser completada por el equipo: los aportes de cada persona no constan en el repositorio. La tabla propone una estructura y borradores a partir del trabajo registrado en el proyecto.'));
kids.push(table(['Perfil', 'Persona(s)', 'Aportes (borrador por ajustar)'], [
  ['Cracks (perfil técnico y analítico)', '[[nombres]]', 'Preparación y limpieza de la base; diseño de variables de 12 meses móviles; modelado, validación cruzada y diagnóstico; construcción del simulador; documentación y repositorio. El código y el análisis se desarrollaron con apoyo de un asistente de IA (Claude, de Anthropic), bajo revisión del equipo.'],
  ['Líderes (coordinación del proyecto)', '[[nombres]]', 'Definición del problema y de los escenarios (regular, estable, optimista); decisión sobre el tratamiento de devoluciones, aves y la participación en cerdos; modelar crecimiento nominal; omitir perros y gatos; dejar solo lo que dicen los datos en la hipótesis de inflación y animales de compañía; compilación de las fuentes de datos.'],
  ['Jefes y jefas (patrocinio y decisión)', '[[nombres]]', '[[Definir: quién usa la proyección para decidir, validación de costos del error y de la proporción 2:1, autorización de datos, aprobación del uso del simulador y de su difusión]].'],
], [2300, 1700, 5360], { boldFirst: true }));
kids.push(gap());
kids.push(P('Las decisiones de negocio y de tratamiento de datos mencionadas en este informe (devoluciones válidas, aves, participación en cerdos, crecimiento nominal, completado de 2026 con modelo estacional, precios constantes en el segundo semestre de 2026, exclusión de perros y gatos, y los valores base de 2027) las tomó el equipo; el asistente de IA propuso, ejecutó y documentó.'));

// ------------------------------------------------------------------ Anexo A
kids.push(H1('Anexo A. Fuentes de datos (APA 7)', true));
kids.push(P('Las series externas cubren de 2020 a 2026. La fecha de consulta de cada fuente debe completarse porque el contenido de estas páginas se actualiza (APA 7 pide la fecha de recuperación en ese caso).'));
const ref = (parts) => new Paragraph({ spacing: { after: 140, line: 264 }, indent: { left: 720, hanging: 720 }, children: parts });
const R = (author, year, title, desc, site, url) => ref([
  ...runs(`${author.trim()} (${year}). `), new TextRun({ text: title, italics: true }), ...runs(` ${desc} ${site} Recuperado el [[día]] de [[mes]] de [[año]], de `), new TextRun({ text: url, color: '1F5FA8' })]);
kids.push(R('Departamento Administrativo Nacional de Estadística. ', 's. f.-a', 'Boletín mensual: Precios de leche cruda en finca', '[Series históricas, 2020-2026].', 'Sistema de Información de Precios y Abastecimiento del Sector Agropecuario (SIPSA).', 'https://www.dane.gov.co/index.php/estadisticas-por-tema/agropecuario/sistema-de-informacion-de-precios-sipsa/boletin-mensual-precios-de-leche-cruda-en-finca'));
kids.push(R('Departamento Administrativo Nacional de Estadística. ', 's. f.-b', 'Índice de precios al consumidor (IPC): Información técnica', '[Variación mensual del IPC por ciudades, 2020-2026].', 'DANE.', 'https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-precios-al-consumidor-ipc/ipc-informacion-tecnica'));
kids.push(R('Departamento Administrativo Nacional de Estadística. ', 's. f.-c', 'Históricos del producto interno bruto (PIB): Cuentas nacionales trimestrales', '[Boletines técnicos, 2020-2026].', 'DANE.', 'https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales/historicos-producto-interno-bruto-pib'));
kids.push(R('Federación Colombiana de Ganaderos. ', 's. f.', 'Precios: Ganado gordo, kilo en pie, macho de ceba', '[Datos históricos, 2020-2026].', 'Fedegán.', 'https://www.fedegan.org.co/estadisticas/precios'));
kids.push(R('Federación Nacional de Avicultores de Colombia. ', 's. f.', 'Precios PEE: Huevo y pollo por kilogramo', '[Datos históricos, 2020-2026; se consideraron muslos, pierna, pechuga y pollo entero].', 'Fenavi.', 'https://fenavi.org/precios-pee/'));
kids.push(R('Porkcolombia. ', 's. f.', 'Ronda de precios: Precio del kilo de cerdo en pie, promedio mensual', '[Datos históricos, 2020-2026].', 'Porkcolombia.', 'https://porkcolombia.co/ronda-de-precios/'));
kids.push(R('Siigo. ', 's. f.', 'Salario mínimo vigente', '[Entrada de blog sobre derecho laboral; aumentos del salario mínimo legal mensual vigente, 2020-2026].', 'Siigo.', 'https://www.siigo.com/blog/derecho-laboral/salario-minimo-vigente/'));
kids.push(CAPT('Tabla A1. Correspondencia entre fuentes y variables de la base'));
kids.push(table(['Fuente', 'Variable en la base', 'Observaciones por confirmar'], [
  ['DANE, SIPSA (leche)', 'Precio Leche', 'Unidad (COP/litro) y si es promedio nacional.'],
  ['Fedegán', 'Precio Carne Res', 'La fuente es el precio del ganado gordo en pie (macho de ceba). La variable de la base se llama "carne res"; en el planteamiento inicial se hablaba de carne en canal. [[Confirmar cuál es el precio usado]].'],
  ['Porkcolombia', 'Precio carne cerdo', 'Precio del kilo de cerdo en pie, promedio mensual.'],
  ['Fenavi', 'Precio huevo; Precio Pollo', '[[Confirmar cómo se combinaron muslos, pierna, pechuga y pollo entero en una sola serie de pollo, y la unidad del huevo]].'],
  ['DANE, IPC', 'IPC; Inflación Mensual', 'La fuente publica variación por ciudades; la base tiene una serie nacional. [[Confirmar si es el total nacional]].'],
  ['DANE, PIB', 'PIB; PIB Agro', 'Un valor por año; [[confirmar si 2026 es un pronóstico o un dato observado]].'],
  ['Siigo', 'Porc Crec SMMLV', 'Fuente secundaria (blog comercial). Se recomienda verificar contra los decretos oficiales del Gobierno nacional.'],
  ['Sin fuente listada', 'Perros; Gatos', '[[Indicar la fuente de la población de perros y gatos]].'],
  ['Sin fuente listada', 'Mercado; Venta Laboratorio; Share Laboratorio', '[[Indicar proveedor y definición de las ventas de mercado y del Laboratorio]].'],
], [2500, 2400, 4460], { boldFirst: true }));
kids.push(gap());
kids.push(H1n('Anexo B. Reproducibilidad'));
kids.push(P('Todo el análisis está en el repositorio. Orden de ejecución:'));
kids.push(table(['Paso', 'Script', 'Función'], [
  ['1', 'src/prepare_data.py', 'Limpieza y completado estacional de julio a diciembre de 2026 (con prueba retrospectiva).'],
  ['2', 'src/build_features.py', 'Variables de 12 meses móviles y partición temporal.'],
  ['3', 'src/protocolo.py dev', 'Validación cruzada con purga, selección, umbral y diagnósticos (sin tocar la prueba).'],
  ['4', 'src/protocolo.py prueba', 'Evaluación única en prueba (con candado) y reajuste final.'],
  ['5', 'src/proyeccion_2027.py', 'Proyección 2027 y sensibilidad del modelo final.'],
  ['6', 'src/datos_informe.py, cifras_informe.py, figuras_informe.py', 'Cifras y figuras del informe.'],
  ['7', 'informe/construir_informe.js', 'Genera este documento a partir de las cifras (sin cifras digitadas a mano).'],
], [800, 3900, 4660]));
kids.push(gap());
kids.push(CAPT('Referencias metodológicas'));
kids.push(ref([...runs('Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. '), new TextRun({ text: 'Journal of Machine Learning Research, 12', italics: true }), ...runs(', 2825-2830.')]));
kids.push(ref([...runs('Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schröder, B., Thuiller, W., Warton, D. I., Wintle, B. A., Hartig, F., & Dormann, C. F. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. '), new TextRun({ text: 'Ecography, 40', italics: true }), ...runs('(8), 913-929. https://doi.org/10.1111/ecog.02881')]));

// ------------------------------------------------------------------ documento
const doc = new Document({
  creator: 'Equipo del proyecto', title: 'Informe Técnico de Mercado Farmacéutico de Salud Animal en Colombia',
  styles: {
    default: { document: { run: { font: 'Calibri', size: 22, color: INK } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 52, bold: true, color: ACC, font: 'Calibri' }, paragraph: { spacing: { after: 200 } } },
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 34, bold: true, color: ACC }, paragraph: { spacing: { before: 120, after: 200 }, outlineLevel: 0, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 25, bold: true, color: INK }, paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1, keepNext: true } },
    ],
  },
  numbering: { config: [
    { reference: 'vin', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
      { level: 1, format: LevelFormat.BULLET, text: '–', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1080, hanging: 270 } } } }] },
    { reference: 'num', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 320 } } } }] },
    { reference: 'num2', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 320 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1300, bottom: 1200, left: 1440, right: 1440 } } },
    headers: { default: new Header({ children: [new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE, space: 4 } }, children: [new TextRun({ text: 'Informe Técnico de Mercado Farmacéutico de Salud Animal en Colombia', size: 16, color: MUTED })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: 'Borrador 1 · Página ', size: 16, color: MUTED }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: MUTED })] })] }) },
    children: kids,
  }],
});
const out = path.join(__dirname, 'Informe_Tecnico_Mercado_Farmaceutico_Salud_Animal_Colombia.docx');
Packer.toBuffer(doc).then(b => { fs.writeFileSync(out, b); console.log('ok', out, Math.round(b.length / 1024) + ' KB'); });
