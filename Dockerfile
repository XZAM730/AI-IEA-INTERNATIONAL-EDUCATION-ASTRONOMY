# 1. Gunakan Python versi ringan
FROM python:3.10-slim

# 2. Atur folder kerja
WORKDIR /app

# 3. Install update sistem dasar
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy file requirements dan install library
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy seluruh kode aplikasi ke dalam server
COPY . .

# 6. Buat user khusus (Agar aman & diterima Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 7. Buka Port 7860 (Standar Hugging Face)
EXPOSE 7860

# 8. Jalankan aplikasi
CMD ["python", "app.py"]

