"""Genera el spitch de 15 minutos por diapositiva (docx) a partir de Sustentacion_Proyecto_ML1.pptx."""
import sys, subprocess
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

AQUI = Path(__file__).parent
IMG = Path(sys.argv[1])                      # carpeta con s-01.jpg ... s-19.jpg
SALIDA = AQUI / "Spitch_Sustentacion_Proyecto_ML1.docx"
OR = RGBColor(0xF6, 0x5C, 0x00); GR = RGBColor(0x3A, 0x3A, 0x3A); GR2 = RGBColor(0x59, 0x57, 0x56)

# (título de la diapositiva, tiempo objetivo en segundos, texto del spitch en párrafos)
S = [
 ("Proyección 2027 del mercado de salud animal en Colombia", 30, [
  "Buenos días. Somos el equipo de Zoetis Colombia: Juan Cuellar, Oscar Hernández y Mariana Jaramillo.",
  "Hoy les contamos cómo construimos un modelo de aprendizaje automático para responder una pregunta concreta: ¿cuánto va a crecer en 2027 el mercado de salud animal en Colombia, cuánto va a crecer Zoetis y cuánto va a crecer cada especie?",
  "Veremos de dónde salen los datos, qué modelos probamos, qué resultados tuvimos y qué decisiones recomendamos.",
  "Nuestro objetivo es que, al terminar, tengan claro qué podemos decir sobre 2027 y qué no."]),
 ("01. Zoetis y la decisión", 10, [
  "Empecemos por el contexto: quién es Zoetis y qué decisión necesitamos apoyar."]),
 ("Zoetis: Zoe, palabra griega que significa vida", 45, [
  "El nombre Zoetis viene de “zoe”, una palabra griega que significa vida. Es el líder mundial en salud animal, con ventas cercanas a 9.500 millones de dólares.",
  "Tiene más de 75 años de historia. Nació como la unidad de salud animal de Pfizer y, desde 2013, es una empresa independiente que cotiza en la bolsa de Nueva York.",
  "Vende sus productos en más de 100 países, tiene presencia comercial directa en unos 45 y cerca de 14.500 colaboradores.",
  "Trabaja en dos líneas: animales de compañía y animales de producción, como bovinos, caballos, cerdos, ovejas, aves y peces."]),
 ("Portafolio de Zoetis en Colombia", 45, [
  "En Colombia, Zoetis tiene portafolio para cuatro especies.",
  "Animales de compañía, es decir, perros y gatos, con seis segmentos farmacéuticos. Ganadería, con bovinos de carne y de leche, con cinco segmentos. Porcicultura, con cerdos, donde hay dos segmentos, antimicrobianos y vacunas, y Zoetis lidera el mercado. Y avicultura, con pollos de engorde y ponedoras, donde el segmento es vacunas.",
  "En total, los segmentos son: antimicrobianos, parasiticidas, dolor, derma, hormonales, vacunas y otros fármacos."]),
 ("Una pregunta para planear 2027", 50, [
  "La compañía necesita saber cómo se comportará el mercado en 2027. La idea es predecir si 2027 será un año regular, estable u optimista.",
  "Regular significa que el mercado crece menos de 8 %. Estable, entre 8 % y 15 %. Optimista, más de 15 %.",
  "Esa respuesta apoya cuatro decisiones. El plan financiero, con metas de ventas y presupuesto por especie. El forecast, para planear inventario y producción. La cuota de comisiones, para poner metas razonables al equipo comercial. Y los acuerdos comerciales con distribuidores, con condiciones acordes al crecimiento esperado del mercado.",
  "Si el mercado crece poco, las metas deben ser prudentes. Si crece mucho, hay que preparar más inventario y producción. Por eso necesitamos una señal clara, aunque sea un rango."]),
 ("02. Datos reales", 10, [
  "Pasemos a los datos que usamos."]),
 ("Datos reales usados en el proyecto", 50, [
  "Usamos cinco grupos de datos reales.",
  "Primero, el mercado. La plataforma SIMVET nos da las ventas “sell-in”, es decir, lo que los laboratorios venden al canal. Son 31 laboratorios, por especie y segmento, de enero de 2020 a junio de 2026.",
  "Segundo, los precios: ganado gordo y cerdo en pie, pollo, leche cruda y huevo, de Fedegán, Porkcolombia, Fenavi y el DANE.",
  "Tercero, los animales en hogares: la población de perros y gatos de Minsalud y su crecimiento según Euromonitor.",
  "Cuarto, la economía: PIB, PIB agropecuario, inflación, salario mínimo y TRM.",
  "Y quinto, las ventas internas de Zoetis Colombia y su participación en el mercado.",
  "Los datos de mercado y de ventas llegan hasta junio de 2026. Para los precios de julio a diciembre de 2026 supusimos que se quedan iguales a los de junio."]),
 ("Columnas de la base y celdas vacías", 45, [
  "Esta tabla resume las columnas de la base: 8.268 filas, de enero de 2020 a junio de 2026.",
  "Las columnas de especie, segmento, mercado, economía y ventas del laboratorio están completas.",
  "Los vacíos que ven son de diseño. Cada precio aplica solo a una especie: la leche y el ganado, a bovinos; el cerdo, a cerdos; el huevo y el pollo, a aves. Lo mismo pasa con perros y gatos, que solo aplica a animales de compañía.",
  "Y el crecimiento del laboratorio está vacío al inicio, porque necesita 12 meses de ventas para poder calcularse.",
  "No rellenamos esos vacíos con números inventados, porque no son datos perdidos."]),
 ("03. Modelos y evaluación", 10, [
  "Ahora veamos los modelos y cómo los evaluamos."]),
 ("Aprendizaje supervisado", 60, [
  "Usamos aprendizaje supervisado. Eso quiere decir que el modelo aprende de ejemplos del pasado en los que ya conocemos la respuesta.",
  "Aquí la respuesta es un número: el crecimiento de las ventas de los últimos 12 meses. Por eso es un problema de regresión. Tenemos dos columnas objetivo: el crecimiento del mercado y el crecimiento de las ventas del laboratorio. Con ese número clasificamos 2027 como regular, estable u optimista.",
  "Para no engañarnos, partimos los datos por fecha. El entrenamiento usa 196 filas del mercado y 100 del laboratorio, hasta diciembre de 2025. El examen son 24 filas, de enero a junio de 2026. Esos datos los guardamos sellados y no los usamos para entrenar ni para ajustar los modelos.",
  "Además, trabajamos con 12 meses móviles: cada fila compara los últimos 12 meses con los 12 meses anteriores. Así, el dato de diciembre de 2027 es el crecimiento anual de 2027, que es justo lo que queremos proyectar."]),
 ("Variables importantes", 60, [
  "Antes de modelar quisimos saber qué variables importan. Usamos la importancia por permutación: se baraja una variable y se mide cuánto empeora el error del modelo. Si casi no cambia, la variable no aporta. Como referencia agregamos columnas de números al azar: una variable solo cuenta si supera al azar.",
  "En el mercado, lo que más pesa es el precio real del cerdo en pie, con 0,40 puntos porcentuales. En el laboratorio pesan más el precio del huevo, con 0,61, y el crecimiento del mercado donde compite, con 0,24. La inflación de animales de compañía también aporta algo.",
  "El PIB, el salario mínimo y la TRM casi no aportan. Y “pp” significa puntos porcentuales.",
  "Esto nos dice dónde está la información. En el simulador, el efecto de cada variable es pequeño, y eso es coherente con esta tabla."]),
 ("Cinco modelos comparados en validación", 90, [
  "Probamos diez modelos y aquí mostramos cinco. El error se mide con el MAE: el promedio de cuántos puntos porcentuales se equivoca el modelo. Menor es mejor. Estos resultados son de validación, antes de abrir el examen.",
  "La regresión lineal simple es la base y se equivoca mucho, 13 puntos en el mercado, porque se ajusta demasiado al pasado.",
  "El modelo A usa Elastic Net en el mercado y Ridge por especie en el laboratorio. Son modelos lineales con penalización, más estables: 4,6 y 5,4. K vecinos tuvo 4,3 y 6,0. Random Forest, 4,5 y 5,8. Y Gradient Boosting, el modelo B, fue el mejor en validación: 4,2 y 5,3.",
  "Para comparar, hay dos métodos sencillos: el promedio de la especie, con 5,1 y 6,1, y repetir el crecimiento del año anterior, con 5,8 y 7,9.",
  "Elegimos el modelo A con una regla fijada antes de ver el examen: entre los modelos con error parecido al mejor, se escoge el más simple. Los parámetros se eligieron dentro de la validación, sin mirar 2026.",
  "Para ubicarnos: K vecinos mira los casos más parecidos del pasado. Random Forest y Gradient Boosting construyen muchas reglas de decisión y las combinan."]),
 ("Resultado en el examen de 2026", 90, [
  "Aquí está el examen, de enero a junio de 2026: datos que el modelo nunca vio.",
  "En el mercado, el modelo A tuvo 9,2 puntos de error. Es peor que el promedio de la especie, con 8,7, y que repetir el año anterior, con 8,4. No superó a los métodos sencillos. En el laboratorio, el modelo A tuvo 4,4: mejora al año anterior, con 6,3, pero no al promedio de la especie, con 4,1.",
  "El modelo B, Gradient Boosting, tuvo menos error: 7,2 en el mercado y 3,7 en el laboratorio. Pero hay que ser claros: lo incorporamos después de ver el examen, así que su error real podría ser mayor.",
  "K vecinos, Random Forest y regresión lineal también aparecen. K vecinos tuvo 5,9 en el mercado y Random Forest 3,6 en el laboratorio. Los medimos después, en una consulta solo informativa, y no los usamos para elegir. Si eligiéramos el mejor del examen, el examen dejaría de ser una prueba honesta.",
  "Los errores del examen son más altos que los de validación en el mercado, y buena parte viene de aves, donde el mercado se comportó distinto de lo que los modelos esperaban."]),
 ("Qué nos dicen los resultados", 45, [
  "¿Qué nos dicen estos resultados? Que las variables explican poco del crecimiento.",
  "El modelo A se equivoca 9,2 puntos en el mercado y 4,4 en el laboratorio. El modelo B, 7,2 y 3,7. El error típico de la proyección total es de unos 5 puntos porcentuales.",
  "La especie más difícil es aves: el mercado cayó cerca de 20 % y los modelos proyectaban alza.",
  "Por eso presentamos los dos modelos como un rango y no como una cifra exacta.",
  "Dicho en sencillo: el modelo sirve para dar un orden de magnitud y un escenario, no para acertar el número exacto. Y es honesto decirlo así."]),
 ("04. Despliegue y decisiones", 10, [
  "Veamos cómo dejamos el modelo funcionando y qué decisiones proponemos."]),
 ("Simulador web del crecimiento 2027", 45, [
  "Dejamos el modelo en un simulador web. Quien lo usa puede mover la inflación, el PIB, el salario mínimo y los precios en pie, de leche, huevo y pollo. Los controles generales mueven todas las especies.",
  "El simulador muestra el crecimiento de 2027 del mercado y de Zoetis, con su escenario: regular, estable u optimista. Los modelos A y B corren en el navegador y el resultado se muestra como un rango.",
  "Así, el equipo comercial y el financiero pueden probar escenarios por su cuenta, sin necesidad de saber de modelos.",
  "[Demostración sugerida de 15 segundos: subir la inflación o bajar el precio del cerdo y mostrar cómo cambia el rango y el escenario.]"]),
 ("Proyección 2027 por especie", 90, [
  "Esta es la proyección de 2027, como rango entre el modelo A y el modelo B.",
  "Para el mercado total, el crecimiento va de 13,7 % a 15,4 %: un año estable, cerca del límite con optimista. Para Zoetis, de 20,6 % a 22,3 %: optimista.",
  "Por especie. Animales de compañía: mercado de 14,1 % a 15,4 %, y Zoetis de 21,6 % a 21,8 %. Bovinos: mercado de 12,5 % a 15,4 %, y Zoetis de 4,8 % a 4,9 %; es el único año regular para Zoetis. Cerdos, la especie de mayor crecimiento: mercado de 15,4 % a 20,8 %, y Zoetis de 25,7 % a 28,7 %. Aves: mercado de 9,7 % a 15,4 %, y Zoetis de 14,9 % a 17,5 %.",
  "Supusimos que los precios de julio a diciembre de 2026 se quedan iguales a los de junio. El error típico del total es de unos 5 puntos porcentuales.",
  "Lo importante es leer los rangos y no un solo número: si el modelo A y el B se parecen, hay más confianza; si se separan mucho, como en cerdos o aves, hay más incertidumbre."]),
 ("Qué hacer con este resultado", 90, [
  "Entonces, ¿qué respondemos a la pregunta? En 2027 el mercado crecería entre 13,7 % y 15,4 %, y Zoetis entre 20,6 % y 22,3 %. Recomendamos tres cosas.",
  "Uno: usarlo como un rango de referencia para el plan financiero, el forecast, las comisiones y los acuerdos con distribuidores. No como un compromiso ni como una cifra única.",
  "Dos: conocer sus límites. El error típico es de unos 5 puntos, aves y bovinos son los más inciertos, y el modelo no sirve como alarma de bajo crecimiento.",
  "Tres: revalidar en 2027. Probar el modelo B con los datos de julio a diciembre de 2026, que serán un examen nuevo, y alimentarlo con los pronósticos oficiales de inflación y PIB. Si ahí algún modelo sigue ganando, tendremos una base para cambiarlo.",
  "En resumen: la dirección es de crecimiento sólido para el mercado y aún mayor para Zoetis, con bovinos como la especie más débil."]),
 ("Equipo del proyecto", 30, [
  "Este trabajo lo hicimos tres personas: Juan Cuellar Chaparro, gerente de BI; Oscar Hernández Alomia, coordinador de BI y tecnología; y Mariana Jaramillo Naranjo, analista de datos.",
  "Gracias por su atención. Quedamos atentos a sus preguntas y comentarios.",
  "Con gusto respondemos lo que necesiten."]),
]
PREG = [
 ("¿Por qué no eligieron K vecinos o Random Forest, si les fue mejor en el examen?",
  "Porque la regla de selección se fijó antes de abrir el examen. Si escogemos el mejor del examen, ya no queda una prueba honesta: parte de su ventaja es suerte, con solo 24 observaciones. Además, en validación no fueron claramente mejores en las dos tareas. Lo correcto es probarlos con los datos de julio a diciembre de 2026."),
 ("¿Qué significa pp?",
  "Puntos porcentuales: la diferencia entre dos porcentajes. Si el modelo proyecta 12 % y el real fue 15 %, el error es de 3 pp."),
 ("¿Qué tan confiable es la proyección?",
  "Es una referencia, no una cifra exacta. El error típico del total es de unos 5 puntos porcentuales y el resultado se presenta como un rango entre dos modelos."),
 ("¿Por qué no usaron la TRM ni el PIB?",
  "Sí los probamos. La TRM, el PIB y el salario mínimo casi no aportaron señal; los precios en pie del cerdo y del huevo, y la inflación de animales de compañía, fueron los que más pesaron."),
]
WPM = 140
doc = Document()
sec = doc.sections[0]; sec.left_margin = sec.right_margin = Inches(0.8); sec.top_margin = Inches(0.7); sec.bottom_margin = Inches(0.7)
st = doc.styles['Normal']; st.font.name = 'Arial'; st.font.size = Pt(11); st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
def par(text='', size=11, bold=False, color=GR, after=6, align=None, italic=False, keep=False):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(after); p.paragraph_format.space_before = Pt(0)
    if align: p.alignment = align
    if keep: p.paragraph_format.keep_with_next = True
    r = p.add_run(text); r.font.size = Pt(size); r.bold = bold; r.italic = italic; r.font.color.rgb = color; r.font.name = 'Arial'
    return p
