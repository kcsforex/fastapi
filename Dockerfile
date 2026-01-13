
# syntax=docker/dockerfile:1.7-labs
FROM python:3.12-slim

# Faster, cleaner Python defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 1) Dependencies layer (cached unless requirements.txt changes)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 2) App layer (your code) — only copy what you need
COPY main.py .
COPY pages/home.py        pages/home.py
COPY pages/home0.py        pages/home0.py
COPY pages/crypto.py      pages/crypto.py
COPY pages/crypto0.py     pages/crypto0.py
COPY pages/air_dataset.py pages/air_dataset.py
COPY pages/ml_databricks.py     pages/ml_databricks.py

# If you have other runtime files/folders, add them here explicitly:
# COPY db.py .
# COPY templates/ templates/
# COPY static/ static/

EXPOSE 8000
CMD ["uvicorn", "main:server", "--host", "0.0.0.0", "--port", "8000"]

