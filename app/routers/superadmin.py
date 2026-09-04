"""
Route khusus SUPERADMIN:
- Dashboard
- Kelola Fakultas, Prodi, Mata Kuliah, Tahun Ajaran
- Kelola akun Dosen (tambah, reset password, nonaktifkan)
"""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, auth as auth_utils

router = APIRouter(prefix="/superadmin")
templates = Jinja2Templates(directory="app/templates")


def ctx(request, user, db, **extra):
    """Helper: menyusun context umum yang dipakai hampir semua halaman superadmin."""
    base = {"request": request, "user": user}
    base.update(extra)
    return base


# ---------------------------------------------------------------- DASHBOARD
@router.get("")
def dashboard(request: Request, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)):
    stats = {
        "fakultas": db.query(models.Fakultas).count(),
        "prodi": db.query(models.Prodi).count(),
        "makul": db.query(models.MataKuliah).count(),
        "kelas": db.query(models.Kelas).count(),
        "dosen": db.query(models.User).filter(models.User.role == "dosen").count(),
        "mahasiswa": db.query(models.Mahasiswa).count(),
    }
    return templates.TemplateResponse("superadmin/dashboard.html", ctx(request, user, db, stats=stats))


# ---------------------------------------------------------------- FAKULTAS
@router.get("/fakultas")
def list_fakultas(request: Request, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)):
    data = db.query(models.Fakultas).order_by(models.Fakultas.nama_fakultas).all()
    return templates.TemplateResponse("superadmin/fakultas.html", ctx(request, user, db, data=data))


@router.post("/fakultas/tambah")
def tambah_fakultas(
    nama_fakultas: str = Form(...),
    user=Depends(auth_utils.require_superadmin),
    db: Session = Depends(get_db),
):
    db.add(models.Fakultas(nama_fakultas=nama_fakultas.strip()))
    db.commit()
    return RedirectResponse("/superadmin/fakultas", status_code=303)


@router.post("/fakultas/{fakultas_id}/hapus")
def hapus_fakultas(
    fakultas_id: int,
    user=Depends(auth_utils.require_superadmin),
    db: Session = Depends(get_db),
):
    f = db.query(models.Fakultas).filter(models.Fakultas.id == fakultas_id).first()
    if f:
        db.delete(f)
        db.commit()
    return RedirectResponse("/superadmin/fakultas", status_code=303)


# ---------------------------------------------------------------- PRODI
@router.get("/prodi")
def list_prodi(request: Request, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)):
    data = db.query(models.Prodi).order_by(models.Prodi.nama_prodi).all()
    fakultas_list = db.query(models.Fakultas).order_by(models.Fakultas.nama_fakultas).all()
    return templates.TemplateResponse(
        "superadmin/prodi.html", ctx(request, user, db, data=data, fakultas_list=fakultas_list)
    )


@router.post("/prodi/tambah")
def tambah_prodi(
    nama_prodi: str = Form(...),
    fakultas_id: int = Form(...),
    user=Depends(auth_utils.require_superadmin),
    db: Session = Depends(get_db),
):
    db.add(models.Prodi(nama_prodi=nama_prodi.strip(), fakultas_id=fakultas_id))
    db.commit()
    return RedirectResponse("/superadmin/prodi", status_code=303)


@router.post("/prodi/{prodi_id}/hapus")
def hapus_prodi(
    prodi_id: int, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)
):
    p = db.query(models.Prodi).filter(models.Prodi.id == prodi_id).first()
    if p:
        db.delete(p)
        db.commit()
    return RedirectResponse("/superadmin/prodi", status_code=303)


# ---------------------------------------------------------------- MATA KULIAH
@router.get("/matakuliah")
def list_makul(request: Request, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)):
    data = db.query(models.MataKuliah).order_by(models.MataKuliah.nama_makul).all()
    prodi_list = db.query(models.Prodi).order_by(models.Prodi.nama_prodi).all()
    return templates.TemplateResponse(
        "superadmin/matakuliah.html", ctx(request, user, db, data=data, prodi_list=prodi_list)
    )


