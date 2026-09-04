"""
Script ini dijalankan SEKALI SAJA di awal untuk membuat akun Superadmin pertama.
Cara jalankan (dari folder root project, virtual environment aktif):
    python seed_admin.py
"""

from app.database import SessionLocal, Base, engine
from app import models
from app.auth import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

USERNAME = "superadmin"
PASSWORD = "admin123"   # <-- SILAKAN GANTI setelah login pertama kali
NAMA = "Super Admin"

sudah_ada = db.query(models.User).filter(models.User.username == USERNAME).first()

if sudah_ada:
    print(f"Akun superadmin dengan username '{USERNAME}' sudah ada. Tidak dibuat ulang.")
else:
    admin = models.User(
        username=USERNAME,
        password_hash=hash_password(PASSWORD),
        nama_lengkap=NAMA,
        role="superadmin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    print("=" * 50)
    print("Akun Superadmin berhasil dibuat!")
    print(f"Username : {USERNAME}")
    print(f"Password : {PASSWORD}")
    print("PENTING: segera login dan ganti password lewat halaman yang sesuai.")
    print("=" * 50)

db.close()
