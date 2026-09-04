"""
File ini mendefinisikan STRUKTUR TABEL database.
Setiap class di bawah ini = 1 tabel di MySQL.
SQLAlchemy akan otomatis membuat tabel-tabel ini saat pertama kali dijalankan.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    """
    Tabel user login: Superadmin dan Dosen sama-sama disimpan di sini,
    dibedakan lewat kolom 'role'.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nama_lengkap = Column(String(150), nullable=False)
    role = Column(String(20), nullable=False)  # "superadmin" atau "dosen"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relasi: satu dosen bisa mengampu banyak kelas
    kelas_diampu = relationship("Kelas", back_populates="dosen")


class Fakultas(Base):
    __tablename__ = "fakultas"

    id = Column(Integer, primary_key=True, index=True)
    nama_fakultas = Column(String(150), nullable=False)

    prodi_list = relationship("Prodi", back_populates="fakultas", cascade="all, delete-orphan")


class Prodi(Base):
    __tablename__ = "prodi"

    id = Column(Integer, primary_key=True, index=True)
    nama_prodi = Column(String(150), nullable=False)
    fakultas_id = Column(Integer, ForeignKey("fakultas.id"), nullable=False)

    fakultas = relationship("Fakultas", back_populates="prodi_list")
    makul_list = relationship("MataKuliah", back_populates="prodi", cascade="all, delete-orphan")


class MataKuliah(Base):
    __tablename__ = "mata_kuliah"

    id = Column(Integer, primary_key=True, index=True)
    kode_makul = Column(String(20), nullable=True)
    nama_makul = Column(String(150), nullable=False)
    sks = Column(Integer, default=2)
    prodi_id = Column(Integer, ForeignKey("prodi.id"), nullable=False)

    prodi = relationship("Prodi", back_populates="makul_list")
    kelas_list = relationship("Kelas", back_populates="mata_kuliah", cascade="all, delete-orphan")


class TahunAjaran(Base):
    __tablename__ = "tahun_ajaran"

    id = Column(Integer, primary_key=True, index=True)
    nama_tahun_ajaran = Column(String(50), nullable=False)  # contoh: "2024/2025 Ganjil"
    is_active = Column(Boolean, default=True)

    kelas_list = relationship("Kelas", back_populates="tahun_ajaran")


class Kelas(Base):
    """
    Kelas = gabungan Mata Kuliah + Tahun Ajaran + Dosen pengampu.
    Contoh: "Basis Data - Kelas A" di tahun ajaran "2024/2025 Ganjil" diampu Pak Budi.
    Bobot nilai disimpan per Kelas (karena tiap kelas/matkul bisa beda bobot).
    """
    __tablename__ = "kelas"

    id = Column(Integer, primary_key=True, index=True)
    nama_kelas = Column(String(50), nullable=False)  # contoh: "A", "B", "Reguler Pagi"

    mata_kuliah_id = Column(Integer, ForeignKey("mata_kuliah.id"), nullable=False)
    tahun_ajaran_id = Column(Integer, ForeignKey("tahun_ajaran.id"), nullable=False)
    dosen_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Bobot nilai dalam persen, total harus 100
    bobot_tugas = Column(Float, default=20)
    bobot_kuis = Column(Float, default=20)
    bobot_uts = Column(Float, default=30)
    bobot_uas = Column(Float, default=30)

    # Kalau False: bobot & Nilai Akhir tidak dipakai sama sekali untuk kelas ini
    # (dipakai kalau nilai per komponen mau diimpor manual ke SIAKAD, tanpa perlu nilai akhir dari sini)
    pakai_bobot = Column(Boolean, default=True)

    mata_kuliah = relationship("MataKuliah", back_populates="kelas_list")
    tahun_ajaran = relationship("TahunAjaran", back_populates="kelas_list")
    dosen = relationship("User", back_populates="kelas_diampu")

    anggota = relationship("KelasMahasiswa", back_populates="kelas", cascade="all, delete-orphan")
    item_nilai_list = relationship("ItemNilai", back_populates="kelas", cascade="all, delete-orphan", order_by="ItemNilai.urutan")


class Mahasiswa(Base):
    """
    Data mahasiswa bersifat umum (Nama + NPM), tidak terikat prodi/kelas tertentu.
    Nanti di-assign manual ke kelas lewat tabel KelasMahasiswa.
    """
    __tablename__ = "mahasiswa"

    id = Column(Integer, primary_key=True, index=True)
    npm = Column(String(30), unique=True, nullable=False, index=True)
    nama = Column(String(150), nullable=False)

    kelas_diikuti = relationship("KelasMahasiswa", back_populates="mahasiswa", cascade="all, delete-orphan")


