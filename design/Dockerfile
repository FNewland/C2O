# ============================================================================
# SpaceCDF — Backend Dockerfile
# ============================================================================
# Builds the FastAPI backend with all Python packages.
# Used by docker-compose.yml alongside PostgreSQL and Redis containers.
#
# Build:  docker build -t spacecdf-server .
# Run:    docker run -p 8000:8000 spacecdf-server
# ============================================================================

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies (minimal — no build tools needed for pure-Python packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# ── Install Python packages ────────────────────────────────────────────────
# Copy only pyproject.toml files first for better Docker layer caching
COPY pyproject.toml ./
COPY packages/spacecdf-common/pyproject.toml packages/spacecdf-common/
COPY packages/spacecdf-common/src/ packages/spacecdf-common/src/
COPY packages/spacecdf-kb/pyproject.toml packages/spacecdf-kb/
COPY packages/spacecdf-kb/src/ packages/spacecdf-kb/src/
COPY packages/spacecdf-agents/pyproject.toml packages/spacecdf-agents/
COPY packages/spacecdf-agents/src/ packages/spacecdf-agents/src/
COPY packages/spacecdf-server/pyproject.toml packages/spacecdf-server/
COPY packages/spacecdf-server/src/ packages/spacecdf-server/src/

# Optional AI package
COPY packages/spacecdf-ai/pyproject.toml packages/spacecdf-ai/
COPY packages/spacecdf-ai/src/ packages/spacecdf-ai/src/

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
        -e packages/spacecdf-common \
        -e packages/spacecdf-kb \
        -e packages/spacecdf-agents \
        -e packages/spacecdf-server

# ── Copy application code ──────────────────────────────────────────────────
COPY configs/ configs/
COPY scripts/ scripts/

# ── Runtime ─────────────────────────────────────────────────────────────────
EXPOSE 8000

# Default: run with --reload for development (override in production)
CMD ["uvicorn", "spacecdf_server.app:app", "--host", "0.0.0.0", "--port", "8000"]
