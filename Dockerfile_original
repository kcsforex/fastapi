# 2026.02.05 8.00
# syntax=docker/dockerfile:1.7-labs
FROM python:3.12-slim

# Faster, cleaner Python defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better cache reuse)
COPY requirements.txt .

# Install Python deps (hardened against network flakiness)
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    pip install \
        --no-cache-dir \
        --progress-bar off \
        --retries 10 \
        --timeout 120 \
        -r requirements.txt

# Copy application code
COPY main.py .

COPY pages/ pages/
COPY apis/ apis/

EXPOSE 8000

# Healthcheck (works for Dash + Uvicorn)
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || \
      curl -fsS http://127.0.0.1:8000/ || exit 1

# Run app
CMD ["uvicorn", "main:server", "--host", "0.0.0.0", "--port", "8000"]

