# SINDO — Sistem Input Nilai Dosen

Aplikasi web pribadi untuk input & kelola nilai mahasiswa (Tugas, Kuis, UTS, UAS), dengan struktur Fakultas → Prodi → Mata Kuliah → Kelas, role Superadmin & Dosen, serta cetak transkrip ke PDF/Excel.

Panduan ini ditulis **sangat detail untuk pemula**. Ikuti dari atas ke bawah, jangan ada yang dilompat ya, boss.

---

## 1. Yang Perlu Disiapkan Dulu

1. **Laragon** — sudah terinstall (untuk MySQL & phpMyAdmin). Kalau belum, download di https://laragon.org/download/ (pilih versi Full), install seperti biasa.
2. **Python 3.10 ke atas** — cek dengan buka Command Prompt / PowerPoint lalu ketik:
   ```
   python --version
   ```
   Kalau belum ada, download di https://www.python.org/downloads/ — **PENTING**: saat install, centang kotak "Add python.exe to PATH".
3. **VSCode** — sudah terinstall (sesuai kebiasaan boss).

---

## 2. Menyiapkan Database di Laragon

1. Buka aplikasi **Laragon**.
2. Klik tombol **Start All** (supaya MySQL jalan). Tunggu sampai tulisan Apache & MySQL berwarna hijau/aktif.
3. Klik menu **Database** di Laragon (atau klik kanan tray icon Laragon → Database) — ini akan membuka **phpMyAdmin** di browser.
4. Di phpMyAdmin, klik tab **Databases** di bagian atas.
5. Di kolom "Create database", ketik nama: `nilai_mahasiswa`
6. Pilih Collation: `utf8mb4_general_ci`
7. Klik **Create**.

Selesai — database kosong sudah siap, nanti tabel-tabelnya akan dibuat OTOMATIS oleh aplikasi saat pertama kali dijalankan (boss tidak perlu bikin tabel manual).

> Default Laragon: user `root`, password **kosong**, port **3306**. Kalau instalasi Laragon boss beda (misal sudah ganti password root), catat dan sesuaikan nanti di langkah 4.

---

## 3. Menyiapkan Folder Project

1. Extract/pindahkan folder `nilai_mahasiswa` yang saya berikan ke lokasi pilihan boss, misalnya:
   ```
   D:\Python\nilai_mahasiswa
   ```
2. Buka folder itu dengan **VSCode**: File → Open Folder → pilih `D:\Python\nilai_mahasiswa`.
3. Buka **Terminal** di VSCode (menu Terminal → New Terminal), pastikan lokasinya di dalam folder project itu.

---

## 4. Membuat Virtual Environment & Install Library

Di terminal VSCode (pastikan posisi di folder `nilai_mahasiswa`), jalankan satu-satu:

```bash
python -m venv venv
```
Ini membuat folder `venv` (virtual environment), sama seperti kebiasaan boss di project SiGEMOY.

Aktifkan virtual environment:
```bash
venv\Scripts\activate
```
Kalau berhasil, di depan baris terminal akan muncul tulisan `(venv)`.

Install semua library yang dibutuhkan:
```bash
pip install -r requirements.txt
```
Tunggu sampai selesai (agak lama karena banyak library, terutama `reportlab` untuk PDF).

---

## 5. Konfigurasi Koneksi Database (.env)

1. Di folder project, cari file `.env.example`.
2. **Copy** file itu, lalu **rename hasil copy-annya** menjadi `.env` (buang kata "example").
   - Di VSCode: klik kanan `.env.example` → Copy, lalu klik kanan folder → Paste, lalu rename jadi `.env`.
3. Buka file `.env`, isinya seperti ini:
   ```
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=nilai_mahasiswa

   SECRET_KEY=ganti-dengan-string-acak-yang-panjang-dan-rahasia
   ```
4. Kalau setup Laragon boss standar (default), **tidak perlu diubah apa-apa** kecuali:
   - `DB_PASSWORD` — isi kalau MySQL Laragon boss memang punya password.
   - `SECRET_KEY` — ganti dengan teks acak apa saja (bebas, minimal 20 karakter), contoh: `sindo-rahasia-2025-jangan-disebar-xyz123`. Ini dipakai untuk mengamankan sesi login.

---

## 6. Membuat Akun Superadmin Pertama

