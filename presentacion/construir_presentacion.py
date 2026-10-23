"""Construye la presentación de sustentación sobre la plantilla Zoetis GMS (base.pptx = plantilla con 17 diapositivas ordenadas)."""
import copy, json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION

AQUI = Path(__file__).parent
C = json.loads((AQUI.parent / "informe_v2" / "cifras.json").read_text())
OR, GR, GR2, LT, TINT = RGBColor(0xF6, 0x5C, 0x00), RGBColor(0x3A, 0x3A, 0x3A), RGBColor(0x59, 0x57, 0x56), RGBColor(0xF2, 0xF2, 0xF2), RGBColor(0xFD, 0xDE, 0xCC)
f1 = lambda x, d=1: f"{x:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")
pc = lambda x, d=1: f"{x*100:.{d}f}".replace(".", ",") + " %"

prs = Presentation(str(AQUI / "base.pptx"))
S = list(prs.slides)


def sh(slide, name_or_id):
    for s in slide.shapes:
        if s.shape_id == name_or_id: return s
    raise KeyError(name_or_id)


def fill(shape, texts, size=None, bold=None):
    """Reemplaza el texto conservando el formato de la primera corrida y del primer párrafo."""
    if isinstance(texts, str): texts = [texts]
    tf = shape.text_frame
    p0 = tf.paragraphs[0]._p
    for p in tf.paragraphs[1:]: p._p.getparent().remove(p._p)
    runs = p0.findall('{*}r')
    for r in runs[1:]: p0.remove(r)
    for b in p0.findall('{*}br'): p0.remove(b)
    for f in p0.findall('{*}fld'): p0.remove(f)
    if not runs:
        from pptx.oxml.ns import qn
        from lxml import etree
        r = etree.SubElement(p0, qn('a:r')); etree.SubElement(r, qn('a:t'))
        end = p0.find(qn('a:endParaRPr'))
        if end is not None: p0.remove(end); p0.append(end)
    for i, t in enumerate(texts):
        if i == 0: p = tf.paragraphs[0]
        else:
            newp = copy.deepcopy(p0); p0.getparent().append(newp); p = tf.paragraphs[-1]
        p.runs[0].text = t
        if size: p.runs[0].font.size = Pt(size)
        if bold is not None: p.runs[0].font.bold = bold


def rm(shape): shape._element.getparent().remove(shape._element)


