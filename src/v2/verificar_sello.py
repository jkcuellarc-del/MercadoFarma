"""Verificacion del sello: demuestra que el desarrollo no depende de los datos de 2026.

1) Estatica: ningun modulo salvo prueba.py/datos.py/sellar_base.py/verificar_sello.py menciona la puerta de la prueba.
2) Dinamica ("canario"): se crea una copia de la fuente en la que TODAS las cifras de 2026 se reemplazan por un
   valor absurdo (999999999), se repite sellado + variables + desarrollo en carpetas temporales y se comprueba que
   los resultados del desarrollo son identicos byte a byte a los oficiales.
3) El registro de accesos a la prueba esta vacio hasta la evaluacion unica.
"""
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

from . import config as C
from . import datos

PERMITIDOS = {"prueba.py", "datos.py", "sellar_base.py", "verificar_sello.py", "despliegue.py"}  # despliegue.py solo corre despues de la prueba
TAREAS = ("mercado", "compite", "lab", "lab_ym")
ARCHIVOS = [f"features_desarrollo_{t}.csv" for t in TAREAS] + ["series_compite.csv", "trm_desarrollo.csv"]
RESULTADOS = [f"{a}_{t}.{e}" for t in TAREAS for a, e in (("seleccion", "json"), ("cv_grid", "csv"), ("comparacion_cv", "csv"), ("oof", "csv"),
              ("umbral", "csv"), ("curva_aprendizaje", "csv"), ("efecto_balance", "csv"), ("sensibilidad_validacion", "csv"),
              ("curva_boosting", "csv"), ("curva_arboles", "csv"))] + ["screening_predictores.csv", "importancia_variables.csv"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def estatica():
    malos = []
    for p in Path(__file__).parent.glob("*.py"):
        t = p.read_text()
        if p.name not in PERMITIDOS and ("leer_prueba" in t or "sellado" in t or "prueba.csv" in t):
            malos.append(p.name)
    return malos


def canario():
    raw = pd.read_csv(C.FUENTE, encoding="utf-8-sig", dtype=str)
    f = pd.to_datetime(raw["Fecha"], format="%d/%m/%Y", errors="coerce")
    for c in datos.NUM:
        raw.loc[f > C.CORTE, c] = "999999999"
    tmp = Path(tempfile.mkdtemp(prefix="canario_"))
    raw.to_csv(tmp / "fuente_alterada.csv", index=False, encoding="utf-8-sig")
    trm = datos.leer_trm_fuente(C.TRM_FUENTE)
    lineas = []
    for l in open(C.TRM_FUENTE, encoding="utf-8-sig"):
        m = re.match(r"^(\d{2})/(\d{2})/(\d{4}),", l)
        lineas.append(f"{m.group(1)}/{m.group(2)}/{m.group(3)},999999,999999\n" if (m and pd.Timestamp(int(m.group(3)), int(m.group(2)), 1) > pd.Timestamp(C.CORTE)) else l)
    (tmp / "trm_alterada.csv").write_text("".join(lineas), encoding="utf-8-sig")
    env = {**os.environ, "MF_FUENTE": str(tmp / "fuente_alterada.csv"), "MF_TRM": str(tmp / "trm_alterada.csv"), "MF_DATA": str(tmp / "data"), "MF_REP": str(tmp / "rep")}
    for m in ("sellar_base", "variables", "desarrollo", "seleccion_predictores", "importancia"):
        r = subprocess.run([sys.executable, "-m", f"src.v2.{m}"], cwd=C.ROOT, env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-500:]
    filas = []
    for a, b in [(C.DATA / x, tmp / "data" / x) for x in ARCHIVOS] + [(C.REP / x, tmp / "rep" / x) for x in RESULTADOS]:
        filas.append((a.name, sha(a) == sha(b)))
    return filas, tmp


def main():
    malos = estatica()
    print("1) Referencias a la prueba fuera de los modulos permitidos:", malos or "ninguna")
    filas, tmp = canario()
    ok = all(v for _, v in filas)
    print(f"2) Canario (cifras de 2026 reemplazadas por 999999999): {sum(v for _, v in filas)}/{len(filas)} archivos identicos")
    for n, v in filas:
        if not v:
            print("   DIFERENTE:", n)
    log = C.REP / "accesos_prueba.log"
    print("3) Accesos registrados a la prueba:", (len(log.read_text().splitlines()) if log.exists() else 0))
    (C.REP / "verificacion_sello.txt").write_text(f"estatica_ok={not malos}\ncanario_identicos={sum(v for _, v in filas)}/{len(filas)}\naccesos_prueba={(len(log.read_text().splitlines()) if log.exists() else 0)}\n")
    sys.exit(0 if (ok and not malos) else 1)


if __name__ == "__main__":
    main()
