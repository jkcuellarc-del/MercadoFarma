"""Rutas y corte temporal. Se pueden redirigir con variables de entorno (lo usa la verificacion del sello)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FUENTE = Path(os.environ.get("MF_FUENTE", ROOT / "Base Mercado Salud Animal.csv"))
TRM_FUENTE = Path(os.environ.get("MF_TRM", ROOT / "TRM.csv"))
DATA = Path(os.environ.get("MF_DATA", ROOT / "data" / "v2"))
REP = Path(os.environ.get("MF_REP", ROOT / "reports" / "v2"))
MODELOS = Path(os.environ.get("MF_MODELOS", ROOT / "models" / "v2"))
CORTE = "2025-12-01"          # ultimo mes visible en desarrollo
PRUEBA_INI, PRUEBA_FIN = "2026-01-01", "2026-06-01"
