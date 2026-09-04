"""
Route untuk data MAHASISWA (general, belum terikat kelas):
- List semua mahasiswa, dengan filter (Fakultas/Prodi/Kelas) & search (nama/NPM)
- Tambah manual
- Import dari Excel (Nama + NPM)
- Download template Excel
"""

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.database import get_db
from app import models, auth as auth_utils
from app.utils import excel_helper

router = APIRouter(prefix="/mahasiswa")
templates = Jinja2Templates(directory="app/templates")


def _kelas_yang_bisa_diakses(user, db: Session):
    """Daftar Kelas yang boleh dipakai sebagai filter, sesuai role: superadmin semua, dosen kelasnya sendiri."""
    q = db.query(models.Kelas).options(
        joinedload(models.Kelas.mata_kuliah).joinedload(models.MataKuliah.prodi).joinedload(models.Prodi.fakultas),
        joinedload(models.Kelas.tahun_ajaran),
    )
    if user.role == "dosen":
        q = q.filter(models.Kelas.dosen_id == user.id)
    return q.all()


def _build_context(request, user, db, q, fakultas_id, prodi_id, kelas_id, pesan):
    """Menyusun daftar mahasiswa (sudah difilter/dicari) + data untuk dropdown filter & badge kelas."""
    kelas_accessible = _kelas_yang_bisa_diakses(user, db)
    kelas_accessible_ids = {k.id for k in kelas_accessible}

    # Kalau kelas_id yang diminta bukan kelas yang boleh diakses user ini, abaikan (biar tidak "bocor" data)
    if kelas_id and kelas_id not in kelas_accessible_ids:
        kelas_id = None

    query = db.query(models.Mahasiswa)

    if q and q.strip():
        kata = f"%{q.strip()}%"
        query = query.filter(or_(models.Mahasiswa.nama.ilike(kata), models.Mahasiswa.npm.ilike(kata)))

    if kelas_id or prodi_id or fakultas_id:
        if kelas_id:
            sub_kelas_ids = [kelas_id]
        elif prodi_id:
            sub_kelas_ids = [k.id for k in kelas_accessible if k.mata_kuliah.prodi_id == prodi_id]
        elif fakultas_id:
            sub_kelas_ids = [k.id for k in kelas_accessible if k.mata_kuliah.prodi.fakultas_id == fakultas_id]
        else:
            sub_kelas_ids = [k.id for k in kelas_accessible]

        mahasiswa_ids = [
            row[0] for row in (
                db.query(models.KelasMahasiswa.mahasiswa_id)
                .filter(models.KelasMahasiswa.kelas_id.in_(sub_kelas_ids))
                .distinct()
                .all()
            )
        ] if sub_kelas_ids else []
        query = query.filter(models.Mahasiswa.id.in_(mahasiswa_ids))

    data = query.order_by(models.Mahasiswa.nama).all()

    # ---- Opsi dropdown Fakultas & Prodi, diambil dari kelas yang bisa diakses user ini ----
    fakultas_map, prodi_map = {}, {}
    for k in kelas_accessible:
        prodi_map[k.mata_kuliah.prodi.id] = k.mata_kuliah.prodi
        fakultas_map[k.mata_kuliah.prodi.fakultas.id] = k.mata_kuliah.prodi.fakultas
    fakultas_list = sorted(fakultas_map.values(), key=lambda x: x.nama_fakultas)
    prodi_list_filter = sorted(prodi_map.values(), key=lambda x: x.nama_prodi)
    if fakultas_id:
        prodi_list_filter = [p for p in prodi_list_filter if p.fakultas_id == fakultas_id]

    kelas_list_filter = kelas_accessible
    if prodi_id:
        kelas_list_filter = [k for k in kelas_list_filter if k.mata_kuliah.prodi_id == prodi_id]
    elif fakultas_id:
        kelas_list_filter = [k for k in kelas_list_filter if k.mata_kuliah.prodi.fakultas_id == fakultas_id]
    kelas_list_filter = sorted(kelas_list_filter, key=lambda k: (k.mata_kuliah.nama_makul, k.nama_kelas))

    # ---- Kelas yang diikuti tiap mahasiswa yang tampil (buat kolom "Kelas" di tabel) ----
    kelas_per_mahasiswa = {}
    if data:
        mhs_ids_tampil = [m.id for m in data]
        km_list = (
            db.query(models.KelasMahasiswa)
            .options(joinedload(models.KelasMahasiswa.kelas).joinedload(models.Kelas.mata_kuliah))
            .filter(models.KelasMahasiswa.mahasiswa_id.in_(mhs_ids_tampil))
            .all()
        )
        for km in km_list:
            # Dosen cuma boleh lihat badge kelas yang dia ampu sendiri (bukan kelas dosen lain)
            if user.role == "dosen" and km.kelas_id not in kelas_accessible_ids:
                continue
            kelas_per_mahasiswa.setdefault(km.mahasiswa_id, []).append(km.kelas)

    return {
        "request": request, "user": user, "data": data, "pesan": pesan,
        "q": q or "", "f_fakultas_id": fakultas_id, "f_prodi_id": prodi_id, "f_kelas_id": kelas_id,
        "fakultas_list": fakultas_list, "prodi_list_filter": prodi_list_filter,
        "kelas_list_filter": kelas_list_filter, "kelas_per_mahasiswa": kelas_per_mahasiswa,
    }


