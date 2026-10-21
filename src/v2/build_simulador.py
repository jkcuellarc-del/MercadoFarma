"""Genera simulador/index.html a partir de template_v2.html y modelo_v2.json (dos modelos, A y B)."""
from pathlib import Path

root = Path(__file__).resolve().parents[2] / "simulador"
html = (root / "template_v2.html").read_text().replace("__MODELO__", (root / "modelo_v2.json").read_text())
(root / "index.html").write_text(html)
print(len(html) // 1024, "KB")