Masih di terminal VSCode (pastikan `(venv)` masih aktif), jalankan:

```bash
python seed_admin.py
```

Kalau berhasil, akan muncul tulisan seperti ini:
```
==================================================
Akun Superadmin berhasil dibuat!
Username : superadmin
Password : admin123
PENTING: segera login dan ganti password lewat halaman yang sesuai.
==================================================
```

**Catat username & password ini.** Ini akan otomatis membuat semua tabel di database `nilai_mahasiswa` (boss bisa cek di phpMyAdmin, tabelnya sudah muncul).

> Catatan: fitur "ganti password sendiri" untuk superadmin belum ada di versi ini (karena skalanya kecil/pribadi, sesuai request awal). Kalau nanti mau ganti password superadmin, kabari saya, saya buatkan script kecil lagi.

---

## 7. Menjalankan Aplikasi

Masih di terminal yang sama, jalankan:

```bash
uvicorn app.main:app --reload
```

Kalau berhasil, akan muncul tulisan:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Buka browser, akses:
```
http://127.0.0.1:8000
```

Akan otomatis diarahkan ke halaman login. Masuk dengan `superadmin` / `admin123`.

> Untuk menghentikan server: tekan `CTRL + C` di terminal.
> Setiap mau menjalankan lagi di lain waktu: buka terminal di folder project → `venv\Scripts\activate` → `uvicorn app.main:app --reload`.

---

## 8. Alur Pemakaian (Urutan yang Disarankan)

1. **Login sebagai Superadmin.**
2. Menu **Fakultas** → tambah minimal 1 fakultas (contoh: "Fakultas Teknik").
3. Menu **Program Studi** → tambah prodi, pilih fakultasnya (contoh: "Teknik Informatika").
4. Menu **Mata Kuliah** → tambah mata kuliah, pilih prodinya (contoh: "Basis Data", SKS 3).
5. Menu **Tahun Ajaran** → tambah, contoh: "2024/2025 Ganjil".
6. Menu **Akun Dosen** → tambah akun dosen (nama, username, password). Kalau boss mau input nilai sendiri, bisa buatkan akun dosen atas nama boss juga, atau pakai akun superadmin langsung (superadmin juga bisa input nilai & assign mahasiswa).
7. Menu **Kelas** → klik "+ Buat Kelas", isi Nama Kelas (contoh: "A"), pilih Mata Kuliah, Tahun Ajaran, dan Dosen Pengampu.
8. Menu **Data Mahasiswa** → import lewat Excel (download template dulu, isi kolom NPM & Nama, lalu upload) atau tambah manual satu-satu.
   - Begitu mahasiswa sudah di-assign ke kelas manapun, kolom **Kelas** di tabel ini otomatis nunjukin badge kelas yang diikuti (klik badge-nya buat langsung ke halaman kelas itu).
   - Ada filter **Fakultas / Program Studi / Kelas** (otomatis apply saat dipilih) dan kotak **pencarian nama/NPM** di kanan atas tabel.
   - Untuk akun Dosen, filter & badge kelas otomatis dibatasi cuma ke kelas yang dia ampu sendiri.
9. Buka **detail Kelas** yang sudah dibuat → bagian "Tambahkan Mahasiswa ke Kelas Ini" → assign mahasiswa yang sudah didata ke kelas tersebut.
10. **Nilai Tugas Harian & Kuis** (spreadsheet):
    - Di bagian "Nilai Tugas Harian", tambah kolom baru tiap ada tugas baru (contoh: "Tugas Pertemuan 1"), isi nilai tiap mahasiswa → Simpan. Bisa tambah kolom sebanyak apapun, kapan saja, dan bisa dihapus kalau salah bikin.
    - Nilai Tugas final otomatis dihitung dari **rata-rata semua kolom** yang sudah diisi. Bagian "Nilai Kuis" caranya sama persis.
