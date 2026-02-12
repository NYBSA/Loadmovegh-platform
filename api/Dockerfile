# LoadMoveGH — Backend API Dockerfile
# Multi-stage build for production deployment on Railway or Render

FROM python:3.12-slim AS base

# System dependencies for asyncpg, lightgbm
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

EXPOSE ${PORT:-8000}

# Run migrations then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4 --loop uvloop --http httptools --access-log"]
