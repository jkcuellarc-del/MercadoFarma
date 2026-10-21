// Construye informe_v2/Informe_Tecnico_Mercado_Farmaceutico_Salud_Animal_Colombia.docx (protocolo v2)
// Todas las cifras salen de informe_v2/cifras.json (generado por informe_v2/construir_cifras.py).
// Marcado de texto: **negrita**, [[pendiente por confirmar]] (resaltado en amarillo).
const fs = require('fs');
const path = require('path');
const DOCX = require('docx');
const C = JSON.parse(fs.readFileSync(path.join(__dirname, 'cifras.json'), 'utf8'));

const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, AlignmentType,
  HeadingLevel, LevelFormat, ImageRun, Footer, Header, PageNumber, PageBreak } = DOCX;

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

const H3b = t => new Paragraph({ spacing:{before:160,after:60}, keepNext:true, children:[new TextRun({text:t,bold:true,size:23})] });
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
// ------------------------------------------------------------------ 4
kids.push(H1('4. Modelado'));
kids.push(H2('4.1 Líneas base y modelo lineal de referencia'));
kids.push(B('**Base 1: crecimiento de hace 12 meses.** Predice que el crecimiento será igual al observado un año antes. Reproduce la práctica de planear con el crecimiento del año anterior.'));
kids.push(B('**Base 2: promedio histórico de la especie.** Predice el crecimiento medio de la especie en el entrenamiento del pliegue. Es la referencia de un modelo que no usa ninguna variable explicativa.'));
kids.push(B(`**Modelo base lineal: regresión lineal sin regularizar.** Referencia de la familia lineal. Con 10 variables y unas 49 observaciones por especie se sobreajusta: error de validación de ${f1(cv(TM, 'ols').MAE_cv)} pp en el mercado y R² fuera de pliegue de ${f1(cv(TM, 'ols').R2_oof)} (frente a ${f1(cv(TM, 'ols').R2_entrenamiento, 2)} en entrenamiento). Por eso los modelos lineales finales llevan regularización (Ridge, Elastic Net).`));
kids.push(H2('4.2 Selección de predictores'));
kids.push(P('Antes de comparar los modelos se revisó si otros predictores mejoraban el resultado, siempre con datos de desarrollo, las mismas filas y los mismos pliegues, con cinco modelos de rejilla reducida. Los conjuntos se declararon antes de evaluarlos:'));
kids.push(table(['Conjunto', 'Contenido'], [
  ['S0 (actual)', 'Inflación, PIB, PIB agro, salario mínimo y cambio nominal de los cinco precios'],
  ['S1', 'S0 + crecimiento de hace 12 meses de la propia serie (autorregresivo)'],
  ['S2 (reales)', 'S0 con los precios deflactados por el IPC (cambio real)'],
  ['S3', 'S0 + inflación y precios rezagados 6 y 12 meses'],
  ['S4', 'S0 + participación del mercado donde compite en el mercado total'],
  ['S5', 'S2 + autorregresivo + rezagos + participación'],
  ['S6', 'S0 + TRM (cambio del promedio de 12 meses y rezagos de 6 y 12 meses)'],
  ['S7', 'S2 + TRM'],
], [2200, 7160], { boldFirst: true }));
kids.push(CAPT('Tabla 4. Error de validación cruzada del mejor modelo de cada conjunto (MAE, pp)'));
const conj = ['S0_actual', 'S1_ar', 'S2_real', 'S3_rezagos', 'S4_mezcla', 'S5_todo', 'S6_trm', 'S7_real_trm'];
const sc = (t, c) => { const r = scr(t, c); return r ? f1(r.MAE_cv, 2) : '–'; };
kids.push(table(['Conjunto', 'Mercado', 'Mercado donde compite', 'Laboratorio'], conj.map(c => [c.replace('_', ' '), sc('mercado', c), sc('compite', c), sc('lab', c)]).concat([['Referencia: promedio de la especie', f1(scr('mercado', 'base').MAE_cv, 2) && f1(C.screening.find(r => r.tarea === 'mercado' && r.mejor_modelo === 'B2_media_especie').MAE_cv, 2), f1(C.screening.find(r => r.tarea === 'compite' && r.mejor_modelo === 'B2_media_especie').MAE_cv, 2), f1(C.screening.find(r => r.tarea === 'lab' && r.mejor_modelo === 'B2_media_especie').MAE_cv, 2)]]), [3600, 1700, 2300, 1760], { right: [1, 2, 3] }));
kids.push(img('f8_cribado.png', 560));
kids.push(CAP('Figura 3. MAE de validación cruzada por conjunto de predictores. En azul, los conjuntos con precios reales.'));
kids.push(B(`**Precios reales (S2):** mejoran el mercado de ${sc('mercado', 'S0_actual')} a ${sc('mercado', 'S2_real')} pp y el mercado donde compite de ${sc('compite', 'S0_actual')} a ${sc('compite', 'S2_real')}. La mejora es de unos 0,4 pp y la diferencia entre pliegues es de 0,5 pp, así que no es concluyente por sí sola. Empeoran un poco el Laboratorio (${sc('lab', 'S0_actual')} a ${sc('lab', 'S2_real')}), dentro del ruido. El equipo decidió adoptarlos para todos los modelos.`));
kids.push(B(`**TRM:** agregada a S0 no cambia nada (${sc('mercado', 'S6_trm')} pp) y agregada a los precios reales aporta ${f1(scr('mercado', 'S2_real').MAE_cv - scr('mercado', 'S7_real_trm').MAE_cv, 2)} pp en el mercado, dentro del ruido. No explica el crecimiento del mercado con estos datos, y no entró al modelo.`));
kids.push(B('**Autorregresivo, rezagos y participación:** no mejoran. El crecimiento del año anterior no predice el siguiente (autocorrelación de 12 meses cercana a cero dentro de cada especie).'));
kids.push(H3b('Variables importantes'));
const ctl = (t, cj, k) => Math.max(...C.importancia.filter(r => r.tarea === t && r.conjunto === cj && r.es_control).map(r => r[k]));
kids.push(P(`Para identificar qué variables importan se usó la importancia por permutación (cuánto sube el error fuera de pliegue al barajar una variable) con tres columnas de ruido como control: una variable cuenta solo si supera al mayor control (en el mercado, ${f1(ctl('mercado', 'S7_real_trm', 'perm_gbm_pp'), 3)} pp con Gradient Boosting). También se calcularon la importancia por impureza del bosque y la estabilidad de Lasso. Esta última no discrimina: los controles de ruido quedan elegidos hasta 60% a 75% de las veces.`));
kids.push(img('f7_importancia.png', 560));
kids.push(CAP('Figura 4. Importancia por permutación (Gradient Boosting) con el conjunto S7. La línea naranja es el mayor control de ruido.'));
const iv = (t, v) => { const r = imp(t, 'S7_real_trm', v); return r ? r.perm_gbm_pp : 0; };
kids.push(table(['Variable', 'Importancia en el mercado (pp)', 'Importancia en el Laboratorio (pp)'], [
  ['Precio real de la carne de cerdo', f1(iv('mercado', 'real_var_cerdo'), 2), f1(iv('lab', 'real_var_cerdo'), 2)],
  ['Precio real del huevo', f1(iv('mercado', 'real_var_huevo'), 2), f1(iv('lab', 'real_var_huevo'), 2)],
  ['Precio real de la carne de res', f1(iv('mercado', 'real_var_res'), 2), f1(iv('lab', 'real_var_res'), 2)],
  ['Inflación de animales de compañía', f1(iv('mercado', 'ipc_yoy_CA'), 2), f1(iv('lab', 'ipc_yoy_CA'), 2)],
  ['Crecimiento del mercado donde compite', '–', f1(iv('lab', 'y_compite'), 2)],
  ['PIB, PIB agropecuario, salario mínimo e inflación', '≈ 0,00', '≈ 0,00 a 0,03'],
  ['TRM (tres variables)', '≈ 0,00', f1(Math.max(iv('lab', 'trm_yoy12'), iv('lab', 'trm_yoy12_l6'), iv('lab', 'trm_yoy12_l12')), 2)],
  ['Mayor control de ruido', f1(ctl('mercado', 'S7_real_trm', 'perm_gbm_pp'), 3), f1(ctl('lab', 'S7_real_trm', 'perm_gbm_pp'), 3)],
], [4200, 2580, 2580], { right: [1, 2], boldFirst: true }));
kids.push(H2('4.3 Familias de modelos y búsqueda de hiperparámetros'));
kids.push(P('Se compararon diez modelos de cuatro familias, con el mismo Pipeline, los mismos pliegues y la misma métrica (MAE), usando búsqueda en rejilla (GridSearchCV) sobre cada pliegue de la validación cruzada del entrenamiento.'));
kids.push(table(['Familia', 'Modelo', 'Hiperparámetros explorados'], [
  ['Lineal', 'Regresión lineal, común y por especie', 'Sin hiperparámetros (solo ponderación)'],
  ['Lineal regularizada', 'Ridge, común y por especie', 'alpha ∈ {0,1; 1; 10; 100; 1.000; 10.000}'],
  ['Lineal regularizada', 'Elastic Net (combina Lasso y Ridge), común y por especie', 'alpha ∈ {0,001; 0,01; 0,1; 1}; l1_ratio ∈ {0,1; 0,5; 0,9; 1,0 (Lasso)}'],
  ['Vecinos', 'K vecinos más cercanos', 'k ∈ {3; 5; 8; 12; 20; 30}; peso uniforme o por distancia; distancia L1 o L2'],
  ['Agregación (bagging)', 'Bagging de árboles y Random Forest', 'profundidad ∈ {2; 3; 5; 8; sin límite}; hojas mínimas ∈ {3; 8}; fracción de datos o variables'],
  ['Refuerzo (boosting)', 'Gradient Boosting', 'iteraciones ∈ {50; 100; 200; 400}; tasa ∈ {0,03; 0,1}; profundidad ∈ {1; 2; 3}; hojas ∈ {3; 8}'],
  ['Todos (menos K vecinos)', 'Ponderación por clase', '{sí, no}'],
], [2200, 3200, 3960]));
kids.push(H2('4.4 Criterio de selección declarado antes de ejecutar'));
kids.push(NUM('El mejor ajuste de cada modelo se define por el menor MAE medio de validación cruzada.'));
kids.push(NUM('Son elegibles los modelos cuyo MAE medio está a menos de un error estándar del mejor.'));
kids.push(NUM('Entre los elegibles se escoge el de menor complejidad: lineales por especie, luego lineales comunes, K vecinos, bagging y bosque, y por último Gradient Boosting. El simulador necesita efectos propios por especie y una respuesta suave.'));
kids.push(NUM('El modelo elegido debe superar las dos líneas base en validación cruzada. Si no lo hace, se declara que no agrega valor.'));
kids.push(P('El examen no interviene en ninguno de estos pasos. Se declaró además, antes de consultarlo, que se reportaría de forma informativa el modelo de menor MAE de validación si difería del elegido.'));
kids.push(H2('4.5 Resultados de validación cruzada'));
const cvRows = T => ['ols_esp', 'ridge_esp', 'enet_esp', 'ols', 'ridge', 'enet', 'knn', 'bagging', 'rf', 'gbm', 'B2_media_especie', 'B1_crecimiento_hace_12m'].map(m => {
  const r = cv(T, m); return [NOM[m], `${f1(r.MAE_cv)} ± ${f1(r.sd)}`, r.R2_oof == null ? '–' : f1(r.R2_oof, 2), r.R2_entrenamiento == null ? '–' : f1(r.R2_entrenamiento, 2), hp(T, m)]; });
