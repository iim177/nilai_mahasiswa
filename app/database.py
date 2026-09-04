"""
File ini mengatur KONEKSI ke database MySQL (Laragon).
Semua file lain akan "meminjam" koneksi dari sini lewat fungsi get_db().
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Membaca isi file .env (konfigurasi database)
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "nilai_mahasiswa")

# Menyusun "alamat" koneksi database MySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# engine = objek yang benar-benar terhubung ke MySQL
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal = "pintu" untuk melakukan query (ambil/simpan data)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = induk dari semua model tabel (models.py akan mewarisi ini)
Base = declarative_base()


def get_db():
    """
    Dipakai di setiap route FastAPI untuk mendapatkan koneksi database.
    Setelah selesai dipakai, koneksi otomatis ditutup (db.close()).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def jalankan_migrasi_ringan():
    """
    Migrasi kecil untuk menambah kolom baru ke tabel yang SUDAH ADA di database
    (dipakai kalau ada update fitur, tapi boss sudah punya data lama).
    SQLAlchemy's create_all() cuma bikin tabel yang belum ada, TIDAK menambah
    kolom baru ke tabel lama -- makanya perlu helper ini, dijalankan otomatis
    tiap aplikasi start, aman dijalankan berkali-kali (skip kalau kolom sudah ada).
    """
    from sqlalchemy import inspect, text

    inspektor = inspect(engine)
    if "kelas" not in inspektor.get_table_names():
        return  # tabel belum ada sama sekali, nanti dibuat oleh create_all(), tidak perlu migrasi

    kolom_kelas = [c["name"] for c in inspektor.get_columns("kelas")]
    if "pakai_bobot" not in kolom_kelas:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE kelas ADD COLUMN pakai_bobot BOOLEAN DEFAULT 1"))
