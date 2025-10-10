FROM python:3.12-slim

# Set environment vars
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    ca-certificates \
    curl \
    wget \
    unzip \
    chromium \
    chromium-driver \
    libnss3 \
    libxss1 \
    libasound2 \
    libu2f-udev \
    libxshmfence1 \
    libgbm1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy app code
WORKDIR /app
COPY app/ /app/

# Copy cron file and entry script
COPY cron/airbnb.crontab /etc/cron.d/airbnb
COPY run.sh /run.sh

# Python requirements
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Setup cron
RUN chmod 0644 /etc/cron.d/airbnb \
    && crontab /etc/cron.d/airbnb \
    && mkdir -p /var/log/cron

# Ensure run.sh is executable
RUN chmod +x /run.sh

# Default command (cron runs in background, run.sh controls flow)
CMD ["/bin/sh", "/run.sh"]
