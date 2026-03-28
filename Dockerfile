FROM python:3.10-slim

# Tizim paketlarini (FFmpeg, git, curl, Node.js) o'rnatish
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Non-root user yaratish (xavfsizlik uchun)
RUN useradd -m -u 1000 botuser

# Loyiha fayllarini ko'chirish
WORKDIR /app
COPY . .

# Fayl huquqlarini sozlash
RUN chown -R botuser:botuser /app

# Kutubxonalarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Non-root userga o'tish
USER botuser

# Health check (8000 portda HTTP endpoint)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Botni ishga tushirish
CMD ["python", "run_bot.py"]
