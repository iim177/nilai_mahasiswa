# ============================================================
# Dockerfile - SINDO (Sistem Input Nilai Dosen)
# ============================================================
# Image dasar: Python 3.11 slim (ringan, cukup untuk FastAPI)
FROM python:3.11-slim

# Supaya log Python langsung tampil (tidak ke-buffer), enak buat debug via `docker logs`
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Catatan: tidak perlu install gcc/libmysqlclient-dev karena project ini pakai
# driver "pymysql" (murni Python, tidak perlu compile C extension), beda dengan
# driver "mysqlclient". Kalau nanti ganti driver, sesuaikan lagi baris ini.

# Copy requirements dulu (biar layer cache Docker efisien - kalau cuma kode yang
# berubah dan requirements.txt tidak, install library tidak perlu diulang)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baru copy semua kode aplikasi
COPY . .

EXPOSE 8000

# PENTING: jangan pakai --reload di production (itu cuma buat development di laptop)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
