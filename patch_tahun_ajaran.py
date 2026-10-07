"""
Jalankan SEKALI dari folder utama project (yang ada folder app/ di dalamnya):
    python patch_tahun_ajaran.py
Efek: Tahun Ajaran yang baru dibuat jadi NONAKTIF dulu (aktifkan manual nanti).
"""
import sys

# 1. logika di server
p = "app/routers/superadmin.py"
s = open(p, encoding="utf-8").read()
lama = "models.TahunAjaran(nama_tahun_ajaran=nama_tahun_ajaran.strip())"
baru = "models.TahunAjaran(nama_tahun_ajaran=nama_tahun_ajaran.strip(), is_active=False)"
if baru in s:
    print("superadmin.py: sudah dipatch sebelumnya, dilewati")
elif lama in s:
    open(p, "w", encoding="utf-8").write(s.replace(lama, baru, 1))
    print("superadmin.py: OK, tahun ajaran baru sekarang nonaktif dulu")
else:
    print("GAGAL: baris db.add(models.TahunAjaran(...)) tidak ditemukan di", p)
    print("Kabari Claude, kirim isi fungsi tambah_tahun_ajaran.")
    sys.exit(1)

# 2. teks tombol (kosmetik, tidak wajib)
p = "app/templates/superadmin/tahun_ajaran.html"
try:
    h = open(p, encoding="utf-8").read()
    if "Simpan (langsung aktif)" in h:
        open(p, "w", encoding="utf-8").write(
            h.replace("Simpan (langsung aktif)", "Simpan (nonaktif dulu, aktifkan nanti)"))
        print("tahun_ajaran.html: teks tombol diperbarui")
    else:
        print("tahun_ajaran.html: teks tombol tidak ditemukan, dilewati (tidak masalah)")
except FileNotFoundError:
    print("tahun_ajaran.html: file tidak ditemukan, dilewati")
