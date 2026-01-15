# 2026.01.12 18.00
# syntax=docker/dockerfile:1.7-labs
FROM python:3.12-slim

# Faster, cleaner Python defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# --- System dependencies & Healthcheck tools ---
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# --- Dependencies layer (cached unless requirements.txt changes) ---
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# --- Application code (changes frequently, light layer) ---
COPY main.py .
COPY pages/home.py        pages/home.py
COPY pages/home0.py       pages/home0.py
COPY pages/crypto.py      pages/crypto.py
COPY pages/crypto0.py     pages/crypto0.py
COPY pages/air_dataset.py pages/air_dataset.py
COPY pages/lufthansa.py   pages/lufthansa.py
COPY pages/ml_databricks.py     pages/ml_databricks.py

# ---If you have other runtime files/folders, add them here ---
# COPY db.py .
# COPY templates/ templates/
# COPY static/ static/

EXPOSE 8000

# --- Try FastAPI /health first, then fallback to root ---
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || curl -fsS http://127.0.0.1:8000/ || exit 1

# --- Entrypoint (Make sure your main.py exposes 'server'---
CMD ["uvicorn", "main:server", "--host", "0.0.0.0", "--port", "8000"]
