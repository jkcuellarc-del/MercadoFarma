"""Genera simulador/index.html a partir de simulador/template.html y simulador/modelo.json."""
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "simulador"
html = (root / "template.html").read_text().replace("__MODELO__", (root / "modelo.json").read_text())
(root / "index.html").write_text(html)
print(len(html) // 1024, "KB")
