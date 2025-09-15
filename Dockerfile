# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \ 
    && apt-get install -y --no-install-recommends build-essential libpq-dev \ 
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels

COPY . .

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \ 
    && apt-get install -y --no-install-recommends libpq-dev \ 
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user
RUN useradd -m appuser

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt gunicorn

COPY --from=builder /app /app

USER appuser

EXPOSE 8000

# Render will set PORT env var; default to 8000
ENV PORT=8000

# Use gunicorn with uvicorn workers; run migrations first
ENTRYPOINT ["sh", "-c", "python -c 'import alembic_runner; alembic_runner.run_migrations()' && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"]
