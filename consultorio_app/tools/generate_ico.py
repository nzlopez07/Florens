"""
Genera un icono multi-tamaño Florens_icon.ico desde PNG de app/media.

Requiere: Pillow
Uso:
    python tools/generate_ico.py
"""
from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Pillow no está instalado. Instala con: pip install pillow")
    sys.exit(1)

MEDIA = Path(__file__).resolve().parents[1] / 'app' / 'media'
# Preferir muela_foto.png (mayor detalle); fallback a muela_icon.png
candidates = ['muela_icon.png', 'muela_foto.png']
src = None
for name in candidates:
    p = MEDIA / name
    if p.exists():
        src = p
        break

if not src:
    print("[ERROR] No se encontró imagen fuente en app/media: muela_icon.png o muela_foto.png")
    sys.exit(2)

out = MEDIA / 'Florens_icon.ico'
img = Image.open(src).convert('RGBA')
# Usar fondo transparente y antialias al redimensionar
sizes = [(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)]
imgs = [img.resize(sz, Image.LANCZOS) for sz in sizes]
# Guardar como ICO con múltiples tamaños
imgs[0].save(out, format='ICO', sizes=sizes)
print(f"[OK] Generado {out} con tamaños: {sizes}")