@router.post("/matakuliah/tambah")
def tambah_makul(
    nama_makul: str = Form(...),
    kode_makul: str = Form(""),
    sks: int = Form(2),
    prodi_id: int = Form(...),
    user=Depends(auth_utils.require_superadmin),
    db: Session = Depends(get_db),
):
    db.add(models.MataKuliah(nama_makul=nama_makul.strip(), kode_makul=kode_makul.strip(), sks=sks, prodi_id=prodi_id))
    db.commit()
    return RedirectResponse("/superadmin/matakuliah", status_code=303)


@router.post("/matakuliah/{makul_id}/hapus")
def hapus_makul(
    makul_id: int, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)
):
    m = db.query(models.MataKuliah).filter(models.MataKuliah.id == makul_id).first()
    if m:
        db.delete(m)
        db.commit()
    return RedirectResponse("/superadmin/matakuliah", status_code=303)


# ---------------------------------------------------------------- TAHUN AJARAN
@router.get("/tahun-ajaran")
def list_tahun_ajaran(request: Request, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)):
    data = db.query(models.TahunAjaran).order_by(models.TahunAjaran.id.desc()).all()
    return templates.TemplateResponse("superadmin/tahun_ajaran.html", ctx(request, user, db, data=data))


@router.post("/tahun-ajaran/tambah")
def tambah_tahun_ajaran(
    nama_tahun_ajaran: str = Form(...),
    user=Depends(auth_utils.require_superadmin),
    db: Session = Depends(get_db),
):
    db.add(models.TahunAjaran(nama_tahun_ajaran=nama_tahun_ajaran.strip()))
    db.commit()
    return RedirectResponse("/superadmin/tahun-ajaran", status_code=303)


@router.post("/tahun-ajaran/{ta_id}/hapus")
def hapus_tahun_ajaran(
    ta_id: int, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)
):
    ta = db.query(models.TahunAjaran).filter(models.TahunAjaran.id == ta_id).first()
    if ta:
        db.delete(ta)
        db.commit()
    return RedirectResponse("/superadmin/tahun-ajaran", status_code=303)


# ---------------------------------------------------------------- DOSEN (USER MANAGEMENT)
@router.get("/dosen")
def list_dosen(request: Request, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)):
    data = db.query(models.User).filter(models.User.role == "dosen").order_by(models.User.nama_lengkap).all()
    return templates.TemplateResponse("superadmin/dosen.html", ctx(request, user, db, data=data))


@router.post("/dosen/tambah")
def tambah_dosen(
    nama_lengkap: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    user=Depends(auth_utils.require_superadmin),
    db: Session = Depends(get_db),
):
    dosen_baru = models.User(
        nama_lengkap=nama_lengkap.strip(),
        username=username.strip(),
        password_hash=auth_utils.hash_password(password),
        role="dosen",
        is_active=True,
    )
    db.add(dosen_baru)
    db.commit()
    return RedirectResponse("/superadmin/dosen", status_code=303)


@router.post("/dosen/{dosen_id}/reset-password")
def reset_password_dosen(
    dosen_id: int,
    password_baru: str = Form(...),
    user=Depends(auth_utils.require_superadmin),
    db: Session = Depends(get_db),
):
    d = db.query(models.User).filter(models.User.id == dosen_id).first()
    if d:
        d.password_hash = auth_utils.hash_password(password_baru)
        db.commit()
    return RedirectResponse("/superadmin/dosen", status_code=303)


@router.post("/dosen/{dosen_id}/toggle-aktif")
def toggle_aktif_dosen(
    dosen_id: int, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)
):
    d = db.query(models.User).filter(models.User.id == dosen_id).first()
    if d:
        d.is_active = not d.is_active
        db.commit()
    return RedirectResponse("/superadmin/dosen", status_code=303)