def mmss(s): return f"{int(s)//60}:{int(s)%60:02d}"
palabras = [sum(len(t.split()) for t in tx) for _, _, tx in S]
est = [w / WPM * 60 for w in palabras]
par("Spitch de 15 minutos", 24, True, OR, 4)
par("Sustentación del proyecto: Proyección 2027 del mercado de salud animal en Colombia", 13, False, GR2, 4)
par("Zoetis Colombia  |  Juan Cuellar Chaparro, Oscar Hernández Alomia y Mariana Jaramillo Naranjo", 10, False, GR2, 12)
par("Cómo usarlo", 14, True, OR, 4)
for t in ["Hay un texto por cada diapositiva de Sustentacion_Proyecto_ML1.pptx (19 diapositivas), con el tiempo sugerido.",
          f"El texto completo suma unas {sum(palabras):,} palabras ({mmss(sum(est))} a un ritmo de {WPM} palabras por minuto), que cabe en 15 minutos con una pequeña pausa para la demostración del simulador.".replace(",", "."),
          "Las diapositivas de transición (01 a 04) son de 10 segundos: sirven para respirar y anunciar el siguiente bloque.",
          "El lenguaje es simple a propósito. Las cifras salen de las diapositivas y del informe; si cambia una diapositiva, hay que ajustar el texto."]:
    p = doc.add_paragraph(style='List Bullet'); p.paragraph_format.space_after = Pt(3)
    r = p.add_run(t); r.font.size = Pt(10.5); r.font.color.rgb = GR