kids.push(CAPT(`Tabla 5. Mercado: MAE de validación cruzada (${TM.seleccion.n_pliegues} pliegues; media ± desviación), R² y mejores hiperparámetros`));
kids.push(table(['Modelo', 'MAE (pp)', 'R² fuera de pliegue', 'R² entren.', 'Hiperparámetros'], cvRows(TM), [2500, 1250, 1250, 1000, 3360], { right: [1, 2, 3] }));
kids.push(CAPT(`Tabla 6. Laboratorio: MAE de validación cruzada (${TL.seleccion.n_pliegues} pliegues), R² y mejores hiperparámetros`));
kids.push(table(['Modelo', 'MAE (pp)', 'R² fuera de pliegue', 'R² entren.', 'Hiperparámetros'], cvRows(TL), [2500, 1250, 1250, 1000, 3360], { right: [1, 2, 3] }));
kids.push(CAP('Las diferencias entre pliegues (desviación de 1 a 2,6 pp) son mayores que las diferencias entre la mayoría de los modelos. El R² del Laboratorio es alto en parte porque cada especie tiene su propio nivel de crecimiento: con solo el promedio de la especie ya se llega a 0,60.'));
kids.push(img('comparacion_mercado.png', 470));
kids.push(CAP('Figura 5. Mercado: MAE de validación cruzada por modelo y R² fuera de pliegue.'));
kids.push(img('curvas_validacion_mercado.png', 600));
kids.push(CAP('Figura 6. Curvas de validación del mercado: alpha de Ridge y Elastic Net, k de K vecinos, profundidad de los árboles, iteraciones del boosting y número de árboles.'));
kids.push(B(`**Ridge y Elastic Net:** el error baja al aumentar la regularización y se estabiliza cerca de alpha = 1.000 (Ridge) o 0,1 (Elastic Net): el modelo se acerca al promedio de cada especie.`));
kids.push(B(`**Boosting:** la curva de validación alcanza su mínimo en ${C.boosting.mercado.mejor_iter} iteraciones (${f1(C.boosting.mercado.mae_min, 2)} pp) y empeora después (${f1(C.boosting.mercado.mae_400, 2)} pp con 400), mientras el error de entrenamiento sigue bajando hasta ${f1(C.boosting.mercado.mae_train_400, 2)}: sobreajuste. Se eligieron ${C.boosting.mercado.elegida} iteraciones.`));
kids.push(B(`**Bagging y bosque:** el error se estabiliza hacia los 100 árboles (Random Forest: ${f1(C.arboles.mercado.rf['10'], 2)} con 10 árboles y ${f1(C.arboles.mercado.rf['100'], 2)} con 100); más árboles no ayudan. Ese es el techo de la varianza que se elimina promediando; el resto del error es sesgo.`));
kids.push(H2('4.6 Modelos elegidos'));
kids.push(CALLOUT(`**Modelo A (elegido por la regla).** Mercado: Elastic Net común (${hp(TM, 'enet')}). Mercado donde compite: Ridge común (${hp(TC, 'ridge')}). Laboratorio: Ridge por especie (${hp(TL, 'ridge_esp')}) con el crecimiento del mercado total como variable (variante de menor error: ${f1(TL.seleccion.MAE_cv_final, 2)} pp frente a ${f1(TLn.seleccion.MAE_cv_final, 2)} con el mercado donde compite). Los cinco o seis modelos más precisos de cada tarea quedaron dentro de un error estándar entre sí, y la regla escogió el más simple.`));
kids.push(B(`**El modelo A es casi una constante en el mercado.** Su R² fuera de pliegue es ${f1(cv(TM, 'enet').R2_oof, 2)} y en entrenamiento ${f1(cv(TM, 'enet').R2_entrenamiento, 2)}: predice cerca del promedio de todas las especies. Supera a las líneas base en validación (${f1(cv(TM, 'enet').MAE_cv)} frente a ${f1(cv(TM, 'B2_media_especie').MAE_cv)} y ${f1(cv(TM, 'B1_crecimiento_hace_12m').MAE_cv)} pp), pero por una diferencia que está dentro del ruido.`));
kids.push(B(`**Gradient Boosting (modelo B)** tuvo el menor MAE de validación en las tres tareas (mercado ${f1(cv(TM, 'gbm').MAE_cv)}, Laboratorio ${f1(cv(TL, 'gbm').MAE_cv)} pp) y el único R² positivo en el mercado (${f1(cv(TM, 'gbm').R2_oof, 2)}). Quedó fuera por la regla de simplicidad; por eso se reporta aparte.`));

