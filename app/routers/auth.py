"""
Route untuk LOGIN dan LOGOUT.
"""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, auth as auth_utils

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def halaman_login(request: Request, db: Session = Depends(get_db)):
    # Kalau sudah login, langsung lempar ke dashboard masing-masing
    user = auth_utils.get_current_user(request, db)
    if user:
        tujuan = "/superadmin" if user.role == "superadmin" else "/dosen"
        return RedirectResponse(tujuan, status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def proses_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == username).first()

    if not user or not auth_utils.verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Username atau password salah."},
            status_code=401,
        )

    if not user.is_active:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Akun ini dinonaktifkan. Hubungi Superadmin."},
            status_code=403,
        )

    # Simpan info login ke session (cookie yang dienkripsi)
    request.session["user_id"] = user.id
    request.session["role"] = user.role
    request.session["nama"] = user.nama_lengkap

    tujuan = "/superadmin" if user.role == "superadmin" else "/dosen"
    return RedirectResponse(tujuan, status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