par("", after=4)
# resumen de tiempos
tb = doc.add_table(rows=1, cols=3); tb.alignment = WD_TABLE_ALIGNMENT.CENTER
def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement('w:shd'); sh.set(qn('w:val'), 'clear'); sh.set(qn('w:color'), 'auto'); sh.set(qn('w:fill'), hexcolor); tcPr.append(sh)
hdr = ["Bloque", "Diapositivas", "Tiempo sugerido"]
bloques = [("Apertura y contexto", "1 a 5", sum(S[i][1] for i in range(0, 5))), ("Datos", "6 a 8", sum(S[i][1] for i in range(5, 8))),
           ("Modelos y evaluación", "9 a 14", sum(S[i][1] for i in range(8, 14))), ("Despliegue, decisiones y cierre", "15 a 19", sum(S[i][1] for i in range(14, 19)))]
for j, h in enumerate(hdr):
    c = tb.rows[0].cells[j]; c.text = ''; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(10); r.font.color.rgb = RGBColor(255, 255, 255); shade(c, 'F65C00')
for b, d, s_ in bloques + [("Total", "1 a 19", sum(x[1] for x in S))]:
    cells = tb.add_row().cells
    for j, v in enumerate((b, d, mmss(s_))):
        cells[j].text = ''; r = cells[j].paragraphs[0].add_run(v); r.font.size = Pt(10); r.font.color.rgb = GR; r.bold = (b == "Total")