// ------------------------------------------------------------------ 5
kids.push(H1('5. Evaluación'));
kids.push(H2('5.1 Métricas según el costo del error'));
kids.push(table(['Métrica', 'Qué mide', 'Por qué se eligió'], [
  ['MAE (pp)', 'Error medio absoluto del crecimiento, en puntos porcentuales.', 'Costo lineal en la distancia al valor real y fácil de explicar al negocio. Principal métrica técnica.'],
  ['RMSE (pp), sesgo (pp) y R²', 'RMSE penaliza errores grandes; el sesgo indica si el modelo sobrestima (positivo) o subestima; R² compara con predecir el promedio.', 'Un sesgo positivo sostenido es el error más costoso en el supuesto de costos.'],
  ['Costo medio por escenario', 'Costo promedio del escenario asignado: 2 por nivel de sobrestimación y 1 por nivel de subestimación.', 'Es la métrica de éxito del negocio (Sección 1.4).'],
  ['Acierto y F1 macro de escenario', 'Proporción de escenarios correctos y promedio del F1 por clase.', 'El acierto solo engaña con clases raras; el F1 macro da el mismo peso a cada escenario.'],
  ['Recall de "regular"', 'De los casos realmente "regulares", cuántos detecta el modelo.', 'Es el escenario más costoso de no ver: llega con meta e inventario que no se vende.'],
], [2300, 3600, 3460], { boldFirst: true }));
kids.push(H2('5.2 Estabilidad de la validación cruzada'));
const fo = T => T.seleccion.mejores[T.seleccion.final].folds;
kids.push(P(`El MAE del modelo A en el mercado va de ${f1(Math.min(...fo(TM)))} a ${f1(Math.max(...fo(TM)))} pp entre los ${TM.seleccion.n_pliegues} pliegues (media ${f1(TM.seleccion.MAE_cv_final)}, desviación ${f1(TM.seleccion.sd_cv_final)}). En el Laboratorio va de ${f1(Math.min(...fo(TL)))} a ${f1(Math.max(...fo(TL)))} pp entre ${TL.seleccion.n_pliegues} pliegues (media ${f1(TL.seleccion.MAE_cv_final)}, desviación ${f1(TL.seleccion.sd_cv_final)}). La variabilidad es alta frente al tamaño de las mejoras sobre las líneas base.`));
kids.push(CAPT('Tabla 7. Error fuera de pliegue por especie del modelo A (MAE en pp, media y desviación)'));
kids.push(table(['Especie', 'Mercado', 'Laboratorio'], EST.map(e => { const a = TM.oof_especie.find(r => r.Especie === e), b = TL.oof_especie.find(r => r.Especie === e);
  return [ESP[e], `${f1(a['mean'])} ± ${f1(a['std'])}`, `${f1(b['mean'])} ± ${f1(b['std'])}`]; }), [3360, 3000, 3000], { right: [1, 2] }));
