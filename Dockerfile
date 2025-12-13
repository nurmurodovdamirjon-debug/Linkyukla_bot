FROM python:3.9-slim

# FFmpeg ni o'rnatish
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Loyiha fayllarini ko'chirish
WORKDIR /app
COPY . .

# Kutubxonalarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Botni ishga tushirish
CMD ["python", "run_bot.py"]