doc.add_page_break()
for i, ((titulo, seg, textos), w, e) in enumerate(zip(S, palabras, est), 1):
    par(f"Diapositiva {i}  |  {titulo}", 13, True, OR, 2, keep=True)
    par(f"Tiempo sugerido: {mmss(seg)}  ·  {w} palabras", 9, False, GR2, 6, keep=True)
    t = doc.add_table(rows=1, cols=2); t.autofit = False
    wid = (Inches(2.6), Inches(4.3))
    for j, c in enumerate(t.rows[0].cells): c.width = wid[j]
    for j, col in enumerate(t.columns): col.width = wid[j]
    trPr = t.rows[0]._tr.get_or_add_trPr(); cs = OxmlElement('w:cantSplit'); trPr.append(cs)
    c0, c1 = t.rows[0].cells
    c0.paragraphs[0].add_run().add_picture(str(IMG / f"s-{i:02d}.jpg"), width=Inches(2.45))
    c1.text = ''
    for k, tx in enumerate(textos):
        p = c1.paragraphs[0] if k == 0 else c1.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(tx); r.font.size = Pt(11); r.font.color.rgb = GR
        if tx.startswith('['): r.italic = True; r.font.color.rgb = GR2
    par("", after=6)
doc.add_page_break()
par("Posibles preguntas y respuestas cortas", 16, True, OR, 8)
for q, a in PREG:
    par(q, 11, True, GR, 2, keep=True); par(a, 11, False, GR, 9)
doc.save(str(SALIDA)); print("ok", sum(palabras), mmss(sum(est)), mmss(sum(x[1] for x in S)))