11. Nilai UTS & UAS diisi manual di tabel "Ringkasan Nilai & Nilai Akhir" di bagian bawah halaman kelas.
12. Kolom **Tugas** & **Kuis** di tabel ringkasan otomatis terisi (angka abu-abu/placeholder) dari rata-rata di poin 10. Kalau boss mau nilainya beda dari rata-rata (misal kasih bonus), tinggal **ketik manual** — nilai itu jadi override, menggantikan rata-rata otomatis. Kosongkan lagi untuk balik ke otomatis.
13. Kalau perlu ubah bobot (default 20/20/30/30) → buka bagian "Bobot Komponen Nilai" → ubah → total wajib 100%.
14. Cetak transkrip lewat tombol **Cetak PDF** atau **Export Excel** di halaman detail kelas (otomatis pakai nilai final).
15. **Matikan Bobot & Nilai Akhir** (opsional): kalau nilai per komponen (Tugas/Kuis/UTS/UAS) mau diimpor manual ke SIAKAD resmi dan gak butuh nilai akhir dari sistem ini, buka bagian "Bobot Komponen Nilai & Nilai Akhir" → klik toggle "Gunakan Bobot & Hitung Nilai Akhir" jadi OFF. Kolom Nilai Akhir otomatis hilang dari tabel & export; nilai Tugas/Kuis/UTS/UAS tetap tersimpan seperti biasa. Bisa dinyalakan lagi kapan saja.

---

## 9. Struktur Folder (untuk referensi)

```
nilai_mahasiswa/
├── venv/                      ← virtual environment (dibuat sendiri, tidak usah diedit)
├── app/
│   ├── main.py                ← entry point aplikasi
│   ├── database.py            ← koneksi ke MySQL
│   ├── models.py              ← struktur tabel database
│   ├── auth.py                ← login & pembatasan akses
│   ├── routers/                ← semua "route"/endpoint web dikelompokkan di sini
│   │   ├── auth.py            ← login/logout
│   │   ├── superadmin.py      ← fakultas, prodi, makul, tahun ajaran, dosen
│   │   ├── dosen.py           ← dashboard dosen
│   │   ├── kelas.py           ← kelas, nilai, bobot, export
│   │   └── mahasiswa.py       ← data mahasiswa & import excel
│   ├── templates/              ← file HTML (tampilan)
│   ├── static/                 ← file CSS/JS custom (kalau ada nanti)
│   └── utils/
│       ├── excel_helper.py    ← import/export Excel
│       └── pdf_helper.py      ← generate PDF transkrip
├── seed_admin.py               ← script bikin superadmin pertama
├── requirements.txt             ← daftar library Python
└── .env                        ← konfigurasi database (jangan di-share ke orang lain)
```

---

## 10. Masalah Umum & Solusinya

**"uvicorn tidak dikenali sebagai perintah"**
→ Pastikan `(venv)` aktif (`venv\Scripts\activate`). Kalau masih gagal, coba `pip install -r requirements.txt` ulang.

**Error koneksi database (`Can't connect to MySQL server`)**
→ Pastikan Laragon sudah di-klik **Start All** dan MySQL statusnya aktif (hijau).

**Error `Access denied for user 'root'`**
→ Cek `DB_PASSWORD` di file `.env`, sesuaikan dengan password MySQL Laragon boss.

**Halaman muncul tapi tidak ada tampilan/berantakan**
→ Pastikan komputer terhubung internet, karena Tailwind CSS & font dimuat dari CDN (belum di-download lokal).

**Lupa password superadmin**
→ Karena tidak ada fitur reset via email (sesuai desain awal), boss bisa hapus baris user tersebut langsung lewat phpMyAdmi (tabel `users`), lalu jalankan ulang `python seed_admin.py`.

**Ingin ganti password akun `admin123` bawaan**
→ Login sebagai superadmin → belum ada tombol ganti password sendiri di versi ini. Sementara, boss bisa reset password dosen manapun (termasuk cara serupa untuk superadmin bisa saya tambahkan kalau dibutuhkan — tinggal bilang).

---

## 11. Catatan Pengembangan Lanjutan (Opsional, Kalau Nanti Dibutuhkan)

Beberapa hal yang SENGAJA belum dibuat karena di luar scope awal, tapi bisa ditambahkan kapan saja kalau boss mau:
- Halaman ganti password untuk superadmin sendiri
- Riwayat/log perubahan nilai
- Grade huruf (A/B/C/D) selain angka
- Filter & pencarian di tabel-tabel besar
- Multi-tahun-ajaran view (rekap nilai mahasiswa lintas semester)

Tinggal bilang ke saya kalau mau ditambahkan salah satu dari ini.

---

Kalau ada error yang muncul saat menjalankan, screenshot atau copy pesan errornya, kirim ke saya (Langit) — nanti saya bantu debug bareng-bareng, boss.
