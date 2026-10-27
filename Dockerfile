# Hyper Video Studio - Production Dockerfile
FROM python:3.11-slim-bookworm

# Install system dependencies (Node.js, Chromium, FFmpeg, fonts)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ffmpeg \
    chromium \
    fonts-indic \
    fonts-freefont-ttf \
    fonts-liberation \
    ca-certificates \
    cron \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Environment variables for headless chromium
ENV CHROME_BIN=/usr/bin/chromium \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Node dependencies
COPY package*.json ./
RUN npm install --production

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Generate default SFX assets
RUN python3 core/sfx_generator.py

EXPOSE 8585

CMD ["python3", "dashboard/server.py"]
