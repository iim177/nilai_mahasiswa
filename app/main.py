"""
FILE UTAMA. Jalankan aplikasi dengan perintah (dari folder root project):
    uvicorn app.main:app --reload

Lalu buka browser ke: http://127.0.0.1:8000
"""

import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine, jalankan_migrasi_ringan
from app import models  # noqa: F401 - supaya semua tabel ke-load sebelum create_all
from app.auth import NotAuthenticated, Forbidden
from app.routers import auth as auth_router
from app.routers import superadmin as superadmin_router
from app.routers import dosen as dosen_router
from app.routers import kelas as kelas_router
from app.routers import mahasiswa as mahasiswa_router

# Membuat semua tabel di database kalau belum ada (aman dijalankan berkali-kali)
Base.metadata.create_all(bind=engine)
# Menambah kolom baru ke tabel LAMA yang sudah ada isinya (lihat penjelasan di database.py)
jalankan_migrasi_ringan()

app = FastAPI(title="Sistem Input Nilai Mahasiswa")

# Session cookie (buat login) - dienkripsi pakai SECRET_KEY dari .env
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "rahasia-ganti-ini"))

# Folder file statis (CSS/JS custom kalau ada)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


# -------------------------------------------------------------------------
# Penanganan error: kalau belum login -> redirect ke /login
#                    kalau tidak punya akses -> halaman 403
# -------------------------------------------------------------------------
@app.exception_handler(NotAuthenticated)
async def handle_not_authenticated(request: Request, exc: NotAuthenticated):
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(Forbidden)
async def handle_forbidden(request: Request, exc: Forbidden):
    return templates.TemplateResponse("403.html", {"request": request}, status_code=403)


# -------------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------------
@app.get("/")
def index():
    return RedirectResponse("/login")


app.include_router(auth_router.router)
app.include_router(superadmin_router.router)
app.include_router(dosen_router.router)
app.include_router(kelas_router.router)
app.include_router(mahasiswa_router.router)
