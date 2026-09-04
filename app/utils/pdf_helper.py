"""
File ini membuat file PDF transkrip nilai memakai library reportlab.
"""

import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def buat_pdf_transkrip(kelas, anggota_list) -> io.BytesIO:
    """
    Membuat PDF transkrip nilai untuk satu kelas.
    anggota_list = list of KelasMahasiswa (sudah include relasi mahasiswa)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    judul_style = ParagraphStyle("Judul", parent=styles["Heading1"], fontSize=14, spaceAfter=4)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.grey)

    elemen = []
    elemen.append(Paragraph("TRANSKRIP NILAI", judul_style))
    elemen.append(Paragraph(f"Mata Kuliah: {kelas.mata_kuliah.nama_makul}", sub_style))
    elemen.append(Paragraph(f"Kelas: {kelas.nama_kelas}", sub_style))
    elemen.append(Paragraph(f"Tahun Ajaran: {kelas.tahun_ajaran.nama_tahun_ajaran}", sub_style))
    elemen.append(Paragraph(f"Dosen Pengampu: {kelas.dosen.nama_lengkap if kelas.dosen else '-'}", sub_style))
    elemen.append(Spacer(1, 0.6 * cm))

    header = [
        "No", "NPM", "Nama",
        f"Tugas\n({kelas.bobot_tugas:.0f}%)",
        f"Kuis\n({kelas.bobot_kuis:.0f}%)",
        f"UTS\n({kelas.bobot_uts:.0f}%)",
        f"UAS\n({kelas.bobot_uas:.0f}%)",
    ]
    if kelas.pakai_bobot:
        header.append("Nilai\nAkhir")

    data = [header]
    for i, am in enumerate(anggota_list, start=1):
        def fmt(v):
            return "-" if v is None else f"{v:.1f}"
        baris = [
            str(i), am.mahasiswa.npm, am.mahasiswa.nama,
            fmt(am.nilai_tugas_final()), fmt(am.nilai_kuis_final()), fmt(am.nilai_uts), fmt(am.nilai_uas),
        ]
        if kelas.pakai_bobot:
            nilai_akhir = am.nilai_akhir()
            baris.append("-" if nilai_akhir is None else f"{nilai_akhir:.2f}")
        data.append(baris)

    lebar_kolom = [1.2 * cm, 2.8 * cm, 5.5 * cm, 1.9 * cm, 1.9 * cm, 1.9 * cm, 1.9 * cm]
    if kelas.pakai_bobot:
        lebar_kolom.append(2 * cm)

    tabel = Table(data, colWidths=lebar_kolom)
    tabel.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("ALIGN", (2, 1), (2, -1), "LEFT"),
    ]))
    elemen.append(tabel)

    elemen.append(Spacer(1, 1.5 * cm))
    ttd_style = ParagraphStyle("Ttd", parent=styles["Normal"], fontSize=10, alignment=2)
    elemen.append(Paragraph("Dosen Pengampu,", ttd_style))
    elemen.append(Spacer(1, 1.8 * cm))
    elemen.append(Paragraph(f"( {kelas.dosen.nama_lengkap if kelas.dosen else '..........................'} )", ttd_style))

    doc.build(elemen)
    buffer.seek(0)
    return buffer
