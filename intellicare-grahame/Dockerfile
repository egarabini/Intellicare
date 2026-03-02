# ============================================================================
# INTELLICARE-GRAHAME � Multi-Stage Dockerfile
# ============================================================================
# Production-ready image with:
# - Multi-stage build (build + runtime)
# - Python 3.11 slim runtime
# - Health check
# ============================================================================

# ----------------------------------------------------------------------------
# BUILD STAGE � Runs as root, has build tools
# ----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies (including libpq-dev for asyncpg/psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install to /usr/local (accessible by all users)
# Install intellicare-core to both /intellicare-core and /build for grahame's dependencies
COPY ./intellicare-core /intellicare-core
COPY ./intellicare-core /build/intellicare-core
RUN pip install --no-cache-dir /intellicare-core

# Install intellicare-auth (optional)
COPY ./intellicare-auth /intellicare-auth
RUN pip install --no-cache-dir /intellicare-auth || true

# Install grahame dependencies
COPY ./intellicare-grahame/pyproject.toml ./intellicare-grahame/README.md* /build/
RUN pip install --no-cache-dir . || true

# Copy grahame source and install
COPY ./intellicare-grahame /build/intellicare-grahame
RUN pip install --no-cache-dir -e /build/intellicare-grahame

# Remove build-only Python packages
RUN pip uninstall -y wheel jaraco.context || true

# ----------------------------------------------------------------------------
# RUNTIME STAGE
# ----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder (installed to /usr/local)
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app - copy the contents so grahame is at /app/grahame
COPY --from=builder /build/intellicare-grahame /app/

WORKDIR /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# ----------------------------------------------------------------------------
# API TARGET � Runs uvicorn server
# ----------------------------------------------------------------------------
FROM runtime AS api

# Run uvicorn
CMD ["python3", "-m", "uvicorn", "grahame.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
