# 2026.02.08  18.00
# syntax=docker/dockerfile:1.7-labs
FROM python:3.12

# -------------------------
# Python defaults
# -------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# -------------------------
# System dependencies
# -------------------------
# python:3.12 already includes most native libs needed by:
# pandas, pyarrow, scikit-learn, psycopg[binary], databricks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

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
        --timeout 60 \
        -r requirements.txt

# -------------------------
# Application code
# -------------------------
COPY main.py .
COPY pages/ pages/
COPY apis/ apis/

# -------------------------
# Runtime
# -------------------------
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "main:server", "--host", "0.0.0.0", "--port", "8000"]