class KelasMahasiswa(Base):
    """
    Tabel penghubung: mahasiswa mana saja yang ada di kelas mana.
    Nilai UTS & UAS disimpan langsung di sini.
    Nilai Tugas & Kuis: kalau kolom nilai_tugas/nilai_kuis di sini diisi manual,
    itu dipakai sebagai OVERRIDE. Kalau kosong, otomatis dihitung dari rata-rata
    "Nilai Harian" (tabel NilaiItem) yang diisi per pertemuan/per tugas.
    """
    __tablename__ = "kelas_mahasiswa"
    __table_args__ = (UniqueConstraint("kelas_id", "mahasiswa_id", name="uq_kelas_mahasiswa"),)

    id = Column(Integer, primary_key=True, index=True)
    kelas_id = Column(Integer, ForeignKey("kelas.id"), nullable=False)
    mahasiswa_id = Column(Integer, ForeignKey("mahasiswa.id"), nullable=False)

    # nilai_tugas & nilai_kuis di sini = OVERRIDE MANUAL (opsional). Kalau None, dihitung otomatis.
    nilai_tugas = Column(Float, nullable=True)
    nilai_kuis = Column(Float, nullable=True)
    nilai_uts = Column(Float, nullable=True)
    nilai_uas = Column(Float, nullable=True)

    kelas = relationship("Kelas", back_populates="anggota")
    mahasiswa = relationship("Mahasiswa", back_populates="kelas_diikuti")
    nilai_harian = relationship("NilaiItem", back_populates="kelas_mahasiswa", cascade="all, delete-orphan")

    def rata_rata_harian(self, jenis: str):
        """Hitung rata-rata nilai harian (tugas/kuis) yang sudah diisi. None kalau belum ada yang diisi."""
        nilai_list = [
            ni.nilai for ni in self.nilai_harian
            if ni.item_nilai.jenis == jenis and ni.nilai is not None
        ]
        if not nilai_list:
            return None
        return round(sum(nilai_list) / len(nilai_list), 2)

    def nilai_tugas_final(self):
        """Nilai Tugas yang dipakai untuk hitung nilai akhir: override manual kalau diisi, else rata-rata harian."""
        if self.nilai_tugas is not None:
            return self.nilai_tugas
        return self.rata_rata_harian("tugas")

    def nilai_kuis_final(self):
        """Nilai Kuis yang dipakai untuk hitung nilai akhir: override manual kalau diisi, else rata-rata harian."""
        if self.nilai_kuis is not None:
            return self.nilai_kuis
        return self.rata_rata_harian("kuis")

    def nilai_akhir(self):
        """Menghitung nilai akhir berdasarkan bobot kelas. Return None kalau bobot dimatikan atau ada komponen kosong."""
        k = self.kelas
        if not k.pakai_bobot:
            return None
        tugas = self.nilai_tugas_final()
        kuis = self.nilai_kuis_final()
        komponen = [tugas, kuis, self.nilai_uts, self.nilai_uas]
        if any(v is None for v in komponen):
            return None
        total = (
            (tugas * k.bobot_tugas)
            + (kuis * k.bobot_kuis)
            + (self.nilai_uts * k.bobot_uts)
            + (self.nilai_uas * k.bobot_uas)
        ) / 100
        return round(total, 2)


class ItemNilai(Base):
    """
    Satu 'kolom' nilai harian di sebuah kelas, contoh: "Tugas 1", "Tugas Pertemuan 5", "Kuis 2".
    jenis: "tugas" atau "kuis"
    """
    __tablename__ = "item_nilai"

    id = Column(Integer, primary_key=True, index=True)
    kelas_id = Column(Integer, ForeignKey("kelas.id"), nullable=False)
    jenis = Column(String(10), nullable=False)  # "tugas" atau "kuis"
    nama = Column(String(100), nullable=False)
    urutan = Column(Integer, default=0)

    kelas = relationship("Kelas", back_populates="item_nilai_list")
    nilai_list = relationship("NilaiItem", back_populates="item_nilai", cascade="all, delete-orphan")


class NilaiItem(Base):
    """Nilai satu mahasiswa untuk satu ItemNilai (satu sel di spreadsheet nilai harian/kuis)."""
    __tablename__ = "nilai_item"
    __table_args__ = (UniqueConstraint("item_nilai_id", "kelas_mahasiswa_id", name="uq_item_km"),)

    id = Column(Integer, primary_key=True, index=True)
    item_nilai_id = Column(Integer, ForeignKey("item_nilai.id"), nullable=False)
    kelas_mahasiswa_id = Column(Integer, ForeignKey("kelas_mahasiswa.id"), nullable=False)
    nilai = Column(Float, nullable=True)

    item_nilai = relationship("ItemNilai", back_populates="nilai_list")
    kelas_mahasiswa = relationship("KelasMahasiswa", back_populates="nilai_harian")
