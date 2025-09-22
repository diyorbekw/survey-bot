FROM python:3.11-slim

WORKDIR /app

# Sistem kutubxonalarini o'rnatish
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Python kutubxonalarini ko'chirish va o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot kodini ko'chirish
COPY main.py .

# Ma'lumotlar bazasi uchun papka yaratish
RUN mkdir -p /app/data

# Volume uchun ruxsat berish
VOLUME /app/data

# Botni ishga tushirish
CMD ["python", "main.py"]