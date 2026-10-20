"""
Jalankan SEKALI dari folder utama project (yang ada folder app/ di dalamnya):
    python patch_favicon.py
Efek: menambah tag favicon ke app/templates/base.html (berlaku untuk SEMUA halaman, termasuk login).
"""
import sys

p = "app/templates/base.html"
s = open(p, encoding="utf-8").read()
if 'rel="icon"' in s:
    print("base.html: favicon sudah terpasang, dilewati")
    sys.exit(0)
if s.count("</title>") != 1:
    print("GAGAL: tag </title> tidak ditemukan tepat satu kali di", p)
    print("Kabari Claude, kirim bagian <head> dari base.html.")
    sys.exit(1)
tag = ('</title>\n'
       '<link rel="icon" type="image/png" href="/static/favicon.png?v=1">\n'
       '<link rel="apple-touch-icon" href="/static/favicon.png?v=1">')
open(p, "w", encoding="utf-8").write(s.replace("</title>", tag, 1))
print("base.html: OK, favicon terpasang (/static/favicon.png)")
