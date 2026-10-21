"""Genera cuaderno/pipeline_completo.ipynb (nbformat). Ejecutar: python cuaderno/construir_cuaderno.py"""
import nbformat as nbf

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
c = []
c.append(md("""# Proyección 2027 del mercado de salud animal y del Laboratorio: pipeline completo

Este cuaderno reproduce **de principio a fin** el proceso: lectura sellada de los datos, variables, comparación de modelos con validación cruzada,
y lectura de los resultados de la prueba y de la proyección. Está pensado para ejecutarse con **Kernel > Reiniciar y ejecutar todo**.

**Garantías**
- Semilla fija (`SEMILLA = 0`) y versiones de librerías declaradas en la primera celda (avisa si difieren).
- Rutas **relativas** a la carpeta del cuaderno (`cuaderno/`). Las salidas se escriben en `cuaderno/salida/`, nunca sobre los resultados oficiales.
- **No consulta el examen** (enero a junio de 2026): la evaluación única ya se hizo y el cuaderno solo lee sus resultados guardados.

**Modos** (variable `COMPLETO` en la celda 2): `False` ejecuta una versión reducida (mercado, cuatro modelos, unos minutos);
`True` repite toda la comparación (cuatro tareas, diez modelos, unos 25 minutos) y la compara con los resultados oficiales."""))
c.append(code('''# 1. Entorno, semilla y versiones declaradas
import os, sys, random, platform, warnings
os.environ["PYTHONHASHSEED"] = "0"
SEMILLA = 0
random.seed(SEMILLA)
import numpy as np
np.random.seed(SEMILLA)
import pandas as pd, sklearn, scipy, matplotlib, joblib

VERSIONES_DECLARADAS = {"python": "3.13", "numpy": "2.5", "pandas": "3.0", "scikit-learn": "1.9", "scipy": "1.18", "matplotlib": "3.11", "joblib": "1.6"}
actual = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "scikit-learn": sklearn.__version__,
          "scipy": scipy.__version__, "matplotlib": matplotlib.__version__, "joblib": joblib.__version__}
for k, v in actual.items():
    ok = v.startswith(VERSIONES_DECLARADAS[k] + ".") or v == VERSIONES_DECLARADAS[k]
    print(f"{k:13s} {v:10s} declarada {VERSIONES_DECLARADAS[k]:6s} {'OK' if ok else 'ADVERTENCIA: version distinta, los resultados pueden variar'}")
    if not ok:
        warnings.warn(f"{k} {v} != {VERSIONES_DECLARADAS[k]}")
print("semilla", SEMILLA)'''))
c.append(code('''# 2. Rutas relativas y modo de ejecucion
from pathlib import Path
import json

COMPLETO = False   # True: repite toda la comparacion de modelos (~25 min) y la compara con los resultados oficiales

RAIZ = Path("..") if Path("../src/v2").exists() else Path(".")
assert (RAIZ / "src" / "v2").exists(), "Abra el cuaderno desde la carpeta cuaderno/ o desde la raiz del repositorio"
SALIDA = RAIZ / "cuaderno" / "salida"
os.environ.update({"MF_FUENTE": str(RAIZ / "Base Mercado Salud Animal.csv"), "MF_TRM": str(RAIZ / "TRM.csv"),
                   "MF_DATA": str(SALIDA / "data"), "MF_REP": str(SALIDA / "reports"), "MF_MODELOS": str(SALIDA / "models")})
sys.path.insert(0, str(RAIZ.resolve()))
print("raiz:", RAIZ, "| salida:", SALIDA, "| completo:", COMPLETO)'''))
c.append(md("## 3. Lectura y sello de los datos\nLa base se parte por fecha: **desarrollo** (hasta diciembre de 2025) y **sellado** (desde enero de 2026). Todo lo demás solo lee el archivo de desarrollo."))
c.append(code('''from src.v2 import config as C, datos, sellar_base, variables
man = sellar_base.sellar()
print(pd.Series(man).to_string())
dev = datos.leer_desarrollo()
print("\\nfilas de desarrollo:", len(dev), "| ultimo mes:", dev.Fecha.max().date(), "| series:", dev.groupby(["Especie", "Segmento", "Subgrupo"]).ngroups)'''))
c.append(md("## 4. Variables de 12 meses móviles\nCrecimiento de las ventas acumuladas de 12 meses (mercado, mercado donde compite el Laboratorio y Laboratorio) y predictores: inflación, PIB, PIB agropecuario, salario mínimo y **precios reales** (cambio del precio promedio de 12 meses, descontada la inflación)."))
c.append(code('''variables.main()
mer = pd.read_csv(C.DATA / "features_desarrollo_mercado.csv", parse_dates=["Fecha"])
mer[["Fecha", "Especie", "y_mercado", "ipc_yoy", "pib", "real_var_cerdo", "real_var_huevo"]].tail(8)'''))
c.append(md("## 5. Comparación de modelos con validación cruzada por bloques de tiempo y purga\nMismos pliegues y mismo Pipeline (escalamiento incluido) para todos los modelos. Regla de selección declarada: menor error de validación cruzada; entre los que están a menos de un error estándar del mejor, se elige el más simple; debe superar las dos líneas base."))
c.append(code('''from src.v2 import desarrollo, nucleo as N
if not COMPLETO:
    # version reducida: solo la tarea "mercado" y cuatro modelos con rejillas pequenas (demostracion; no reemplaza los resultados oficiales)
    for k in list(N.EST):
        if k not in ("ridge", "enet", "knn", "gbm"):
            del N.EST[k]
    N.GRID["gbm"] = {"n_estimators": [50, 100], "learning_rate": [0.03], "max_depth": [2, 3], "min_samples_leaf": [8]}
    N.GRID["knn"] = {"n_neighbors": [12, 20], "weights": ["uniform", "distance"], "p": [2]}
    tareas = ["mercado"]
else:
    tareas = list(N.TASKS)
C.REP.mkdir(parents=True, exist_ok=True)
for t in tareas:
    desarrollo.dev(t)'''))
