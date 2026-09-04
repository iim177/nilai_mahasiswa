"""
Route dashboard untuk DOSEN.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, auth as auth_utils

router = APIRouter(prefix="/dosen")
templates = Jinja2Templates(directory="app/templates")


@router.get("")
def dashboard(request: Request, user=Depends(auth_utils.require_login), db: Session = Depends(get_db)):
    kelas_list = (
        db.query(models.Kelas)
        .options(joinedload(models.Kelas.mata_kuliah), joinedload(models.Kelas.tahun_ajaran))
        .filter(models.Kelas.dosen_id == user.id)
        .order_by(models.Kelas.id.desc())
        .all()
    )
    return templates.TemplateResponse(
        "dosen/dashboard.html", {"request": request, "user": user, "kelas_list": kelas_list}
    )