kids.push(gap());
kids.push(H2('5.3 Umbral de decisión recomendado'));
kids.push(P('Los umbrales de escenario (8% y 15%) son del negocio y no se modifican. Lo que sí se puede ajustar es cuánta prudencia se aplica antes de clasificar: se resta un descuento m a la predicción y luego se aplican los umbrales. El valor de m se eligió con las predicciones fuera de pliegue para minimizar el costo esperado.'));
kids.push(img('f4_umbral.png', 560));
kids.push(CAP('Figura 7. Costo medio por observación según el descuento de prudencia m (predicciones fuera de pliegue del entrenamiento).'));
const um = (T, m) => T.umbral.reduce((a, r) => Math.abs(r.m_pp - m) < Math.abs(a.m_pp - m) ? r : a);
kids.push(table(['', 'Mercado', 'Laboratorio'], [
  ['m recomendado por validación cruzada', `${sg(TM.seleccion.m_umbral * 100)} pp`, `${sg(TL.seleccion.m_umbral * 100)} pp`],
  ['Costo medio con m = 0 (validación)', f1(um(TM, 0).costo_medio, 2), f1(um(TL, 0).costo_medio, 2)],
  ['Costo medio con el m recomendado (validación)', f1(um(TM, TM.seleccion.m_umbral * 100).costo_medio, 2), f1(um(TL, TL.seleccion.m_umbral * 100).costo_medio, 2)],
  ['Acierto en el examen con m = 0', pct(PR.mercado.modelo_m0.acierto, 0), pct(PR.lab_ym.modelo_m0.acierto, 0)],
  ['Acierto en el examen con el m recomendado', pct(PR.mercado.modelo_mstar.acierto, 0), pct(PR.lab_ym.modelo_mstar.acierto, 0)],
], [4500, 2430, 2430], { right: [1, 2], boldFirst: true }));
kids.push(gap());
kids.push(P(`**Recomendación sobre el umbral:** no adoptar ningún descuento de prudencia por ahora. La mejora esperada en validación es pequeña, y en el examen el m recomendado empeoró la clasificación (mercado: acierto de ${pct(PR.mercado.modelo_m0.acierto, 0)} a ${pct(PR.mercado.modelo_mstar.acierto, 0)}; Laboratorio: de ${pct(PR.lab_ym.modelo_m0.acierto, 0)} a ${pct(PR.lab_ym.modelo_mstar.acierto, 0)}). Se mantienen los umbrales de 8% y 15% y se muestra siempre el margen de error junto a cada escenario. El valor de m debe recalcularse con los datos de julio a diciembre de 2026. Esta recomendación se apoya en el examen solo como advertencia; no se usó para modificar el protocolo.`));
kids.push(H2('5.4 Diagnóstico de sesgo y varianza'));
kids.push(img('f3_aprendizaje.png', 560));
kids.push(CAP('Figura 8. Curvas de aprendizaje del modelo A: error en los meses de entrenamiento y en meses retenidos, según la cantidad de meses usados para entrenar.'));
const lcm = TM.curva_aprendizaje, lcl = TL.curva_aprendizaje, ult = a => a[a.length - 1];
const rg = (T, a) => T.curva_regularizacion.find(r => r.alpha === a);
kids.push(B(`**Mercado.** Con 36 meses el error en entrenamiento es ${f1(ult(lcm).MAE_entrenamiento)} pp y en meses retenidos ${f1(ult(lcm).MAE_retenido)} pp; con 6 meses era ${f1(lcm[0].MAE_entrenamiento)} y ${f1(lcm[0].MAE_retenido)}. Las dos curvas se acercan y quedan altas: el modelo regularizado tiene **sesgo alto y poca varianza**; más datos no cambiarían mucho su error. Es lo esperable si casi no usa las variables.`));
{ const rc = TM.curva_regularizacion, lo = rc[0], hi = rc[rc.length - 1]; const fa = a => String(a).replace('.', ','); kids.push(B(`**Compromiso sesgo-varianza.** Con poca regularización el modelo se sobreajusta (en el mercado, Ridge común con alpha = ${fa(lo.alpha)} tiene ${f1(lo.MAE_entrenamiento)} pp en entrenamiento y ${f1(lo.MAE_cv)} en validación); con alpha = ${fa(hi.alpha)} tiene ${f1(hi.MAE_entrenamiento)} y ${f1(hi.MAE_cv)}.`)); }
kids.push(B(`**Gradient Boosting** muestra el patrón contrario: error de entrenamiento de ${f1(C.boosting.mercado.mae_train_400, 2)} pp con 400 iteraciones frente a ${f1(C.boosting.mercado.mae_400, 2)} en validación: alta varianza, que se controla con pocas iteraciones (50) y árboles poco profundos.`));
kids.push(B(`**Laboratorio.** Entrenamiento ${f1(ult(lcl).MAE_entrenamiento)} pp y meses retenidos ${f1(ult(lcl).MAE_retenido)} pp con ${ult(lcl).meses_entrenamiento} meses de entrenamiento; la curva no se estabiliza con tan pocos meses, así que el diagnóstico es menos confiable.`));
kids.push(H2('5.5 Resultados en el examen (enero a junio de 2026)'));
kids.push(P('Todas las cifras son errores en puntos porcentuales de crecimiento de 12 meses sobre 24 observaciones (6 meses × 4 especies, con ventanas solapadas: el número efectivo de observaciones independientes es mucho menor). El laboratorio se evaluó con el crecimiento del mercado proyectado por el modelo de mercado, que es lo que ocurrirá en 2027.'));
const ex = (k, t) => (t === 'mercado' ? PR.mercado : PR.lab_ym);
kids.push(CAPT('Tabla 8. Examen: consulta principal'));
kids.push(table(['Modelo', 'Mercado: MAE', 'Mercado: R²', 'Laboratorio: MAE', 'Laboratorio: R²'], [
  ['Modelo A (elegido por la regla)', f1(PR.mercado.MAE_pp), f1(PR.mercado.R2, 2), f1(PR.lab_ym.MAE_pp), f1(PR.lab_ym.R2, 2)],
  ['Modelo B (Gradient Boosting)', f1(PR.mercado.alternativa_mejor_cv.MAE_pp), f1(PR.mercado.alternativa_mejor_cv.R2, 2), f1(PR.lab_ym.alternativa_mejor_cv.MAE_pp), f1(PR.lab_ym.alternativa_mejor_cv.R2, 2)],
  ['Base 2: promedio de la especie', f1(PR.mercado.B2_media_especie.MAE_pp), f1(PR.mercado.B2_media_especie.R2, 2), f1(PR.lab_ym.B2_media_especie.MAE_pp), f1(PR.lab_ym.B2_media_especie.R2, 2)],
  ['Base 1: crecimiento de hace 12 meses', f1(PR.mercado.B1_crecimiento_hace_12m.MAE_pp), '–', f1(PR.lab_ym.B1_crecimiento_hace_12m.MAE_pp), '–'],
], [3200, 1500, 1500, 1660, 1500], { right: [1, 2, 3, 4], boldFirst: true }));
kids.push(CAPT('Tabla 9. Examen: consulta complementaria posterior, solo informativa (K vecinos, Random Forest y regresión lineal)'));
kids.push(table(['Modelo', 'Mercado: MAE', 'Mercado: R²', 'Laboratorio: MAE', 'Laboratorio: R²'], ['knn', 'rf', 'ols'].map(m => [NOM[m], f1(PC[m].mercado.MAE_pp), f1(PC[m].mercado.R2, 2), f1(PC[m].lab.MAE_pp), f1(PC[m].lab.R2, 2)]), [3200, 1500, 1500, 1660, 1500], { right: [1, 2, 3, 4], boldFirst: true }));
kids.push(img('f5_prueba_mercado.png', 600));
kids.push(CAP('Figura 9. Mercado: crecimiento de 12 meses real y predicho por los modelos A y B, por especie. Líneas punteadas grises: umbrales de 8% y 15%.'));
kids.push(img('f5_prueba_lab.png', 600));
kids.push(CAP('Figura 10. Laboratorio: crecimiento de 12 meses real y predicho por los modelos A y B, por especie.'));
const pe = (g, t) => EST.map(e => `${ESP[e]} ${f1(PR[t][g === 'A' ? 'por_especie' : 'alternativa_mejor_cv'] ? (g === 'A' ? PR[t].por_especie[e].MAE_pp : PR[t].alternativa_mejor_cv.por_especie[e].MAE_pp) : 0)}`).join('; ');
kids.push(B(`**Mercado.** El modelo A (${f1(PR.mercado.MAE_pp)} pp) no mejora a las líneas base (${f1(PR.mercado.B2_media_especie.MAE_pp)} y ${f1(PR.mercado.B1_crecimiento_hace_12m.MAE_pp)}). Por especie: ${pe('A', 'mercado')} pp. Aves explica la mayor parte: el modelo predice crecimiento positivo y el mercado cayó. Gradient Boosting reduce el error a ${f1(PR.mercado.alternativa_mejor_cv.MAE_pp)} (R² ${f1(PR.mercado.alternativa_mejor_cv.R2, 2)}); K vecinos, a ${f1(PC.knn.mercado.MAE_pp)}.`));
kids.push(B(`**Detección de escenarios.** En el mercado, el modelo A acertó ${pct(PR.mercado.modelo_m0.acierto, 0)} de los escenarios y no detectó ningún caso "regular" (${PR.mercado.modelo_m0.matriz[0].reduce((a, b) => a + b, 0)} casos reales, seis de ellos de aves); la base 2 acertó ${pct(PR.mercado.B2_m0.acierto, 0)}. No debe usarse como alarma de bajo crecimiento.`));
kids.push(B(`**Laboratorio.** El modelo A (${f1(PR.lab_ym.MAE_pp)} pp) mejora la base 1 (${f1(PR.lab_ym.B1_crecimiento_hace_12m.MAE_pp)}) pero no la base 2 (${f1(PR.lab_ym.B2_media_especie.MAE_pp)}). En clasificación acierta ${pct(PR.lab_ym.modelo_m0.acierto, 0)} (costo ${f1(PR.lab_ym.modelo_m0.costo_medio, 2)}) y la base 2 ${pct(PR.lab_ym.B2_m0.acierto, 0)} (costo ${f1(PR.lab_ym.B2_m0.costo_medio, 2)}). Gradient Boosting (${f1(PR.lab_ym.alternativa_mejor_cv.MAE_pp)} pp) y Random Forest (${f1(PC.rf.lab.MAE_pp)}) tienen el menor error.`));
kids.push(B('**Lectura prudente.** Gradient Boosting, K vecinos y Random Forest rindieron mejor que el modelo elegido, pero se miraron después del examen o sobre el mismo examen. Cuando se comparan varios modelos sobre los mismos datos, el que gana en parte lo hace por suerte. La regresión lineal sin regularizar queda muy por detrás, como en validación.'));

