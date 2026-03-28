FROM python:3.10-slim

# Tizim paketlarini (FFmpeg, git, curl, Node.js) o'rnatish
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Loyiha fayllarini ko'chirish
WORKDIR /app
COPY . .

# Kutubxonalarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Botni ishga tushirish
CMD ["python", "run_bot.py"]