def tb(slide, x, y, w, h, text, size=11, color=GR, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False):
    t = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = t.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(text if isinstance(text, list) else [text]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run(); r.text = line
        r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic; r.font.name = "Arial"; r.font.color.rgb = color
    return t


def tabla(slide, x, y, w, col_w, filas, size=10, row_h=0.27, head_size=None, bold_last=False, align=None):
    n, m = len(filas), len(filas[0])
    gf = slide.shapes.add_table(n, m, Inches(x), Inches(y), Inches(w), Inches(row_h * n))
    t = gf.table
    tblPr = t._tbl.tblPr
    for a in ('bandRow', 'firstRow'): tblPr.set(a, '0')
    sid = tblPr.find('{*}tableStyleId')
    if sid is not None: sid.text = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'  # sin estilo ni bordes
    for j, cw in enumerate(col_w): t.columns[j].width = Inches(cw)
    for i in range(n):
        t.rows[i].height = Inches(row_h)
        for j in range(m):
            c = t.cell(i, j); c.margin_left = c.margin_right = Inches(0.06); c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = c.text_frame.paragraphs[0]; r = p.add_run(); r.text = str(filas[i][j]); r.font.name = "Arial"
            r.font.size = Pt(head_size or size) if i == 0 else Pt(size)
            c.fill.solid()
            if i == 0:
                c.fill.fore_color.rgb = OR; r.font.color.rgb = RGBColor(255, 255, 255); r.font.bold = True
            else:
                c.fill.fore_color.rgb = LT if i % 2 == 0 else RGBColor(255, 255, 255); r.font.color.rgb = GR
                r.font.bold = (j == 0) or (bold_last and i == n - 1)
            if align and align[j] == 'r': p.alignment = PP_ALIGN.RIGHT
            elif align and align[j] == 'c': p.alignment = PP_ALIGN.CENTER
    return gf


def notas(slide, texto): slide.notes_slide.notes_text_frame.text = texto


def titulo(slide, shape_id, texto, size=None):
    fill(sh(slide, shape_id), texto, size=size)


def limpia_tabla_plantilla(slide):
    for s in list(slide.shapes):
        if s.has_text_frame is False and s.shape_type == 19: rm(s)       # tabla vacía
        elif s.has_text_frame and s.text_frame.text.strip() == "Lorem Ipsum": pass


# ---------------------------------------------------------------- 1 portada
s = S[0]
fill(sh(s, 5), "Proyección 2027 del mercado de salud animal en Colombia", size=34)
fill(sh(s, 6), "Zoetis Colombia  |  Sustentación del proyecto  |  Octubre de 2026")
sh(s, 6).width = Inches(7); sh(s, 6).top = Inches(2.75)
notas(s, "0:30. Saludo y objetivo: responder cuánto crecerá en 2027 el mercado de salud animal en Colombia, Zoetis y cada especie.")

# ---------------------------------------------------------------- 2 divisor 01
s = S[1]
fill(sh(s, 9), "01."); fill(sh(s, 7), "Zoetis y la decisión")
notas(s, "Transición.")

# ---------------------------------------------------------------- 3 Zoetis global
s = S[2]
fill(sh(s, 2), "ZOETIS EN EL MUNDO"); fill(sh(s, 5), "Zoetis: salud animal a escala global")
fill(sh(s, 6), "Más de 70 años cuidando animales de compañía y de producción")
stats = [("+70 años", "de historia en salud animal, desde sus orígenes como unidad de Pfizer"),
         ("2013", "se vuelve empresa independiente y cotiza en bolsa (NYSE: ZTS)"),
         ("+100 países", "donde se venden sus productos"),
         ("~45 países", "con presencia comercial directa"),
         ("~14.000", "colaboradores en el mundo"),
         ("2 líneas", "animales de compañía y animales de producción: bovinos, cerdos y aves")]
ids = [(7, 8), (9, 10), (11, 12), (13, 14), (15, 16), (17, 18)]
for (a, b), (n, d) in zip(ids, stats):
    fill(sh(s, a), n); fill(sh(s, b), d, size=11)
notas(s, "0:45. Zoetis es una multinacional de salud animal con más de 70 años de historia, independiente desde 2013, con productos en más de 100 países. "
         "Cifras aproximadas tomadas de documentos públicos de la compañía (10-K); confirmar contra el informe anual vigente antes de la sustentación.")

# ---------------------------------------------------------------- 4 portafolio Colombia
s = S[3]
fill(sh(s, 17), "ZOETIS COLOMBIA"); fill(sh(s, 16), "Portafolio de Zoetis en Colombia")
fill(sh(s, 20), "Cuatro especies, cada una con sus segmentos farmacéuticos")
cols = [(19, 18, "Animales de compañía", ["Perros y gatos", "6 segmentos farmacéuticos en la base de mercado"]),
        (22, 24, "Ganadería", ["Bovinos de carne y de leche", "5 segmentos farmacéuticos"]),
        (25, 27, "Porcicultura", ["Cerdos", "2 segmentos: antimicrobianos y vacunas", "Zoetis lidera este mercado"]),
        (28, 30, "Avicultura", ["Pollos", "1 segmento: vacunas"])]
for h, b, t, ls in cols:
    fill(sh(s, h), t); fill(sh(s, b), ls, size=12)
from pptx.oxml.ns import qn
for k, (x0, nombre) in enumerate(((0.36, "ca"), (2.72, "ganado"), (5.08, "cerdos"), (7.44, "aves"))):
    pic = s.shapes.add_picture(str(AQUI / f"img_{nombre}.jpg"), Inches(x0), Inches(1.72), Inches(2.23), Inches(3.39))
    blip = pic._element.find('.//' + qn('a:blip')); am = blip.makeelement(qn('a:alphaModFix'), {'amt': '28000'}); blip.append(am)
    pic.name = f"Imagen de fondo {nombre}"
    s.shapes._spTree.remove(pic._element); s.shapes._spTree.insert(2, pic._element)   # detrás del texto
notas(s, "0:45. En Colombia, Zoetis ofrece portafolio para animales de compañía, ganadería (bovinos), porcicultura y aves. Es el líder del mercado en cerdos.")

# ---------------------------------------------------------------- 5 decisión
s = S[4]
fill(sh(s, 47), "LA DECISIÓN"); fill(sh(s, 46), "Una pregunta para planear 2027")
filas = [("¿Cuánto crecerá en 2027?", "Predecir si 2027 será un año regular (crece menos de 8 %), estable (de 8 % a 15 %) u optimista (más de 15 %), para el mercado de salud animal, Zoetis y cada especie."),
         ("Plan financiero", "Metas de ventas y presupuesto de 2027 por especie."),
         ("Forecast", "Referencia para planear inventario y producción."),
         ("Cuota de comisiones", "Metas razonables para el equipo comercial."),
         ("Acuerdos comerciales con distribuidores", "Metas y condiciones acordes con el crecimiento esperado del mercado.")]
for (hid, bid), (h, b) in zip([(53, 48), (54, 49), (55, 50), (56, 51), (57, 52)], filas):
    fill(sh(s, hid), h, size=12); fill(sh(s, bid), b, size=12)
notas(s, "1:00. La pregunta nace de una decisión real: el plan financiero, el forecast, la cuota de comisiones y los acuerdos con distribuidores dependen de cuánto crezca el mercado.")

# ---------------------------------------------------------------- 6 divisor 02
s = S[5]
fill(sh(s, 5), "02."); fill(sh(s, 2), "Datos reales")
fill(sh(s, 8), "Fuentes y variables")

# ---------------------------------------------------------------- 7 datos
s = S[6]
fill(sh(s, 47), "DATOS REALES"); fill(sh(s, 46), "Datos reales usados en el proyecto")
filas = [("Mercado", "SIMVET: ventas (sell-in) de 31 laboratorios por especie, segmento y subgrupo; enero de 2020 a junio de 2026."),
         ("Precios en pie, leche, pollo y huevo", "Ganado gordo, cerdo y pollo en pie; leche cruda y huevo (Fedegán, Porkcolombia, Fenavi, DANE)."),
         ("Animales en hogares", "Perros y gatos: población de Minsalud y crecimiento de Euromonitor."),
         ("Economía", "PIB y PIB agropecuario, IPC e inflación (DANE), salario mínimo (SMMLV) y TRM (Banco de la República)."),
         ("Laboratorio", "Ventas internas de Zoetis Colombia y su participación en el mercado.")]
for (hid, bid), (h, b) in zip([(53, 48), (54, 49), (55, 50), (56, 51), (57, 52)], filas):
    fill(sh(s, hid), h, size=12); fill(sh(s, bid), b, size=12)
notas(s, "0:45. Cinco grupos de datos. La TRM se probó y no mostró señal. Fuentes completas en el Anexo A del informe.")

# ---------------------------------------------------------------- 8 tabla de columnas
s = S[7]
rm(sh(s, 15))
fill(sh(s, 11), "Columnas de la base y celdas vacías"); sh(s, 11).width = Inches(9.26)
t = sh(s, 6); fill(t, "8.268 filas, de enero de 2020 a junio de 2026. Los precios y la población de perros y gatos aplican a una sola especie: sus vacíos son por diseño."); t.width = Inches(9.2); t.top = Inches(1.05); t.height = Inches(0.4)
for r in t.text_frame.paragraphs[0].runs: r.font.size = Pt(12)
corto = lambda x: x.split(' (')[0].replace('Entera', 'Entera').replace('Fracción', 'Fracción')
fich = [r for r in C["ficha"] if r["columna"] != "Compite Laboraorio"]
def fila(r): return [r["columna"], corto(r["tipo"]), f'{r["faltantes"]:,}'.replace(",", ".") + (f' ({f1(r["pct"], 0)} %)' if r["faltantes"] else '')]
mitad = (len(fich) + 1) // 2
for k, grupo in enumerate((fich[:mitad], fich[mitad:])):
    tabla(s, 0.4 + k * 4.7, 1.55, 4.5, [1.75, 1.35, 1.4], [["Columna", "Tipo", "Vacías"]] + [fila(r) for r in grupo], size=10, row_h=0.26, align=['l', 'l', 'r'])
notas(s, "0:45. Resumen de las columnas. Los vacíos de precios (68 % a 85 %) y de perros y gatos (70 %) son estructurales. El crecimiento del Laboratorio está vacío antes de tener 12 meses de venta.")

# ---------------------------------------------------------------- 9 divisor 03
s = S[8]
fill(sh(s, 3), "03."); fill(sh(s, 7), "Modelos y evaluación")

# ---------------------------------------------------------------- 9b aprendizaje supervisado + partición
s = S[9]
rm(sh(s, 15))
fill(sh(s, 11), "Aprendizaje supervisado"); sh(s, 11).width = Inches(9.26)
t = sh(s, 6); fill(t, "El modelo aprende de ejemplos históricos donde ya se conoce la respuesta."); t.width = Inches(9.2); t.top = Inches(1.05); t.height = Inches(0.35)
for r in t.text_frame.paragraphs[0].runs: r.font.size = Pt(12)
bt = tb(s, 0.4, 1.55, 9.2, 1.5, ["Es un problema de regresión supervisada: el modelo predice un número, el crecimiento nominal de las ventas de 12 meses.",
                                  "Columnas objetivo: el crecimiento del mercado (por especie) y el crecimiento de las ventas del Laboratorio.",
                                  "Con la proyección se clasifica el año 2027: regular (menos de 8 %), estable (8 % a 15 %) u optimista (más de 15 %)."], size=13, color=GR)
for p in bt.text_frame.paragraphs:
    p.space_after = Pt(6)
    pPr = p._p.get_or_add_pPr(); pPr.set('marL', '171450'); pPr.set('indent', '-171450')
    from pptx.oxml.ns import qn as _qn
    bu = pPr.makeelement(_qn('a:buChar'), {'char': '•'}); pPr.append(bu)
tb(s, 0.4, 3.1, 9.2, 0.25, "Partición de los datos (por mes t de la ventana de 12 meses)", size=12, color=OR, bold=True)
TMs, TLs = C["tareas"]["mercado"]["seleccion"], C["tareas"]["lab_ym"]["seleccion"]
filas = [["Conjunto", "Periodo (mes t)", "Mercado (filas)", "Laboratorio (filas)", "Uso"],
         ["Entrenamiento", "Mercado: dic-2021 a dic-2025. Laboratorio: dic-2023 a dic-2025", str(TMs["n_train"]), str(TLs["n_train"]), "Validación cruzada, ajuste de hiperparámetros y selección"],
         ["Examen", "ene-2026 a jun-2026", "24", "24", "Consulta principal y una consulta complementaria"]]
tabla(s, 0.4, 3.45, 9.2, [1.4, 2.7, 1.25, 1.35, 2.5], filas, size=11, row_h=0.5, align=['l', 'l', 'r', 'r', 'l'])
notas(s, "1:00. Aprendizaje supervisado de regresión: se entrena con crecimientos pasados conocidos. Las columnas objetivo son el crecimiento del mercado y el de las ventas del Laboratorio. Entrenamiento hasta diciembre de 2025 y examen sellado de enero a junio de 2026.")

# ---------------------------------------------------------------- 9c variables importantes
s = S[10]
rm(sh(s, 15))
fill(sh(s, 11), "Variables importantes"); sh(s, 11).width = Inches(9.26)
t = sh(s, 6); fill(t, "Importancia por permutación (Gradient Boosting): cuánto sube el error en puntos porcentuales al barajar cada variable."); t.width = Inches(9.2); t.top = Inches(1.05); t.height = Inches(0.4)
for r in t.text_frame.paragraphs[0].runs: r.font.size = Pt(12)
imp = lambda tarea, v: next((r for r in C["importancia"] if r["tarea"] == tarea and r["conjunto"] == "S7_real_trm" and r["variable"] == v), None)
iv = lambda tarea, v: imp(tarea, v)["perm_gbm_pp"] if imp(tarea, v) else 0
ctl = lambda tarea: max(r["perm_gbm_pp"] for r in C["importancia"] if r["tarea"] == tarea and r["conjunto"] == "S7_real_trm" and r["es_control"])
d2 = lambda x: f1(x, 2)
filas = [["Variable", "Mercado (pp)", "Laboratorio (pp)"],
         ["Precio real del cerdo en pie", d2(iv("mercado", "real_var_cerdo")), d2(iv("lab", "real_var_cerdo"))],
         ["Precio real del huevo", d2(iv("mercado", "real_var_huevo")), d2(iv("lab", "real_var_huevo"))],
         ["Precio real del ganado en pie", d2(iv("mercado", "real_var_res")), d2(iv("lab", "real_var_res"))],
         ["Inflación de animales de compañía", d2(iv("mercado", "ipc_yoy_CA")), d2(iv("lab", "ipc_yoy_CA"))],
         ["Crecimiento del mercado donde compite", "–", d2(iv("lab", "y_compite"))],
         ["PIB, PIB agropecuario, salario mínimo e inflación", "≈ 0,00", "≈ 0,00 a 0,03"],
         ["TRM (tres variables)", "≈ 0,00", d2(max(iv("lab", "trm_yoy12"), iv("lab", "trm_yoy12_l6"), iv("lab", "trm_yoy12_l12")))],
         ["Mayor control de ruido", f1(ctl("mercado"), 3), f1(ctl("lab"), 3)]]
tabla(s, 0.4, 1.65, 9.2, [5.0, 2.1, 2.1], filas, size=11, row_h=0.35, align=['l', 'r', 'r'])
tb(s, 0.4, 4.9, 9.2, 0.25, "Una variable cuenta solo si supera al mayor control de ruido (tres columnas de números al azar).", size=10, color=GR2)
notas(s, "1:00. Los precios reales del cerdo y del huevo, y la inflación de animales de compañía, son las únicas variables que superan al ruido. PIB, salario mínimo y TRM no aportan señal.")

# ---------------------------------------------------------------- 10 tabla de 5 modelos
s = S[11]
rm(sh(s, 15))
fill(sh(s, 11), "Cinco modelos comparados en validación"); sh(s, 11).width = Inches(9.26)
t = sh(s, 6); fill(t, "Error medio absoluto (MAE, en puntos porcentuales) en validación cruzada por bloques de tiempo, antes de abrir la prueba de 2026."); t.width = Inches(9.2); t.top = Inches(1.05); t.height = Inches(0.4)
for r in t.text_frame.paragraphs[0].runs: r.font.size = Pt(12)
cm = {m: v for m, v in C["tareas"]["mercado"]["seleccion"]["mejores"].items()}
cl = {m: v for m, v in C["tareas"]["lab_ym"]["seleccion"]["mejores"].items()}
filas = [["Modelo", "Parámetros en el mercado", "Parámetros en el Laboratorio", "MAE mercado", "MAE Laboratorio"],
         ["Regresión lineal (base)", "Sin parámetros", "Sin parámetros", f1(cm["ols"]["MAE_cv"]), f1(cl["ols"]["MAE_cv"])],
         ["Modelo A: Elastic Net (mercado) y Ridge por especie (Laboratorio)", "alfa 0,1; mezcla L1 0,5", "alfa 10", f1(cm["enet"]["MAE_cv"]), f1(cl["ridge_esp"]["MAE_cv"])],
         ["K vecinos más cercanos", "12 vecinos; distancia L2; pesos iguales", "3 vecinos; distancia L1; pesos por distancia", f1(cm["knn"]["MAE_cv"]), f1(cl["knn"]["MAE_cv"])],
         ["Random Forest", "300 árboles; profundidad 2; 50 % de variables; hoja mínima 3", "300 árboles; profundidad 8; 50 % de variables; hoja mínima 3", f1(cm["rf"]["MAE_cv"]), f1(cl["rf"]["MAE_cv"])],
         ["Modelo B: Gradient Boosting", "50 iteraciones; tasa 0,03; profundidad 3; hoja mínima 8", "400 iteraciones; tasa 0,03; profundidad 3; hoja mínima 3", f1(cm["gbm"]["MAE_cv"]), f1(cl["gbm"]["MAE_cv"])]]
tabla(s, 0.4, 2.25, 9.2, [2.5, 2.35, 2.35, 1.0, 1.0], filas, size=10, row_h=0.42, align=['l', 'l', 'l', 'r', 'r'])
tb(s, 0.4, 1.55, 9.2, 0.7, [f'Los datos se partieron por año: entrenamiento de 2020 a 2025 (9 pliegues de 6 meses con purga) y examen sellado de enero a junio de 2026. Los parámetros se eligieron por búsqueda en rejilla dentro de la validación, sin mirar 2026. Líneas base: promedio de la especie ({f1(C["tareas"]["mercado"]["seleccion"]["base_B2"])} y {f1(C["tareas"]["lab_ym"]["seleccion"]["base_B2"])}) y crecimiento del año anterior ({f1(C["tareas"]["mercado"]["seleccion"]["base_B1"])} y {f1(C["tareas"]["lab_ym"]["seleccion"]["base_B1"])}).'], size=11, color=GR2)
notas(s, "1:30. Cinco de los diez modelos probados, con sus parámetros elegidos y el error en validación. El modelo A salió elegido por la regla declarada de antemano (más simple dentro de un error estándar del mejor). "
         "La regresión lineal sin regularizar se sobreajusta (13 puntos de error en el mercado).")

# ---------------------------------------------------------------- 11 resultados del examen
s = S[12]
rm(sh(s, 15))
fill(sh(s, 11), "Resultado en el examen de 2026"); sh(s, 11).width = Inches(9.26)
t = sh(s, 6); fill(t, "Seis meses sellados, de enero a junio de 2026: error medio absoluto en puntos porcentuales (menor es mejor)."); t.width = Inches(9.2); t.top = Inches(1.05); t.height = Inches(0.4)
for r in t.text_frame.paragraphs[0].runs: r.font.size = Pt(12)
cmp_ = C["comparacion"]
nombres = ["Modelo A", "Modelo B", "K vecinos", "Random Forest", "Regresión lineal", "Promedio de la especie", "Año anterior"]
order = [0, 1, 2, 3, 4, 5, 6]
def chart(slide, x, y, w, h, titulo_, key):
    cd = CategoryChartData(); cd.categories = nombres[::-1]
    cd.add_series(titulo_, [round(cmp_[i][key], 1) for i in order][::-1])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart; ch.has_legend = False; ch.has_title = True
    ch.chart_title.text_frame.text = titulo_
    r = ch.chart_title.text_frame.paragraphs[0].runs[0]; r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = OR; r.font.name = "Arial"
    pl = ch.plots[0]; pl.gap_width = 50; pl.has_data_labels = True
    dl = pl.data_labels; dl.font.size = Pt(10); dl.font.name = "Arial"; dl.font.color.rgb = GR; dl.number_format = '0.0'; dl.number_format_is_linked = False; dl.position = XL_LABEL_POSITION.OUTSIDE_END
    ser = pl.series[0]
    for k, nm in enumerate(nombres[::-1]):
        pt = ser.points[k]; pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = RGBColor(0x91, 0x9C, 0x80) if nm in ("Promedio de la especie", "Año anterior") else OR
    ca = ch.category_axis; ca.tick_labels.font.size = Pt(10); ca.tick_labels.font.name = "Arial"; ca.tick_labels.font.color.rgb = GR; ca.format.line.color.rgb = RGBColor(0xBF, 0xBF, 0xBF)
    va = ch.value_axis; va.visible = False; va.has_major_gridlines = False; va.maximum_scale = 18; va.minimum_scale = 0
chart(s, 0.35, 1.5, 4.6, 3.2, "Mercado", "ex_mercado")
chart(s, 5.05, 1.5, 4.6, 3.2, "Laboratorio", "ex_lab")
tb(s, 0.4, 4.75, 9.2, 0.5, "Naranja: modelos; verde: métodos sencillos de comparación. K vecinos, Random Forest y regresión lineal se midieron en una segunda consulta posterior, solo informativa, que no se usó para elegir modelo.", size=10, color=GR2)
notas(s, "1:30. Con el examen sellado de enero a junio de 2026, el modelo A no superó a los métodos sencillos en el mercado (9,2 frente a 8,7 y 8,4). "
         "El modelo B, Gradient Boosting, tuvo menor error (7,2 y 3,7), pero se incorporó después de ver el examen, por lo que su error real puede ser mayor. "
         "K vecinos, Random Forest y regresión lineal se midieron después, en una consulta solo informativa.")

# ---------------------------------------------------------------- 12 lectura de resultados
s = S[13]
fill(sh(s, 2), "LECTURA DE LOS RESULTADOS"); fill(sh(s, 5), "Qué nos dicen los resultados")
fill(sh(s, 6), "Las variables explican poco: el resultado es un rango")
P = C["prueba"]
stats = [(f'{f1(P["mercado"]["MAE_pp"])} pp', f'Modelo A en el mercado: no mejora al promedio de la especie ({f1(P["mercado"]["B2_media_especie"]["MAE_pp"])} pp)'),
         (f'{f1(P["mercado"]["alternativa_mejor_cv"]["MAE_pp"])} pp', 'Modelo B en el mercado: menor error, pero se incorporó después del examen'),
         (f'{f1(P["lab_ym"]["MAE_pp"])} pp', f'Modelo A en el Laboratorio: mejora al año anterior ({f1(P["lab_ym"]["B1_crecimiento_hace_12m"]["MAE_pp"])} pp), no al promedio ({f1(P["lab_ym"]["B2_media_especie"]["MAE_pp"])} pp)'),
         (f'{f1(P["lab_ym"]["alternativa_mejor_cv"]["MAE_pp"])} pp', 'Modelo B en el Laboratorio: el menor error de los dos modelos'),
         ("±5 pp", "Error típico de la proyección total, en el mercado y en el Laboratorio"),
         ("Aves", "La especie más difícil: el mercado cayó cerca de 20 % y los modelos proyectaban alza")]
for (a, b), (n, d) in zip(ids, stats):
    fill(sh(s, a), n); fill(sh(s, b), d, size=11)
notas(s, "0:45. Lectura honesta: las variables económicas y de precios explican poco del crecimiento. Por eso se presentan dos modelos como rango y se declara un margen de error de unos 5 puntos.")

# ---------------------------------------------------------------- 13 divisor 04
s = S[14]
num = copy.deepcopy(sh(S[8], 3)._element)
s.shapes._spTree.append(num)
fill([x for x in s.shapes if x.has_text_frame and x.text_frame.text == "03."][0], "04.")
fill(sh(s, 16), "Despliegue y decisiones")

# ---------------------------------------------------------------- 14 simulador
s = S[15]
fill(sh(s, 11), "DESPLIEGUE DEL MODELO"); fill(sh(s, 5), "Simulador web del crecimiento 2027")
fill(sh(s, 12), "Dos modelos, un rango, por especie")
b = sh(s, 13); b.left = Inches(0.37); b.top = Inches(1.7); b.width = Inches(3.9); b.height = Inches(3.3)
fill(b, ["Se mueven la inflación, el PIB, el salario mínimo y los precios en pie, de leche, huevo y pollo.",
         "Los controles generales mueven todas las especies.",
         "Muestra el crecimiento 2027 del mercado y de Zoetis, con su escenario: regular, estable u optimista.",
         "Los modelos A y B corren en el navegador y el resultado es un rango."], size=13)
pic = s.shapes.add_picture(str(AQUI / "sim_crop.png"), Inches(4.45), Inches(1.45), width=Inches(5.2))
pic.line.color.rgb = RGBColor(0xBF, 0xBF, 0xBF)
notas(s, "0:45. Demostración: mover la inflación o el precio del cerdo y mostrar cómo cambian el rango y el escenario por especie. Se publica como página web (GitHub Pages o artefacto).")

# ---------------------------------------------------------------- 15 proyección
s = S[16]
rm(sh(s, 15))
fill(sh(s, 11), "Proyección 2027 por especie"); sh(s, 11).width = Inches(9.26)
t = sh(s, 6); fill(t, "Crecimiento nominal de 2027 frente a 2026: rango entre el modelo A y el modelo B."); t.width = Inches(9.2); t.top = Inches(1.05); t.height = Inches(0.4)
for r in t.text_frame.paragraphs[0].runs: r.font.size = Pt(12)
A = {r["Especie"]: r for r in C["proy"]["A"]}; B = {r["Especie"]: r for r in C["proy"]["B"]}
esp = {"CA": "Animales de compañía", "Cattle": "Bovinos", "Swine": "Cerdos", "Poultry": "Aves", "Total": "Total ponderado"}
def rng(k, key):
    v = sorted([A[k][key], B[k][key]]); return f'{f1(v[0]*100+1e-9)} % a {f1(v[1]*100+1e-9)} %' if abs(v[0]-v[1]) > 0.0005 else f'{f1(v[0]*100+1e-9)} %'
def esc(k, key):
    e = {A[k][key], B[k][key]}; o = ["regular", "estable", "optimista"]
    e = sorted(e, key=o.index); return e[0].capitalize() if len(e) == 1 else f'{e[0].capitalize()} a {e[-1]}'
filas = [["Especie", "Mercado", "Escenario", "Zoetis", "Escenario"]]
for k in ("CA", "Cattle", "Swine", "Poultry", "Total"):
    filas.append([esp[k], rng(k, "crec_mercado"), esc(k, "escenario_mercado"), rng(k, "crec_lab"), esc(k, "escenario_lab")])
tabla(s, 0.4, 1.6, 9.2, [2.4, 1.8, 1.6, 1.8, 1.6], filas, size=12, row_h=0.45, bold_last=True, align=['l', 'r', 'l', 'r', 'l'])
tb(s, 0.4, 4.45, 9.2, 0.7, "Escenarios: regular, menor de 8 %; estable, de 8 % a 15 %; optimista, mayor de 15 %. Supuesto: precios de julio a diciembre de 2026 iguales a los de junio. Error típico del total: unos 5 puntos porcentuales.", size=10, color=GR2)
notas(s, "1:30. El mercado crecería entre 13,7 % y 15,4 % en 2027 y Zoetis entre 20,6 % y 22,3 %. Por especie, cerdos es la de mayor crecimiento y bovinos la de menor para Zoetis (cerca de 5 %).")

# ---------------------------------------------------------------- 16 decisiones
s = S[17]
fill(sh(s, 18), "DECISIONES Y RECOMENDACIONES"); fill(sh(s, 14), "Qué hacer con este resultado")
fill(sh(s, 5), "Mercado: +13,7 % a +15,4 %. Zoetis: +20,6 % a +22,3 % en 2027", size=18)
tx = [(34, 35, "Usarlo como rango", "Para el plan financiero, el forecast, las comisiones y los acuerdos con distribuidores: referencia con rango, no compromiso ni cifra única."),
      (36, 37, "Conocer sus límites", "Error típico de unos 5 puntos. Aves y bovinos son los más inciertos. No sirve como alarma de bajo crecimiento."),
      (38, 39, "Revalidar en 2027", "Probar el modelo B con los datos de julio a diciembre de 2026 y alimentarlo con pronósticos oficiales de IPC y PIB.")]
for h, b, ht, bt in tx:
    fill(sh(s, h), ht); fill(sh(s, b), bt, size=12)
notas(s, "1:30. Respuesta a la pregunta: el mercado crecería entre 13,7 % y 15,4 % y Zoetis entre 20,6 % y 22,3 % en 2027. "
         "Recomendaciones: usar el rango como referencia, conocer sus límites y revalidar en el primer trimestre de 2027 con los datos de julio a diciembre de 2026.")

# ---------------------------------------------------------------- 17 equipo
s = S[18]
fill(sh(s, 20), "EQUIPO DEL PROYECTO"); fill(sh(s, 19), "Equipo del proyecto")
mem = [(22, 23, 27, "Juan Cuellar Chaparro", "Jefe", "Patrocinio y decisión"), (28, 29, 30, "Oscar Hernandez Alomia", "Líder", "Coordinación"),
       (31, 32, 33, "Mariana Jaramillo Naranjo", "Crack", "Ejecución técnica")]
for n_, r_, b_, nombre, rol, desc in mem:
    fill(sh(s, n_), nombre); fill(sh(s, r_), f"{rol}, Zoetis Colombia"); fill(sh(s, b_), desc)
for i in (39, 34, 35, 36): rm(sh(s, i))
for x_, n_, r_, b_ in ((2.36, 22, 23, 27), (4.21, 28, 29, 30), (6.10, 31, 32, 33)):
    for sid, y_, h_ in ((n_, 2.61, 0.45), (r_, 3.1, 0.3), (b_, 3.45, 0.8)):
        e = sh(s, sid); e.left, e.top, e.width, e.height = Inches(x_), Inches(y_), Inches(1.65), Inches(h_)
    sh(s, n_).text_frame.vertical_anchor = MSO_ANCHOR.TOP
    for r in sh(s, n_).text_frame.paragraphs[0].runs: r.font.size = Pt(12)
tb(s, 7.95, 1.55, 1.7, 1.0, "¡Gracias!", size=28, color=OR, bold=True)
tb(s, 7.95, 2.35, 1.7, 0.8, "Preguntas y comentarios", size=14, color=GR)
notas(s, "0:30. Cierre y preguntas. Tiempo total estimado: 15 minutos.")

for sl in prs.slides:
    for x in sl.shapes:
        if x.has_text_frame and x.text_frame.text.strip() == "Presentation Name or Footer Copy":
            x.text_frame.paragraphs[0].runs[0].text = "Proyección 2027 | Zoetis Colombia"
            for r in x.text_frame.paragraphs[0].runs[1:]: r.text = ""
prs.save(str(AQUI / "Sustentacion_Proyeccion_2027_Zoetis_Colombia.pptx"))
print("ok")
