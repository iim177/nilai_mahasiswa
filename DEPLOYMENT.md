# Panduan Deploy SINDO ke VPS via Docker

Panduan ini fokus jawab kekhawatiran utama: **biar config di laptop & di server gak pernah beda-beda tanpa sadar.**

---

## 1. Prinsip Dasar (baca ini dulu)

> **Kode ikut Git. Config (`.env`) TIDAK PERNAH ikut Git.**

- File `.env` isinya rahasia (password database, secret key) dan **beda-beda tiap tempat** — laptop boss pakai Laragon lokal, VPS pakai MySQL VPS.
- `.env` sudah otomatis diabaikan Git (lihat `.gitignore`), jadi dia **tidak akan pernah ke-push atau ke-pull**.
- Yang jadi "kontrak" antara laptop dan VPS adalah `.env.example` — daftar variabel yang WAJIB ada, tapi tanpa isi rahasianya. Kalau nanti nambah variabel config baru, update juga `.env.example` di Git, supaya VPS tahu ada variabel baru yang perlu diisi.
- Konsekuensinya: **VPS butuh file `.env` sendiri, dibuat manual SEKALI di VPS**, tidak akan berubah otomatis walau boss `git push` dari laptop berkali-kali (memang harus begitu, demi keamanan).

---

## 2. Setup Git (kalau belum)

Dari folder project di laptop:
```bash
git init
git add .
git commit -m "Initial commit - SINDO"
git remote add origin <URL repo Git boss>
git push -u origin main
```

`.gitignore` sudah disiapkan supaya `venv/`, `__pycache__/`, `.env`, dan `*.db` tidak ikut ke-push. **Cek dulu sebelum push pertama kali**:
```bash
git status
```
Pastikan `.env` TIDAK muncul di daftar file yang mau di-commit. Kalau muncul, berarti ada masalah di `.gitignore` — jangan lanjut push, kabari saya.

---

## 3. Setup Pertama Kali di VPS

```bash
git clone <URL repo Git boss>
cd nilai_mahasiswa
cp .env.example .env
nano .env    # atau vim/editor lain, isi sesuai kondisi VPS (lihat bagian 4)
```

---

## 4. Isi `.env` di VPS (bagian paling penting)

Karena MySQL ada **langsung di VPS** (bukan di Docker), dan aplikasi jalan **di dalam Docker**, container perlu cara khusus buat "menembus keluar" dan connect ke MySQL di host-nya. `127.0.0.1` di dalam container itu artinya "container itu sendiri", BUKAN VPS-nya — ini kesalahan paling umum orang baru pakai Docker.

**Isi `.env` di VPS seperti ini:**
```
DB_HOST=host.docker.internal
DB_PORT=3306
DB_USER=root_atau_user_mysql_vps
DB_PASSWORD=password_mysql_vps
DB_NAME=nilai_mahasiswa
SECRET_KEY=string-acak-beda-dari-yang-di-laptop
```

`docker-compose.yml` yang sudah disiapkan otomatis menambahkan `host.docker.internal` supaya alamat itu valid di Linux (biasanya cuma otomatis kebaca di Docker Desktop, jadi kita tambahkan manual lewat `extra_hosts`).

**Kalau ternyata cara di atas masih tidak bisa connect**, cara alternatif (pilih salah satu):
- Cek MySQL VPS dengar di alamat mana: `sudo netstat -tlnp | grep 3306`. Kalau MySQL cuma dengar di `127.0.0.1` (bukan `0.0.0.0`), perlu diubah dulu di `/etc/mysql/mysql.conf.d/mysqld.cnf` (`bind-address = 0.0.0.0`) lalu restart MySQL — **tapi hati-hati**, ini bikin MySQL bisa diakses dari luar juga, pastikan firewall VPS (`ufw`) memblokir port 3306 dari luar dan cuma izinkan dari Docker network.
- Atau jalankan container dengan `network_mode: host` di `docker-compose.yml` (khusus Linux) — dengan begini `DB_HOST=127.0.0.1` di `.env` VPS jadi bisa dipakai lagi, karena container "berbagi jaringan" dengan VPS-nya. Ini lebih simpel tapi container jadi tidak terisolasi jaringannya dari container Docker lain.

Kalau boss butuh bantuan pas nyampe langkah ini dan masih gagal connect, kirim pesan error `docker logs sindo_app`-nya ke saya.

---

## 5. Build & Jalankan di VPS

```bash
docker compose up -d --build
```

Cek jalan atau tidak:
```bash
docker compose logs -f sindo
```

Aplikasi bisa diakses langsung di `http://<IP-VPS>:5003` (setelah firewall VPS izinkan port itu — cek dulu `sudo ufw status`, kalau belum ada aturan buat 5003, tambahkan: `sudo ufw allow 5003/tcp`).

**Kenapa port 5003, bukan 8000?** Karena di VPS boss port 80, 8081, 8090, 8091, 9000, 9443, 5001, 5002 sudah dipakai container lain. Port `5003` di sini adalah port yang dibuka di VPS (host); di dalam `docker-compose.yml`, container tetap jalan di port `8000` secara internal — pemetaannya `"5003:8000"` (host:container), jadi boss tidak perlu ubah apapun di kode aplikasi sendiri.

