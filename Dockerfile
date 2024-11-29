# 1. Python imajından başlıyoruz
FROM python:3.10-slim

# 2. Çalışma dizini oluştur ve buraya geç
WORKDIR /code

# 3. Sistemde eksik paketleri yükle (örneğin PostgreSQL için `libpq-dev`)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 4. Pip'i güncelle
RUN pip install --upgrade pip

# 5. Gereksinim dosyasını kopyala ve bağımlılıkları yükle
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 6. Proje dosyalarını kopyala
COPY . .

# 7. Django sunucusunu çalıştır
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
