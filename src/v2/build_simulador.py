"""Genera simulador/index.html a partir de template_v2.html, modelo_v2.json (dos modelos) y las imagenes de simulador/imagenes."""
import base64
import io
import json
from pathlib import Path

from PIL import Image

root = Path(__file__).resolve().parents[2] / "simulador"
ARCHIVOS = {"CA": "Cat and Dog.png", "Cattle": "Cattle.png", "Swine": "Pig.png", "Poultry": "Poultry.png", "logo": "Zoetis logo orange.png"}


def uri(nombre, ancho):
    im = Image.open(root / "imagenes" / nombre).convert("RGBA")
    if im.width != ancho:
        im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()


imgs = {k: uri(v, 260 if k == "logo" else 75) for k, v in ARCHIVOS.items()}
html = (root / "template_v2.html").read_text().replace("__MODELO__", (root / "modelo_v2.json").read_text()).replace("__IMAGENES__", json.dumps(imgs))
(root / "index.html").write_text(html)
print(len(html) // 1024, "KB")