c.append(code('''# Resultados de la comparacion (MAE en puntos porcentuales y R2 fuera de pliegue)
for t in tareas:
    print("\\n==", t)
    display(pd.read_csv(C.REP / f"comparacion_cv_{t}.csv").round(2))
    s = json.loads((C.REP / f"seleccion_{t}.json").read_text())
    print("modelo elegido:", s["nombre"], s["params"], "| MAE de CV:", round(s["MAE_cv_final"], 2), "| supera las bases:", s["supera_lineas_base"])'''))
c.append(code('''# Reproducibilidad: en modo completo, la seleccion debe coincidir con la oficial (reports/v2)
if COMPLETO:
    for t in tareas:
        a = json.loads((C.REP / f"seleccion_{t}.json").read_text()); b = json.loads((RAIZ / "reports" / "v2" / f"seleccion_{t}.json").read_text())
        print(t, "identica a la oficial:", a == b)
else:
    print("Modo reducido: la comparacion con los resultados oficiales solo aplica con COMPLETO = True.")'''))
c.append(md("## 6. Examen de 2026 y proyección 2027\nEl cuaderno **no** consulta el examen: lee los resultados guardados. Hubo una consulta principal (modelo elegido por la regla, el de menor error de validación y los métodos sencillos) y una consulta complementaria posterior, solo informativa (K vecinos, Random Forest y regresión lineal). Si el candado no existe, la evaluación aún no se ha hecho y se corre con `python -m src.v2.prueba`."))
c.append(code('''OFICIAL = RAIZ / "reports" / "v2"
lock = OFICIAL / "prueba_consultada.lock"
if lock.exists():
    print("Consulta principal del examen el", lock.read_text().strip())
    r = json.loads((OFICIAL / "prueba_resultados.json").read_text())
    filas = []
    for t in ("mercado", "compite", r["variante_lab"]):
        x = r[t]
        filas.append({"tarea": t, "modelo": x["modelo_final"], "MAE_pp": x["MAE_pp"], "base promedio especie": x["B2_media_especie"]["MAE_pp"],
                      "base año anterior": x["B1_crecimiento_hace_12m"]["MAE_pp"], "R2": x["R2"]})
    display(pd.DataFrame(filas).round(2))
    comp = OFICIAL / "prueba_complementaria.json"
    if comp.exists():
        print("\\nConsulta complementaria posterior (solo informativa, no se uso para elegir modelo):", (OFICIAL / "prueba_complementaria.lock").read_text().strip())
        c = json.loads(comp.read_text())
        display(pd.DataFrame([{"modelo": k, "MAE mercado": v["mercado"]["MAE_pp"], "MAE laboratorio": v["lab"]["MAE_pp"]} for k, v in c.items()]).round(2))
else:
    print("El examen aun no se ha consultado. No lo ejecute desde este cuaderno.")'''))
c.append(code('''proy = OFICIAL / "proyeccion_2027_base.csv"
if proy.exists():
    display(pd.read_csv(proy).round(3))
else:
    print("La proyeccion final se genera despues de la evaluacion unica.")'''))
c.append(md("## 7. Verificación del sello\nResultado guardado de la prueba del canario (cifras de 2026 reemplazadas por un valor absurdo: el desarrollo debe dar resultados idénticos)."))
c.append(code('''ver = OFICIAL / "verificacion_sello.txt"
print(ver.read_text() if ver.exists() else "Sin registro de verificacion.")
print("accesos a la prueba durante el desarrollo:", (OFICIAL / "accesos_prueba.log").read_text() if (OFICIAL / "accesos_prueba.log").exists() else "ninguno registrado en esta carpeta")'''))
nb = nbf.v4.new_notebook(cells=c, metadata={"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python"}})
nbf.write(nb, "cuaderno/pipeline_completo.ipynb")
print("ok", len(c), "celdas")
