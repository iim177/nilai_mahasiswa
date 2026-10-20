"""
Ubah foto/logo apa saja (JPG/PNG, tidak harus persegi) jadi favicon yang pas.
Butuh Pillow sekali saja:  pip install pillow
Pakai (dari folder utama project):  python buat_favicon.py foto.jpg
Hasil: app/static/favicon.png (persegi 512x512, dipotong dari tengah)
"""
import os
import sys

from PIL import Image

if len(sys.argv) < 2:
    print("Cara pakai: python buat_favicon.py nama_foto.jpg")
    sys.exit(1)

img = Image.open(sys.argv[1]).convert("RGBA")
w, h = img.size
sisi = min(w, h)
kiri, atas = (w - sisi) // 2, (h - sisi) // 2
img = img.crop((kiri, atas, kiri + sisi, atas + sisi)).resize((512, 512), getattr(Image, "Resampling", Image).LANCZOS)
os.makedirs("app/static", exist_ok=True)
img.save("app/static/favicon.png", optimize=True)
print("OK: app/static/favicon.png dibuat (512x512)")
