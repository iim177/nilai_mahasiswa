"""
File ini mengatur AUTENTIKASI:
- hash & verifikasi password (biar password tidak disimpan polos di database)
- fungsi untuk mengecek "siapa yang sedang login" berdasarkan session cookie
- fungsi untuk membatasi akses halaman (hanya superadmin / hanya dosen)
"""

from passlib.context import CryptContext
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class NotAuthenticated(Exception):
    """Dilempar kalau user belum login. Ditangkap di main.py lalu di-redirect ke /login."""
    pass


class Forbidden(Exception):
    """Dilempar kalau user login tapi rolenya tidak diizinkan akses halaman ini."""
    pass


def hash_password(password: str) -> str:
    """Mengubah password polos jadi hash (acak, tidak bisa dibalik)."""
    return pwd_context.hash(password)


def verify_password(password_polos: str, password_hash: str) -> bool:
    """Mengecek apakah password yang diketik user cocok dengan hash di database."""
    return pwd_context.verify(password_polos, password_hash)


def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Mengambil data user yang sedang login dari session cookie.
    Return None kalau belum login.
    Session diisi saat login (lihat routers/auth.py) berupa {"user_id": ..., "role": ...}
    """
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(models.User).filter(models.User.id == user_id, models.User.is_active == True).first()
    return user


def require_login(request: Request, db: Session = Depends(get_db)):
    """Dipakai di halaman yang WAJIB login (siapa saja, superadmin atau dosen)."""
    user = get_current_user(request, db)
    if not user:
        raise NotAuthenticated()
    return user


def require_superadmin(request: Request, db: Session = Depends(get_db)):
    """Dipakai di halaman yang WAJIB superadmin."""
    user = require_login(request, db)
    if user.role != "superadmin":
        raise Forbidden()
    return user


def require_dosen(request: Request, db: Session = Depends(get_db)):
    """Dipakai di halaman yang WAJIB dosen (superadmin juga boleh lewat, tapi biasanya dipakai murni utk dosen)."""
    user = require_login(request, db)
    if user.role not in ("dosen", "superadmin"):
        raise Forbidden()
    return user
