"""Paso 1 (unico script que abre la base completa): separa y SELLA los datos de prueba.

Parte la base por fecha en dos archivos de texto, sin interpretar ni transformar ninguna celda:
  data/v2/desarrollo.csv        meses <= 2025-12  (lo unico que leen los scripts de desarrollo)
  data/v2/sellado/prueba.csv    meses >= 2026-01  (solo lo abre prueba.py, con registro de acceso)
Guarda en data/v2/manifiesto.json el hash SHA-256 de la fuente y de cada parte.
"""
import hashlib
import json
import time

import pandas as pd

from . import config as C


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sellar():
    raw = pd.read_csv(C.FUENTE, encoding="utf-8-sig", dtype=str).dropna(how="all")
    fecha = pd.to_datetime(raw["Fecha"], format="%d/%m/%Y")
    dev, sel = raw[fecha <= C.CORTE], raw[fecha > C.CORTE]
    (C.DATA / "sellado").mkdir(parents=True, exist_ok=True)
    pd_dev, pd_sel = C.DATA / "desarrollo.csv", C.DATA / "sellado" / "prueba.csv"
    dev.to_csv(pd_dev, index=False)
    sel.to_csv(pd_sel, index=False)
    man = {"fuente": str(C.FUENTE.name), "sha256_fuente": sha(C.FUENTE), "corte_desarrollo": C.CORTE,
           "filas_desarrollo": int(len(dev)), "filas_sellado": int(len(sel)),
           "fecha_max_desarrollo": str(fecha[fecha <= C.CORTE].max().date()), "fecha_min_sellado": str(fecha[fecha > C.CORTE].min().date()),
           "sha256_desarrollo": sha(pd_dev), "sha256_sellado": sha(pd_sel), "sellado_el": time.strftime("%Y-%m-%d %H:%M:%S")}
    (C.DATA / "manifiesto.json").write_text(json.dumps(man, indent=1))
    return man


if __name__ == "__main__":
    print(json.dumps(sellar(), indent=1))
