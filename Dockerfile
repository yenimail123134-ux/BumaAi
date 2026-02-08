# Python 3.11-slim: Hafif ve hızlı
FROM python:3.11-slim

# DNS çözücüleri ve aiohttp speedups için gerekli sistem kütüphanelerini ekliyoruz
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libc-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizini
WORKDIR /code

# Pip'i güncelliyoruz
RUN pip install --no-cache-dir --upgrade pip

# Gereksinimleri kopyala ve yükle
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

# Tüm kodları içeri al
COPY . .

# Logların anlık düşmesi için (Buffering kapatıldı)
ENV PYTHONUNBUFFERED=1

# Botu ateşle
CMD ["python", "app.py"]