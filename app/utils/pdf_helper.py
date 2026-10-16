"""
File ini membuat file PDF transkrip nilai memakai library reportlab.
"""

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Margin kiri/kanan dibuat tipis supaya kolom Nama bisa lebar
MARGIN_SAMPING = 1.0 * cm


def buat_pdf_transkrip(kelas, anggota_list) -> io.BytesIO:
    """
    Membuat PDF transkrip nilai untuk satu kelas.
    anggota_list = list of KelasMahasiswa (sudah include relasi mahasiswa)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=MARGIN_SAMPING, rightMargin=MARGIN_SAMPING,
    )
    styles = getSampleStyleSheet()
    judul_style = ParagraphStyle("Judul", parent=styles["Heading1"], fontSize=14, spaceAfter=4)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    # Nama dibungkus (Paragraph) supaya nama yang sangat panjang turun ke baris bawah,
    # tidak menimpa kolom di sebelahnya.
    nama_style = ParagraphStyle("NamaMhs", parent=styles["Normal"], fontSize=9, leading=11, alignment=0)

    elemen = []
    elemen.append(Paragraph("TRANSKRIP NILAI", judul_style))
    elemen.append(Paragraph(f"Mata Kuliah: {escape(kelas.mata_kuliah.nama_makul)}", sub_style))
    elemen.append(Paragraph(f"Kelas: {escape(kelas.nama_kelas)}", sub_style))
    elemen.append(Paragraph(f"Tahun Ajaran: {escape(kelas.tahun_ajaran.nama_tahun_ajaran)}", sub_style))
    elemen.append(Paragraph(f"Dosen Pengampu: {escape(kelas.dosen.nama_lengkap) if kelas.dosen else '-'}", sub_style))
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

    def fmt(v):
        return "-" if v is None else f"{v:.1f}"

    data = [header]
    for i, am in enumerate(anggota_list, start=1):
        baris = [
            str(i), am.mahasiswa.npm, Paragraph(escape(am.mahasiswa.nama), nama_style),
            fmt(am.nilai_tugas_final()), fmt(am.nilai_kuis_final()), fmt(am.nilai_uts), fmt(am.nilai_uas),
        ]
        if kelas.pakai_bobot:
            nilai_akhir = am.nilai_akhir()
            baris.append("-" if nilai_akhir is None else f"{nilai_akhir:.2f}")
        data.append(baris)

    # Lebar kolom: kolom lain tetap kecil, kolom Nama mengambil SISA lebar halaman.
    lebar_halaman = A4[0] - 2 * MARGIN_SAMPING
    lebar_tetap = [1.0 * cm, 2.6 * cm] + [1.7 * cm] * 4          # No, NPM, Tugas, Kuis, UTS, UAS
    if kelas.pakai_bobot:
        lebar_tetap.append(1.8 * cm)                               # Nilai Akhir
    lebar_nama = lebar_halaman - sum(lebar_tetap)
    lebar_kolom = lebar_tetap[:2] + [lebar_nama] + lebar_tetap[2:]

    tabel = Table(data, colWidths=lebar_kolom, repeatRows=1)       # header diulang di halaman berikutnya
    tabel.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("ALIGN", (2, 0), (2, -1), "LEFT"),
        ("LEFTPADDING", (2, 0), (2, -1), 6),
    ]))
    elemen.append(tabel)

    elemen.append(Spacer(1, 1.5 * cm))
    ttd_style = ParagraphStyle("Ttd", parent=styles["Normal"], fontSize=10, alignment=2)
    elemen.append(Paragraph("Dosen Pengampu,", ttd_style))
    elemen.append(Spacer(1, 1.8 * cm))
    nama_ttd = escape(kelas.dosen.nama_lengkap) if kelas.dosen else '..........................'
    elemen.append(Paragraph(f"( {nama_ttd} )", ttd_style))

    doc.build(elemen)
    buffer.seek(0)
    return buffer