@router.get("")
def list_mahasiswa(
    request: Request,
    q: str = None,
    fakultas_id: int = None,
    prodi_id: int = None,
    kelas_id: int = None,
    user=Depends(auth_utils.require_login),
    db: Session = Depends(get_db),
):
    ctx = _build_context(request, user, db, q, fakultas_id, prodi_id, kelas_id, pesan=None)
    return templates.TemplateResponse("mahasiswa/list.html", ctx)


@router.post("/tambah")
def tambah_mahasiswa(
    npm: str = Form(...),
    nama: str = Form(...),
    user=Depends(auth_utils.require_login),
    db: Session = Depends(get_db),
):
    sudah_ada = db.query(models.Mahasiswa).filter(models.Mahasiswa.npm == npm.strip()).first()
    if not sudah_ada:
        db.add(models.Mahasiswa(npm=npm.strip(), nama=nama.strip()))
        db.commit()
    return RedirectResponse("/mahasiswa", status_code=303)


@router.post("/{mhs_id}/hapus")
def hapus_mahasiswa(mhs_id: int, user=Depends(auth_utils.require_login), db: Session = Depends(get_db)):
    m = db.query(models.Mahasiswa).filter(models.Mahasiswa.id == mhs_id).first()
    if m:
        db.delete(m)
        db.commit()
    return RedirectResponse("/mahasiswa", status_code=303)


@router.get("/template-excel")
def download_template(user=Depends(auth_utils.require_login)):
    buffer = excel_helper.buat_template_mahasiswa()
    return StreamingResponse(
        buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="template_mahasiswa.xlsx"'},
    )


@router.post("/import")
async def import_excel(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(auth_utils.require_login),
    db: Session = Depends(get_db),
):
    isi = await file.read()
    try:
        baris = excel_helper.baca_excel_mahasiswa(isi)
    except Exception:
        ctx = _build_context(request, user, db, None, None, None, None, "File Excel tidak valid. Pastikan formatnya sesuai template.")
        return templates.TemplateResponse("mahasiswa/list.html", ctx, status_code=400)

    jumlah_baru = 0
    jumlah_lewat = 0
    npm_sudah_diproses = set()  # cegah duplikat NPM di dalam file Excel yang sama
    for b in baris:
        if b["npm"] in npm_sudah_diproses:
            jumlah_lewat += 1
            continue
        sudah_ada = db.query(models.Mahasiswa).filter(models.Mahasiswa.npm == b["npm"]).first()
        if sudah_ada:
            jumlah_lewat += 1
            npm_sudah_diproses.add(b["npm"])
            continue
        db.add(models.Mahasiswa(npm=b["npm"], nama=b["nama"]))
        npm_sudah_diproses.add(b["npm"])
        jumlah_baru += 1
    db.commit()

    pesan = f"Berhasil import {jumlah_baru} mahasiswa baru. {jumlah_lewat} NPM sudah ada sebelumnya (dilewati)."
    ctx = _build_context(request, user, db, None, None, None, None, pesan)
    return templates.TemplateResponse("mahasiswa/list.html", ctx)