// ------------------------------------------------------------------ 6
kids.push(H1('6. Decisión, límites y gobernanza'));
kids.push(H2('6.1 Recomendación'));
kids.push(CALLOUT(`**Recomendación para quien decide:** usar la proyección 2027 como **referencia con rango entre los modelos A y B**, para el presupuesto y la planeación de inventarios, y no como meta ni como base de compensación. Probar el plan con un margen de ±${f1(band('A', 'mercado', 'Total'), 0)} puntos alrededor de la proyección del mercado y de ±${f1(band('A', 'lab', 'Total'), 0)} alrededor de la del Laboratorio (margen típico de error). No fijar metas por especie con estas cifras sin revisarlas con el equipo comercial, sobre todo en bovinos.`));
kids.push(NUM('**Aprobar el uso como insumo, no como compromiso.** El modelo A no superó a los métodos sencillos en el examen; el B sí, pero no está confirmado.', 'num2'));
kids.push(NUM('**No actuar sobre la alerta de escenario "regular".** El modelo no la detecta en el mercado.', 'num2'));
kids.push(NUM('**Revalidar en el primer trimestre de 2027** con los datos reales de julio a diciembre de 2026, que son el examen verdaderamente nuevo, y decidir entonces si el modelo B reemplaza al A.', 'num2'));
kids.push(NUM('**Alimentar el simulador con pronósticos oficiales** de inflación, PIB y salario mínimo 2027 y actualizarlos cuando cambien.', 'num2'));
kids.push(NUM('**Reunir más historia y más variables** (precios por producto, canales, eventos sanitarios) antes de pedirle al modelo efectos causales.', 'num2'));
kids.push(H2('6.2 Proyección 2027, escenario base'));
kids.push(P(`Valores base de 2027: inflación ${pct(C.base.ipc)} (mediana de la encuesta de analistas del Banco de la República para diciembre de 2027; el equipo técnico del Banco proyecta 4,3% y el Gobierno 4,8%), PIB ${f1(C.base.pib)}% (BBVA Research; consenso de analistas entre 1,8% y 2,6%), PIB agropecuario ${f1(C.base.pib_agro)}% y salario mínimo ${pct(C.base.smmlv)} (promedios históricos, sin pronóstico público) y precios en su nivel de junio de 2026 durante 2027. Las cifras de inflación y PIB provienen de reportes de prensa y de análisis; no pudieron verificarse en las páginas oficiales. [[Confirmar contra fuentes oficiales]].`));
kids.push(CAPT('Tabla 10. Crecimiento nominal proyectado 2027 (escenario base)'));
kids.push(table(['Especie', 'Mercado A', 'Mercado B', 'Laboratorio A', 'Laboratorio B', 'Error típico mercado / Lab. (pp)'], ['CA', 'Cattle', 'Poultry', 'Swine', 'Total'].map(e => [ESP[e], pct(proy('A', e).crec_mercado), pct(proy('B', e).crec_mercado), pct(proy('A', e).crec_lab), pct(proy('B', e).crec_lab), `±${f1(band('A', 'mercado', e))} / ±${f1(band('A', 'lab', e))}`]), [2000, 1300, 1300, 1450, 1450, 1860], { right: [1, 2, 3, 4], boldFirst: true }));
kids.push(CAP('El error típico es el promedio del MAE fuera de pliegue y del MAE del examen por especie para el modelo A; el del total es un promedio ponderado por las ventas de los últimos 12 meses. Para el modelo B los márgenes son: mercado ±' + f1(band('B', 'mercado', 'Total')) + ' y Laboratorio ±' + f1(band('B', 'lab', 'Total')) + ' puntos. El modelo A proyecta el mismo crecimiento de mercado para todas las especies porque es casi una constante.'));
kids.push(H2('6.3 Condiciones que invalidan la recomendación'));
kids.push(table(['Condición', 'Señal de alerta', 'Acción'], [
  ['Error de seguimiento alto', 'MAE trimestral del crecimiento real frente al proyectado mayor a 8 pp en el mercado o 6 pp en el Laboratorio.', 'Detener el uso del simulador y reentrenar.'],
  ['Cambio de régimen', 'Inflación, PIB o precios fuera del rango visto en 2021-2026 (el simulador lo advierte).', 'Tratar el resultado como extrapolación.'],
  ['Evento sanitario o regulatorio', 'Brotes (por ejemplo influenza aviar, Newcastle, fiebre aftosa, peste porcina), cambios de registro o de política de antimicrobianos.', 'Reemplazar la proyección por escenarios específicos de la especie.'],
  ['Cambios de portafolio o competencia', 'Lanzamientos, descontinuaciones o entrada de competidores relevantes.', 'Ajustar la proyección del Laboratorio con juicio experto.'],
  ['Cambio de la fuente', 'Cambio metodológico o de cobertura en SIMVET o en las series de precios.', 'Revalidar la serie completa.'],
  ['Revalidación desfavorable', 'Con los datos de julio a diciembre de 2026, el modelo B no supera a los métodos sencillos.', 'Volver a los métodos sencillos y a la planeación por escenarios.'],
], [2300, 4200, 2860], { boldFirst: true }));
kids.push(H2('6.4 Límites del modelo'));
const sv = (n, k) => sensV(n)[k];
[
  `**Poca historia:** ${TM.seleccion.n_train} observaciones de entrenamiento en el mercado y ${TL.seleccion.n_train} en el Laboratorio, con ventanas solapadas.`,
  `**Poca sensibilidad a las variables.** En el escenario base, el modelo A casi no responde en el mercado. El modelo B sube ${sg(sv('Cambio nominal del precio de la carne de res', 'B_mercado'), 2)} puntos el crecimiento total del mercado por +10 puntos en el cambio nominal del precio de la carne de res y ${sg(sv('Inflación', 'B_mercado'), 2)} por +1 punto de inflación (por la vía de los precios reales); el PIB mueve ${sg(sv('PIB +1', 'B_mercado'), 2)}. Para el Laboratorio, +10 puntos en el precio de la carne de cerdo suben el crecimiento ${sg(sv('Cambio nominal del precio de la carne de cerdo', 'A_lab'), 2)} (modelo A) y ${sg(sv('Cambio nominal del precio de la carne de cerdo', 'B_lab'), 2)} (modelo B). Son efectos menores que el error del modelo: **el simulador no puede cuantificar con confianza qué pasa al mover esas variables.**`,
  '**Sin capacidad de detectar escenarios bajos.** No identifica el escenario "regular" en el mercado.',
  '**Crecimiento nominal.** Incluye inflación; una inflación más alta tiende a subir el crecimiento nominal por el efecto de precios, no por mayor demanda.',
  `**Bovinos en el Laboratorio.** La proyección de 2027 (${pct(proy('A', 'Cattle').crec_lab)} y ${pct(proy('B', 'Cattle').crec_lab)}) contrasta con 14% en 2026 y con la historia de 1% a 14%; requiere revisión del equipo comercial.`,
  '**Supuestos de 2027.** La proyección depende de pronósticos de terceros y de supuestos propios (PIB agropecuario, salario mínimo y precios constantes).',
  '**Modelo B elegido después del examen.** Su ventaja en el examen es optimista. Se confirmará con datos nuevos.',
].forEach(t => kids.push(B(t)));
kids.push(H2('6.5 A quiénes podría perjudicar'));
[
  '**Equipos comerciales:** metas basadas en una cifra puntual pueden penalizar a quienes no la alcancen por razones ajenas.',
  '**Especies con menor peso del Laboratorio (bovinos, aves):** proyecciones de menor calidad pueden llevar a subinvertir o a sobrestockear.',
  '**Productores y clínicas:** el desabastecimiento por subestimación afecta la salud de los animales y la producción; el exceso de inventario puede presionar precios o descuentos.',
  '**Uso prudente de antimicrobianos:** una meta de crecimiento en ese segmento choca con políticas de reducción de uso.',
  '**Quien lea el simulador sin contexto:** puede interpretar un efecto causal donde solo hay asociación (Sección 6.6).',
].forEach(t => kids.push(B(t)));
kids.push(H2('6.6 Correlación y causalidad'));
kids.push(P('Los coeficientes y las importancias describen asociaciones entre series de pocos años; no demuestran que cambiar una variable cause el cambio en el crecimiento. Tres ejemplos:'));
kids.push(B('**Inflación y animales de compañía.** El equipo planteó que con más inflación los hogares priorizan gastos esenciales sobre la salud de la mascota. En la base, el crecimiento nominal de animales de compañía se mueve junto con la inflación (correlación de 0,43), porque las ventas están en pesos corrientes. Al descontar la inflación, la correlación es de 0,04: no hay evidencia a favor ni en contra de la hipótesis. Probarla exigiría datos de unidades vendidas o de ingresos de los hogares.'));
kids.push(B('**Precio real de la carne de cerdo.** Es la variable con más señal predictiva, pero la caída del precio en 2026 coincide con un cambio en las ventas, y ambas pudieron responder a la oferta, a la demanda o a un tercer factor.'));
kids.push(B('**Simulador como "qué pasaría si".** Cambiar un control muestra cómo responde el modelo, no qué pasaría en el mercado si esa variable cambiara. Para efectos causales harían falta experimentos o variaciones exógenas y datos más finos.'));
kids.push(H2('6.7 Plan de seguimiento'));
kids.push(table(['Indicador', 'Frecuencia', 'Umbral de alerta', 'Responsable'], [
  ['MAE del crecimiento de 12 meses real frente al proyectado, por especie', 'Mensual', '> 8 pp mercado; > 6 pp Laboratorio', '[[confirmar]]'],
  ['Sesgo (proyectado menos real)', 'Trimestral', 'Mayor a ±3 pp durante dos trimestres', '[[confirmar]]'],
  ['Variables del simulador frente al rango de entrenamiento', 'Cada uso', 'Cualquier variable fuera de rango', '[[confirmar]]'],
  ['Disponibilidad de pronósticos oficiales 2027', 'Trimestral', 'Cambio de más de 1 pp en inflación o PIB', '[[confirmar]]'],
  ['Revalidación del modelo B con jul-dic 2026', 'Una vez, primer trimestre de 2027', 'B no supera a los métodos sencillos', '[[confirmar]]'],
  ['Eventos sanitarios y de portafolio', 'Continuo', 'Cualquier evento relevante', '[[confirmar]]'],
], [3700, 1500, 2700, 1460]));
kids.push(H2('6.8 Estado del simulador'));
kids.push(P('El simulador publicado (versión web) calcula en el navegador los dos modelos, A y B, con la misma proyección de este informe. Muestra el rango entre ambos, el margen de error, la comparación de modelos (Tabla 8 y 9), un gráfico con historia y proyección, la sensibilidad de cada modelo y avisos cuando un valor sale del rango de entrenamiento. El modelo B se evalúa con los árboles exportados; la evaluación exportada coincide con scikit-learn con diferencias de 6×10⁻¹⁷ o menos. Incluye íconos por especie y el logo en la columna del Laboratorio, y una nota de que es un análisis interno.'));

