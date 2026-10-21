"""Paso 1 (unico script que abre la base completa): separa y SELLA los datos de prueba.

Parte la base por fecha en dos archivos de texto, sin interpretar ni transformar ninguna celda:
  data/v2/desarrollo.csv        meses <= 2025-12  (lo unico que leen los scripts de desarrollo)
  data/v2/sellado/prueba.csv    meses >= 2026-01  (solo lo abre prueba.py, con registro de acceso)
Igual para TRM.csv: trm_desarrollo.csv (<= 2025-12) y sellado/trm_prueba.csv (>= 2026-01).
Guarda en data/v2/manifiesto.json el hash SHA-256 de la fuente y de cada parte.
"""
import hashlib
import json
import time

import pandas as pd

from . import config as C
from . import datos


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
    # TRM: misma regla de corte
    trm = datos.leer_trm_fuente(C.TRM_FUENTE)
    t_dev, t_sel = trm[trm["Fecha"] <= C.CORTE], trm[trm["Fecha"] > C.CORTE]
    pt_dev, pt_sel = C.DATA / "trm_desarrollo.csv", C.DATA / "sellado" / "trm_prueba.csv"
    t_dev.to_csv(pt_dev, index=False)
    t_sel.to_csv(pt_sel, index=False)
    man.update({"sha256_trm_fuente": sha(C.TRM_FUENTE), "filas_trm_desarrollo": int(len(t_dev)), "filas_trm_sellado": int(len(t_sel)),
                "sha256_trm_desarrollo": sha(pt_dev), "sha256_trm_sellado": sha(pt_sel)})
    (C.DATA / "manifiesto.json").write_text(json.dumps(man, indent=1))
    return man


if __name__ == "__main__":
    print(json.dumps(sellar(), indent=1))
