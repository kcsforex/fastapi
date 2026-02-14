# 2026.02.14  10.00
# syntax=docker/dockerfile:1.7-labs
FROM python:3.12.2-slim

# -------------------------
# Python defaults
# -------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# -------------------------
# System dependencies
# -------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# -------------------------
# Python dependencies
# -------------------------
COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    pip install \
        --no-cache-dir \
        --progress-bar off \
        --retries 5 \
        --timeout 120 \
        -r requirements.txt

# -------------------------
# Application code
# -------------------------
COPY main.py .
COPY pages/ pages/
COPY apis/ apis/

# -------------------------
# Create non-root user for security
# -------------------------
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# -------------------------
# Runtime
# -------------------------
EXPOSE 8000

# Improved health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

# Use multiple workers for better performance
# Workers can be overridden via UVICORN_WORKERS env var
CMD ["sh", "-c", "uvicorn main:server --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-2} --timeout-keep-alive 120 --access-log"]