// ------------------------------------------------------------------ 7
kids.push(H1('7. Roles y trabajo en equipo'));
kids.push(P('El equipo del proyecto está formado por tres perfiles. La tabla resume su aporte; la redacción de los aportes específicos es una propuesta basada en lo registrado en el proyecto y debe ser ajustada por cada integrante.'));
kids.push(table(['Perfil', 'Integrante', 'Aportes'], [
  ['Jefe (patrocinio y decisión)', 'Juan Cuellar Chaparro', 'Plantea el problema de negocio y la decisión que se quiere apoyar; define los escenarios (regular, estable, optimista); valida los tratamientos de datos (devoluciones válidas, aves, participación en cerdos), la decisión de modelar crecimiento nominal, de dejar solo lo que dicen los datos en la hipótesis de inflación y animales de compañía, de excluir perros y gatos, de usar precios reales y de mostrar ambos modelos en el simulador. [[Confirmar y ampliar]]'],
  ['Líder (coordinación)', 'Oscar Hernandez Alomia', '[[Describir: coordinación del proyecto, gestión de accesos a SIMVET y a las ventas internas de Zoetis Colombia, revisión de las entregas y validación con el área comercial]]'],
  ['Crack (ejecución técnica)', 'Mariana Jaramillo Naranjo', '[[Describir: obtención y consolidación de las fuentes de datos (SIMVET, ventas internas, precios, IPC, PIB, población y TRM), revisión del análisis y de los modelos]]'],
], [2300, 2100, 4960], { boldFirst: true }));
kids.push(gap());
kids.push(P('El análisis, el código, el simulador y este informe se desarrollaron con apoyo de un asistente de inteligencia artificial (Claude, de Anthropic), que propuso, ejecutó y documentó bajo la dirección del equipo. Las decisiones de negocio y de tratamiento de datos las tomó el equipo: devoluciones válidas, caída de aves real, participación alta en cerdos, crecimiento nominal, exclusión de perros y gatos, precios en términos reales, uso de ambos modelos en el simulador y la consulta complementaria del examen.'));

