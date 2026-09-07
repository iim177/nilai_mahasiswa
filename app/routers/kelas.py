"""
Route untuk KELAS (dipakai bareng oleh Superadmin & Dosen):
- List kelas (superadmin lihat semua, dosen lihat kelas dia saja, hanya Tahun Ajaran aktif) + filter & search
- Buat kelas baru (khusus superadmin, karena harus tunjuk dosen)
- Detail kelas: assign mahasiswa, input nilai, bobot, nilai harian (tugas/kuis)
- Export transkrip (PDF & Excel)
"""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, auth as auth_utils
from app.utils import pdf_helper, excel_helper

router = APIRouter(prefix="/kelas")
templates = Jinja2Templates(directory="app/templates")


def _to_int(value):
    """Ubah teks dari query parameter jadi angka, atau None kalau kosong/tidak valid."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def get_kelas_atau_403(kelas_id: int, user, db: Session):
    """
    Ambil kelas, pastikan dosen hanya boleh akses kelas yang dia ampu,
    DAN hanya kalau Tahun Ajaran kelas itu masih aktif (dosen tidak bisa
    akses kelas dari tahun nonaktif sama sekali, walau tahu URL-nya).
    Superadmin selalu bisa akses kelas manapun, aktif atau tidak.
    """
    kelas = (
        db.query(models.Kelas)
        .options(
            joinedload(models.Kelas.mata_kuliah),
            joinedload(models.Kelas.tahun_ajaran),
            joinedload(models.Kelas.dosen),
        )
        .filter(models.Kelas.id == kelas_id)
        .first()
    )
    if not kelas:
        return None
    if user.role == "dosen":
        if kelas.dosen_id != user.id:
            return None
        if not kelas.tahun_ajaran.is_active:
            return None
    return kelas


# ---------------------------------------------------------------- LIST KELAS
@router.get("")
def list_kelas(
    request: Request,
    fakultas_id: str = None,
    prodi_id: str = None,
    mata_kuliah_id: str = None,
    tahun_ajaran_id: str = None,
    hanya_aktif: str = None,
    user=Depends(auth_utils.require_login),
    db: Session = Depends(get_db),
):
    fakultas_id = _to_int(fakultas_id)
    prodi_id = _to_int(prodi_id)
    mata_kuliah_id = _to_int(mata_kuliah_id)
    tahun_ajaran_id = _to_int(tahun_ajaran_id)
    hanya_aktif_bool = bool(hanya_aktif)  # checkbox: ada nilai apapun = dicentang

    q = db.query(models.Kelas).options(
        joinedload(models.Kelas.mata_kuliah).joinedload(models.MataKuliah.prodi).joinedload(models.Prodi.fakultas),
        joinedload(models.Kelas.tahun_ajaran),
        joinedload(models.Kelas.dosen),
    )

    if user.role == "dosen":
        # Dosen: kelasnya sendiri, DAN cuma dari Tahun Ajaran yang aktif
        q = q.filter(models.Kelas.dosen_id == user.id)
        q = q.join(models.TahunAjaran, models.Kelas.tahun_ajaran_id == models.TahunAjaran.id)
        q = q.filter(models.TahunAjaran.is_active == True)
    elif hanya_aktif_bool:
        # Superadmin dengan checkbox "hanya tampilkan tahun aktif" dicentang
        q = q.join(models.TahunAjaran, models.Kelas.tahun_ajaran_id == models.TahunAjaran.id)
        q = q.filter(models.TahunAjaran.is_active == True)

    # ---- Filter pencarian (Fakultas -> Prodi -> Mata Kuliah, + Tahun Ajaran) ----
    if tahun_ajaran_id:
        q = q.filter(models.Kelas.tahun_ajaran_id == tahun_ajaran_id)
    if mata_kuliah_id:
        q = q.filter(models.Kelas.mata_kuliah_id == mata_kuliah_id)
    elif prodi_id:
        q = q.join(models.MataKuliah, models.Kelas.mata_kuliah_id == models.MataKuliah.id).filter(models.MataKuliah.prodi_id == prodi_id)
    elif fakultas_id:
        q = q.join(models.MataKuliah, models.Kelas.mata_kuliah_id == models.MataKuliah.id).join(models.Prodi).filter(models.Prodi.fakultas_id == fakultas_id)

    data = q.order_by(models.Kelas.id.desc()).all()

    # Data untuk form "buat kelas baru" (khusus superadmin) - tetap semua Tahun Ajaran, aktif/tidak
    makul_list, ta_list, dosen_list = [], [], []
    if user.role == "superadmin":
        makul_list = db.query(models.MataKuliah).order_by(models.MataKuliah.nama_makul).all()
        ta_list = db.query(models.TahunAjaran).order_by(models.TahunAjaran.id.desc()).all()
        dosen_list = db.query(models.User).filter(models.User.role == "dosen").order_by(models.User.nama_lengkap).all()

    # Data untuk dropdown FILTER
    fakultas_list = db.query(models.Fakultas).order_by(models.Fakultas.nama_fakultas).all()
    prodi_list_filter = db.query(models.Prodi).order_by(models.Prodi.nama_prodi).all()
    if fakultas_id:
        prodi_list_filter = [p for p in prodi_list_filter if p.fakultas_id == fakultas_id]
    makul_list_filter = db.query(models.MataKuliah).order_by(models.MataKuliah.nama_makul).all()
    if prodi_id:
        makul_list_filter = [m for m in makul_list_filter if m.prodi_id == prodi_id]
    elif fakultas_id:
        prodi_id_terkait = [p.id for p in prodi_list_filter]
        makul_list_filter = [m for m in makul_list_filter if m.prodi_id in prodi_id_terkait]

    # Dropdown Tahun Ajaran: dosen cuma lihat yang aktif; superadmin lihat semua (dikasih label Nonaktif)
    ta_list_filter = db.query(models.TahunAjaran).order_by(models.TahunAjaran.id.desc()).all()
    if user.role == "dosen":
        ta_list_filter = [t for t in ta_list_filter if t.is_active]

    return templates.TemplateResponse(
        "kelas/list.html",
        {
            "request": request, "user": user, "data": data,
            "makul_list": makul_list, "ta_list": ta_list, "dosen_list": dosen_list,
            "fakultas_list": fakultas_list, "prodi_list_filter": prodi_list_filter,
            "makul_list_filter": makul_list_filter, "ta_list_filter": ta_list_filter,
            "f_fakultas_id": fakultas_id, "f_prodi_id": prodi_id,
            "f_mata_kuliah_id": mata_kuliah_id, "f_tahun_ajaran_id": tahun_ajaran_id,
            "hanya_aktif": hanya_aktif_bool,
        },
    )


@router.post("/tambah")
def tambah_kelas(
    nama_kelas: str = Form(...),
    mata_kuliah_id: int = Form(...),
    tahun_ajaran_id: int = Form(...),
    dosen_id: int = Form(...),
    user=Depends(auth_utils.require_superadmin),
    db: Session = Depends(get_db),
):
    k = models.Kelas(
        nama_kelas=nama_kelas.strip(),
        mata_kuliah_id=mata_kuliah_id,
        tahun_ajaran_id=tahun_ajaran_id,
        dosen_id=dosen_id,
    )
    db.add(k)
    db.commit()
    return RedirectResponse("/kelas", status_code=303)


@router.post("/{kelas_id}/hapus")
def hapus_kelas(kelas_id: int, user=Depends(auth_utils.require_superadmin), db: Session = Depends(get_db)):
    k = db.query(models.Kelas).filter(models.Kelas.id == kelas_id).first()
    if k:
        db.delete(k)
        db.commit()
    return RedirectResponse("/kelas", status_code=303)


# ---------------------------------------------------------------- DETAIL KELAS
@router.get("/{kelas_id}")
def detail_kelas(
    kelas_id: int, request: Request, error_bobot: str = None,
    user=Depends(auth_utils.require_login), db: Session = Depends(get_db)
):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)

    anggota = (
        db.query(models.KelasMahasiswa)
        .options(
            joinedload(models.KelasMahasiswa.mahasiswa),
            joinedload(models.KelasMahasiswa.nilai_harian),
        )
        .filter(models.KelasMahasiswa.kelas_id == kelas_id)
        .join(models.Mahasiswa)
        .order_by(models.Mahasiswa.nama)
        .all()
    )

    item_tugas = [i for i in kelas.item_nilai_list if i.jenis == "tugas"]
    item_kuis = [i for i in kelas.item_nilai_list if i.jenis == "kuis"]

    peta_nilai_harian = {}
    for km in anggota:
        for ni in km.nilai_harian:
            peta_nilai_harian[(ni.item_nilai_id, km.id)] = ni.nilai

    id_terdaftar = [a.mahasiswa_id for a in anggota]
    q_belum = db.query(models.Mahasiswa)
    if id_terdaftar:
        q_belum = q_belum.filter(~models.Mahasiswa.id.in_(id_terdaftar))
    mahasiswa_belum_terdaftar = q_belum.order_by(models.Mahasiswa.nama).all()

    return templates.TemplateResponse(
        "kelas/detail.html",
        {
            "request": request, "user": user, "kelas": kelas,
            "anggota": anggota, "mahasiswa_belum_terdaftar": mahasiswa_belum_terdaftar,
            "item_tugas": item_tugas, "item_kuis": item_kuis,
            "peta_nilai_harian": peta_nilai_harian,
            "error_bobot": error_bobot,
        },
    )


# ---------------------------------------------------------------- ITEM NILAI (Tugas Harian / Kuis)
@router.post("/{kelas_id}/item-nilai/tambah")
def tambah_item_nilai(
    kelas_id: int,
    jenis: str = Form(...),
    nama: str = Form(...),
    user=Depends(auth_utils.require_login),
    db: Session = Depends(get_db),
):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)
    if jenis not in ("tugas", "kuis"):
        return RedirectResponse(f"/kelas/{kelas_id}", status_code=303)

    urutan_terakhir = (
        db.query(models.ItemNilai)
        .filter(models.ItemNilai.kelas_id == kelas_id, models.ItemNilai.jenis == jenis)
        .count()
    )
    db.add(models.ItemNilai(kelas_id=kelas_id, jenis=jenis, nama=nama.strip(), urutan=urutan_terakhir + 1))
    db.commit()
    return RedirectResponse(f"/kelas/{kelas_id}#{jenis}", status_code=303)


@router.post("/{kelas_id}/item-nilai/{item_id}/hapus")
def hapus_item_nilai(
    kelas_id: int, item_id: int, user=Depends(auth_utils.require_login), db: Session = Depends(get_db)
):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)
    item = db.query(models.ItemNilai).filter(models.ItemNilai.id == item_id, models.ItemNilai.kelas_id == kelas_id).first()
    jenis = item.jenis if item else "tugas"
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(f"/kelas/{kelas_id}#{jenis}", status_code=303)


@router.post("/{kelas_id}/item-nilai/simpan")
async def simpan_nilai_harian(
    kelas_id: int,
    request: Request,
    jenis: str = Form(...),
    user=Depends(auth_utils.require_login),
    db: Session = Depends(get_db),
):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)

    def parse(v):
        if v is None:
            return None
        v = v.strip()
        if v == "":
            return None
        try:
            nilai = float(v)
        except ValueError:
            return None
        return max(0, min(100, nilai))

    form_data = await request.form()
    item_ids = [i.id for i in kelas.item_nilai_list if i.jenis == jenis]
    km_ids = [km.id for km in kelas.anggota]

    for item_id in item_ids:
        for km_id in km_ids:
            nilai = parse(form_data.get(f"nilai_{item_id}_{km_id}"))
            baris = (
                db.query(models.NilaiItem)
                .filter(models.NilaiItem.item_nilai_id == item_id, models.NilaiItem.kelas_mahasiswa_id == km_id)
                .first()
            )
            if baris:
                baris.nilai = nilai
            else:
                db.add(models.NilaiItem(item_nilai_id=item_id, kelas_mahasiswa_id=km_id, nilai=nilai))

    db.commit()
    return RedirectResponse(f"/kelas/{kelas_id}#{jenis}", status_code=303)


# ---------------------------------------------------------------- BOBOT & TOGGLE
@router.post("/{kelas_id}/bobot")
def update_bobot(
    kelas_id: int,
    request: Request,
    bobot_tugas: float = Form(...),
    bobot_kuis: float = Form(...),
    bobot_uts: float = Form(...),
    bobot_uas: float = Form(...),
    user=Depends(auth_utils.require_login),
    db: Session = Depends(get_db),
):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)

    total = bobot_tugas + bobot_kuis + bobot_uts + bobot_uas
    if abs(total - 100) > 0.01:
        return RedirectResponse(f"/kelas/{kelas_id}?error_bobot=Total+bobot+harus+100%25,+saat+ini+{total:.1f}%25", status_code=303)

    kelas.bobot_tugas = bobot_tugas
    kelas.bobot_kuis = bobot_kuis
    kelas.bobot_uts = bobot_uts
    kelas.bobot_uas = bobot_uas
    db.commit()
    return RedirectResponse(f"/kelas/{kelas_id}", status_code=303)


@router.post("/{kelas_id}/toggle-bobot")
def toggle_bobot(
    kelas_id: int, user=Depends(auth_utils.require_login), db: Session = Depends(get_db)
):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)
    kelas.pakai_bobot = not kelas.pakai_bobot
    db.commit()
    return RedirectResponse(f"/kelas/{kelas_id}", status_code=303)


# ---------------------------------------------------------------- ASSIGN MAHASISWA
@router.post("/{kelas_id}/assign")
def assign_mahasiswa(
    kelas_id: int,
    mahasiswa_id: int = Form(...),
    user=Depends(auth_utils.require_login),
    db: Session = Depends(get_db),
):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)

    sudah_ada = (
        db.query(models.KelasMahasiswa)
        .filter(models.KelasMahasiswa.kelas_id == kelas_id, models.KelasMahasiswa.mahasiswa_id == mahasiswa_id)
        .first()
    )
    if not sudah_ada:
        db.add(models.KelasMahasiswa(kelas_id=kelas_id, mahasiswa_id=mahasiswa_id))
        db.commit()
    return RedirectResponse(f"/kelas/{kelas_id}", status_code=303)


@router.post("/{kelas_id}/keluarkan/{km_id}")
def keluarkan_mahasiswa(
    kelas_id: int, km_id: int, user=Depends(auth_utils.require_login), db: Session = Depends(get_db)
):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)
    km = db.query(models.KelasMahasiswa).filter(models.KelasMahasiswa.id == km_id).first()
    if km and km.kelas_id == kelas_id:
        db.delete(km)
        db.commit()
    return RedirectResponse(f"/kelas/{kelas_id}", status_code=303)


# ---------------------------------------------------------------- NILAI UTS/UAS + OVERRIDE TUGAS/KUIS
@router.post("/{kelas_id}/nilai/simpan-semua")
async def simpan_semua_nilai(
    kelas_id: int,
    request: Request,
    user=Depends(auth_utils.require_login),
    db: Session = Depends(get_db),
):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)

    def parse(v):
        if v is None:
            return None
        v = v.strip()
        if v == "":
            return None
        try:
            nilai = float(v)
        except ValueError:
            return None
        return max(0, min(100, nilai))

    form_data = await request.form()
    anggota = db.query(models.KelasMahasiswa).filter(models.KelasMahasiswa.kelas_id == kelas_id).all()

    for km in anggota:
        km.nilai_tugas = parse(form_data.get(f"tugas_{km.id}"))
        km.nilai_kuis = parse(form_data.get(f"kuis_{km.id}"))
        km.nilai_uts = parse(form_data.get(f"uts_{km.id}"))
        km.nilai_uas = parse(form_data.get(f"uas_{km.id}"))

    db.commit()
    return RedirectResponse(f"/kelas/{kelas_id}", status_code=303)


# ---------------------------------------------------------------- EXPORT
@router.get("/{kelas_id}/export/pdf")
def export_pdf(kelas_id: int, user=Depends(auth_utils.require_login), db: Session = Depends(get_db)):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)
    anggota = (
        db.query(models.KelasMahasiswa)
        .options(joinedload(models.KelasMahasiswa.mahasiswa))
        .filter(models.KelasMahasiswa.kelas_id == kelas_id)
        .join(models.Mahasiswa).order_by(models.Mahasiswa.nama).all()
    )
    buffer = pdf_helper.buat_pdf_transkrip(kelas, anggota)
    nama_file = f"transkrip_{kelas.mata_kuliah.nama_makul}_{kelas.nama_kelas}.pdf".replace(" ", "_")
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nama_file}"'},
    )


@router.get("/{kelas_id}/export/excel")
def export_excel(kelas_id: int, user=Depends(auth_utils.require_login), db: Session = Depends(get_db)):
    kelas = get_kelas_atau_403(kelas_id, user, db)
    if not kelas:
        return RedirectResponse("/kelas", status_code=303)
    anggota = (
        db.query(models.KelasMahasiswa)
        .options(joinedload(models.KelasMahasiswa.mahasiswa))
        .filter(models.KelasMahasiswa.kelas_id == kelas_id)
        .join(models.Mahasiswa).order_by(models.Mahasiswa.nama).all()
    )
    buffer = excel_helper.buat_excel_transkrip(kelas, anggota)
    nama_file = f"transkrip_{kelas.mata_kuliah.nama_makul}_{kelas.nama_kelas}.xlsx".replace(" ", "_")
    return StreamingResponse(
        buffer, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nama_file}"'},
    )