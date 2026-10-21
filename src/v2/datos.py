"""Lectura tipada de los datos. Desarrollo y prueba tienen puertas distintas."""
import hashlib
import inspect
import json
import time

import pandas as pd

from . import config as C

NUM = ["Mercado", "Venta Laboratorio", "Precio Leche", "Precio Carne Res", "Precio carne cerdo", "Precio huevo", "Precio Pollo",
       "Perros", "Gatos", "IPC", "Inflación Mensual", "PIB", "PIB Agro", "Porc Crec SMMLV", "Share Laboratorio",
       "Crec Mercado Q movil", "Crec Mercado Año", "Crec Laboratorio año"]


def _tipar(df):
    df = df.rename(columns={"Compite Laboraorio": "Compite_Laboratorio"})  # el encabezado de la fuente trae un error de ortografia
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y")
    df["Año"] = df["Año"].astype(int)
    for c in NUM:
        df[c] = pd.to_numeric(df[c].str.replace(",", "", regex=False), errors="coerce")
    return df


def leer_desarrollo():
    """Solo meses <= CORTE. Falla si por cualquier razon aparece un mes posterior."""
    df = _tipar(pd.read_csv(C.DATA / "desarrollo.csv", dtype=str))
    assert df["Fecha"].max() <= pd.Timestamp(C.CORTE), "El archivo de desarrollo contiene meses posteriores al corte"
    return df


def leer_prueba(motivo):
    """Puerta de la prueba: verifica el hash del archivo sellado y deja registro de cada acceso."""
    man = json.loads((C.DATA / "manifiesto.json").read_text())
    p = C.DATA / "sellado" / "prueba.csv"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == man["sha256_sellado"], "El archivo sellado fue modificado"
    C.REP.mkdir(parents=True, exist_ok=True)
    with open(C.REP / "accesos_prueba.log", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{motivo}\t{inspect.stack()[1].filename}\n")
    return _tipar(pd.read_csv(p, dtype=str))