// ------------------------------------------------------------------ Anexo A
kids.push(H1('Anexo A. Fuentes de datos (APA 7)', true));
kids.push(P('Todas las fuentes se consultaron el 18 de octubre de 2026, salvo la TRM, cuyo archivo indica descarga el 21 de octubre de 2026. Cobertura: de 2020 a 2026 (junio de 2026 para mercado y ventas).'));
const ref = (parts) => new Paragraph({ spacing: { after: 140, line: 264 }, indent: { left: 720, hanging: 720 }, children: parts });
const R = (autor, año, titulo, desc, sitio, url, fecha = 'el 18 de octubre de 2026') => ref([...runs(`${autor} (${año}). `), new TextRun({ text: titulo, italics: true }), ...runs(` ${desc} ${sitio ? sitio + ' ' : ''}${fecha ? 'Recuperado ' + fecha + ', de ' : ''}`), new TextRun({ text: url, color: '1F5FA8' })]);
kids.push(R('Banco de la República.', 's. f.', 'Tasa de cambio: Tasa Representativa del Mercado (TRM), fin de mes y promedio mensual', '[Serie histórica mensual, 2020-2026].', 'Banco de la República.', '[[completar la dirección del sistema de series estadísticas]]', 'el 21 de octubre de 2026'));
kids.push(R('Departamento Administrativo Nacional de Estadística.', 's. f.-a', 'Boletín mensual: Precios de leche cruda en finca', '[Series históricas, 2020-2026].', 'Sistema de Información de Precios y Abastecimiento del Sector Agropecuario (SIPSA).', 'https://www.dane.gov.co/index.php/estadisticas-por-tema/agropecuario/sistema-de-informacion-de-precios-sipsa/boletin-mensual-precios-de-leche-cruda-en-finca'));
kids.push(R('Departamento Administrativo Nacional de Estadística.', 's. f.-b', 'Índice de precios al consumidor (IPC): Información técnica', '[Variación mensual del IPC por ciudades, 2020-2026].', 'DANE.', 'https://www.dane.gov.co/index.php/estadisticas-por-tema/precios-y-costos/indice-de-precios-al-consumidor-ipc/ipc-informacion-tecnica'));
kids.push(R('Departamento Administrativo Nacional de Estadística.', 's. f.-c', 'Históricos del producto interno bruto (PIB): Cuentas nacionales trimestrales', '[Boletines técnicos, 2020-2026].', 'DANE.', 'https://www.dane.gov.co/index.php/estadisticas-por-tema/cuentas-nacionales/cuentas-nacionales-trimestrales/historicos-producto-interno-bruto-pib'));
kids.push(R('Euromonitor International.', 's. f.', 'Pet Healthcare: Historic growth, pet population, 2020-2026', '[Base de datos con licencia].', 'Euromonitor International, Passport.', 'https://www.portal.euromonitor.com/statisticsevolution/index'));
kids.push(R('Federación Colombiana de Ganaderos.', 's. f.', 'Precios: Ganado gordo, kilo en pie, macho de ceba', '[Datos históricos, 2020-2026].', 'Fedegán.', 'https://www.fedegan.org.co/estadisticas/precios'));
kids.push(R('Federación Nacional de Avicultores de Colombia.', 's. f.', 'Precios PEE: Huevo y pollo por kilogramo', '[Datos históricos, 2020-2026; se consideraron muslos, pierna, pechuga y pollo entero].', 'Fenavi.', 'https://fenavi.org/precios-pee/'));
kids.push(ref([...runs('Ministerio de Salud y Protección Social. (2018). '), new TextRun({ text: 'Reporte de vacunación antirrábica de perros y gatos, Colombia año 2017', italics: true }), ...runs(' [Informe en PDF, 24 páginas; última actualización: 15 de marzo de 2018]. Subdirección de Salud Ambiental. Archivo "Población Perros y Gatos 2017.pdf" del repositorio del proyecto. Consultado el 18 de octubre de 2026.')]));
kids.push(ref([...runs('Ministerio de Salud y Protección Social. (2019). '), new TextRun({ text: 'Instructivo para el diligenciamiento de los informes bimestrales de vacunación antirrábica para perros y gatos', italics: true }), ...runs(' [Informe en PDF, 35 páginas; incluye el consolidado nacional 2019 de población de perros y gatos]. Subdirección de Salud Ambiental. Archivo "Población Perros y Gatos 2019.pdf" del repositorio del proyecto. Consultado el 18 de octubre de 2026.')]));
kids.push(R('Porkcolombia.', 's. f.', 'Ronda de precios: Precio del kilo de cerdo en pie, promedio mensual', '[Datos históricos, 2020-2026].', 'Porkcolombia.', 'https://porkcolombia.co/ronda-de-precios/'));
kids.push(R('Siigo.', 's. f.', 'Salario mínimo vigente', '[Entrada de blog sobre derecho laboral; aumentos del salario mínimo legal mensual vigente, 2020-2026].', 'Siigo.', 'https://www.siigo.com/blog/derecho-laboral/salario-minimo-vigente/'));
kids.push(R('SIMVET.', 's. f.', 'Venta de productos farmacéuticos veterinarios (sell-in) reportada por 31 laboratorios, enero de 2020 a junio de 2026', '[Base de datos con licencia; descarga con cuenta; no muestra nombres de laboratorios ni de marcas].', 'Plataforma SIMVET.', 'https://plataforma-simvet.com/'));
kids.push(ref([...runs('Zoetis Colombia. (2026). '), new TextRun({ text: 'Ventas del Laboratorio por especie, segmento y subgrupo, enero de 2020 a junio de 2026', italics: true }), ...runs(' [Datos internos no publicados]. Consultado el 18 de octubre de 2026.')]));
kids.push(CAPT('Tabla A1. Correspondencia entre fuentes y variables de la base'));
kids.push(table(['Fuente', 'Variable en la base', 'Observaciones'], [
  ['SIMVET', 'Mercado; Segmento; Subgrupo', 'Sell-in de 31 laboratorios, sin nombres de laboratorios ni de marcas. Información privilegiada pero no confidencial; uso amparado por la licencia.'],
  ['Zoetis Colombia (interna)', 'Venta Laboratorio; Share Laboratorio; Compite Laboraorio', 'Ventas propias. [[Confirmar la definición de la marca "Compite"]].'],
  ['Minsalud y Euromonitor', 'Perros; Gatos', 'Población de 2019 (6.403.444 perros y 1.938.517 gatos) multiplicada por el crecimiento anual de Euromonitor, igual para ambas especies (2020: 5,34%; 2021: 5,39%; 2022: 5,00%; 2023: 1,93%; 2024: 2,88%; 2025: 3,10%; 2026: 2,27%). No se usa en el modelo.'],
  ['DANE, SIPSA (leche)', 'Precio Leche', 'COP por litro.'],
  ['Fedegán', 'Precio Carne Res', 'Precio del ganado gordo en pie (macho de ceba); en la base la variable se llama "carne res" [[confirmar]].'],
  ['Porkcolombia', 'Precio carne cerdo', 'Precio del kilo de cerdo en pie, promedio mensual.'],
  ['Fenavi', 'Precio huevo; Precio Pollo', '[[Confirmar cómo se combinaron muslos, pierna, pechuga y pollo entero en una serie, y la unidad del huevo]].'],
  ['DANE, IPC', 'IPC; Inflación Mensual', 'La fuente publica variación por ciudades; la base tiene una serie nacional [[confirmar que es el total nacional]].'],
  ['DANE, PIB', 'PIB; PIB Agro', 'Un valor por año [[confirmar si 2026 es un dato observado o un pronóstico]].'],
  ['Siigo', 'Porc Crec SMMLV', 'Fuente secundaria (blog comercial). Se recomienda verificar contra los decretos oficiales.'],
  ['Banco de la República', 'TRM (archivo aparte)', 'Evaluada como predictor; no mejoró y no entró al modelo.'],
], [2300, 2400, 4660], { boldFirst: true }));

