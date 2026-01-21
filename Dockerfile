# 2026.01.21 11.00
# syntax=docker/dockerfile:1.7-labs
FROM python:3.12-slim

# Faster, cleaner Python defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY pages/home.py    pages/home.py
COPY pages/crypto.py  pages/crypto.py
COPY apis/crypto_api.py   apis/crypto_api.py
COPY pages/air_dataset.py pages/air_dataset.py
COPY pages/lufthansa.py     pages/lufthansa.py
COPY apis/lufthansa_api.py  apis/lufthansa_api.py
COPY pages/lufthansa_ml.py     pages/lufthansa_ml.py
COPY pages/databricks.py  pages/databricks.py

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || curl -fsS http://127.0.0.1:8000/ || exit 1

CMD ["uvicorn", "main:server", "--host", "0.0.0.0", "--port", "8000"]