---

## 6. Setup Cloudflare Tunnel (biar bisa diakses via domain)

VPS boss sudah punya container `cloudflared` yang jalan (dipakai kemungkinan oleh `siakad-webserver`). Cloudflare Tunnel bekerja dengan 1 file config (`config.yml`, biasanya ada di `~/.cloudflared/` atau volume yang di-mount ke container `cloudflared`) yang berisi daftar *ingress rules* — aturan "domain/subdomain ini diarahkan ke service mana".

Langkah-langkahnya:

1. **Cek file config `cloudflared` yang sudah ada** — biasanya berupa file `config.yml` dengan isi kira-kira begini:
   ```yaml
   tunnel: <tunnel-id>
   credentials-file: /etc/cloudflared/<tunnel-id>.json
   ingress:
     - hostname: siakad.contoh.ac.id
       service: http://siakad-webserver:80
     - service: http_status:404
   ```
   Cara cek lokasinya: `docker inspect cloudflared | grep -A5 Mounts` (lihat volume yang di-mount ke container itu), atau `docker exec cloudflared cat /etc/cloudflared/config.yml`.

2. **Tambahkan entri baru untuk SINDO** sebelum baris `- service: http_status:404` (baris itu harus selalu paling akhir):
   ```yaml
     - hostname: sindo.contoh.ac.id
       service: http://sindo_app:8000
   ```
   Catatan: `service` di sini pakai **nama container** (`sindo_app`) dan **port internal** (`8000`), BUKAN port host (`5003`) — soalnya `cloudflared` berkomunikasi ke container lain lewat jaringan Docker internal, bukan lewat IP publik VPS. Ini juga berarti **container `sindo_app` dan `cloudflared` harus satu Docker network** yang sama. Kalau `cloudflared` sekarang ada di network tersendiri (misal `siakad_default`), boss perlu tambahkan `sindo_app` ke network yang sama itu juga di `docker-compose.yml`, atau buat network baru dan sambungkan `cloudflared` ke situ juga.

3. **Tambahkan DNS record** di dashboard Cloudflare (`sindo.contoh.ac.id` → CNAME ke tunnel, biasanya lewat `cloudflared tunnel route dns <tunnel-id> sindo.contoh.ac.id`).

4. Restart `cloudflared`: `docker restart cloudflared`.

**Kalau boss bisa share isi file `config.yml` cloudflared yang sekarang** (boleh disensor bagian tunnel-id/credentials kalau perlu), gue bisa bantu tuliskan baris ingress yang pas persis buat SINDO, sekalian sesuaikan network di `docker-compose.yml` biar `sindo_app` bisa "ketemu" `cloudflared`.

---

## 7. Alur Update Selanjutnya (biar tidak drift)

Tiap ada perubahan kode:

**Di laptop:**
```bash
git add .
git commit -m "Deskripsi perubahan"
git push
```

**Di VPS:**
```bash
git pull
docker compose up -d --build
```

Itu saja. Karena `.env` tidak ikut ter-pull/ter-push, config VPS **tidak akan pernah keubah/ke-timpa tanpa sengaja** oleh update dari laptop.

**Kapan perlu edit `.env` di VPS secara manual?** Cuma kalau boss memang menambah variabel config BARU (misal butuh API key baru). Kalau itu terjadi, saya akan selalu update `.env.example` juga di kode, jadi tinggal boss bandingkan `.env.example` terbaru vs `.env` yang ada di VPS untuk lihat apa yang kurang.

---

## 8. Soal Migrasi Database

Aplikasi ini sudah otomatis menjalankan migrasi kolom baru tiap kali start (lihat `jalankan_migrasi_ringan()` di `app/database.py`) — jadi kalau ada update yang menambah kolom baru ke tabel yang sudah ada, boss **tidak perlu langkah manual tambahan** di VPS. Cukup `docker compose up -d --build` seperti biasa, migrasi jalan otomatis begitu container start.

---

## 9. Checklist Sebelum Deploy Pertama Kali

- [ ] `.env` sudah dibuat manual di VPS (bukan hasil clone/pull dari Git)
- [ ] `DB_HOST` di VPS sudah pakai `host.docker.internal` (bukan `127.0.0.1`)
- [ ] MySQL di OS VPS sudah punya database `nilai_mahasiswa` (buat manual dulu kalau belum ada, sama seperti langkah bikin database di Laragon — bisa lewat `mysql -u root -p` langsung di VPS)
- [ ] MySQL di OS VPS sudah izinkan koneksi dari Docker (`bind-address` bukan cuma `127.0.0.1`, dan user MySQL yang dipakai punya akses dari host selain `localhost` — lihat bagian 4)
- [ ] Firewall VPS (`ufw`) sudah `allow 5003/tcp` (kalau mau akses langsung IP:port) — kalau full lewat Cloudflare Tunnel, port 5003 sebenarnya tidak perlu dibuka ke publik sama sekali, cukup bisa diakses dari container `cloudflared` di jaringan Docker yang sama
- [ ] Container `sindo_app` sudah satu Docker network dengan `cloudflared` (kalau mau pakai Tunnel)
- [ ] `git status` di laptop tidak menampilkan `.env` sebelum push pertama kali