// ------------------------------------------------------------------ Anexo B
kids.push(gap());
kids.push(H1n('Anexo B. Reproducibilidad'));
kids.push(P('Todo el análisis está en el repositorio. El orden de ejecución es el siguiente:'));
kids.push(table(['Paso', 'Script', 'Función'], [
  ['1', 'src/v2/sellar_base.py', 'Separa y sella los datos de 2026 (base y TRM); guarda huellas digitales.'],
  ['2', 'src/v2/variables.py', 'Variables de 12 meses móviles solo con datos de desarrollo.'],
  ['3', 'src/v2/desarrollo.py', 'Validación cruzada con purga, selección, umbral, curvas y diagnósticos.'],
  ['4', 'src/v2/seleccion_predictores.py, importancia.py', 'Cribado de predictores e importancia de variables con controles de ruido.'],
  ['5', 'src/v2/verificar_sello.py', 'Prueba del canario: cifras de 2026 alteradas, resultados idénticos.'],
  ['6', 'src/v2/prueba.py (una vez) y prueba_complementaria.py', 'Consulta principal y consulta complementaria del examen, con candado y registro de accesos.'],
  ['7', 'src/v2/despliegue.py, proyeccion.py, exportar_simulador.py, build_simulador.py', 'Reajuste final, proyección 2027, exportación y construcción del simulador.'],
  ['8', 'cuaderno/pipeline_completo.ipynb', 'Cuaderno que reproduce el proceso de principio a fin, con semilla 0, versiones declaradas y rutas relativas.'],
  ['9', 'informe_v2/construir_cifras.py, figuras_v2.py, construir_informe_v2.js', 'Cifras, figuras y este documento, sin cifras digitadas a mano.'],
], [800, 3900, 4660]));
kids.push(gap());
kids.push(CAPT('Referencias metodológicas'));
kids.push(ref([...runs('Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., & Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. '), new TextRun({ text: 'Journal of Machine Learning Research, 12', italics: true }), ...runs(', 2825-2830.')]));
kids.push(ref([...runs('Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schröder, B., Thuiller, W., Warton, D. I., Wintle, B. A., Hartig, F., & Dormann, C. F. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. '), new TextRun({ text: 'Ecography, 40', italics: true }), ...runs('(8), 913-929. https://doi.org/10.1111/ecog.02881')]));

// ------------------------------------------------------------------ documento
const doc = new Document({
  creator: 'Juan Cuellar Chaparro, Oscar Hernandez Alomia, Mariana Jaramillo Naranjo', title: 'Informe Técnico de Mercado Farmacéutico de Salud Animal en Colombia',
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
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: 'Borrador 2 · Página ', size: 16, color: MUTED }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: MUTED })] })] }) },
    children: kids,
  }],
});
const out = path.join(__dirname, 'Informe_Tecnico_Mercado_Farmaceutico_Salud_Animal_Colombia.docx');
Packer.toBuffer(doc).then(b => { fs.writeFileSync(out, b); console.log('ok', out, Math.round(b.length / 1024) + ' KB'); });
