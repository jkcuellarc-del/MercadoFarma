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

