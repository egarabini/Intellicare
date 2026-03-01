# ============================================================================
# INTELLICARE-GRAHAME � Hardened Multi-Stage Dockerfile
# ============================================================================
# Production-ready image with:
# - Multi-stage build (build + runtime)
# - Distroless runtime (minimal attack surface)
# - Non-root user (nobody)
# - Health check
# - Security scanning ready (Trivy)
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
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install intellicare-core to /root/.local AND /build for dependencies
COPY ./intellicare-core /intellicare-core
COPY ./intellicare-core /build/intellicare-core
RUN pip install --no-cache-dir --user -e /intellicare-core

# Install intellicare-auth (optional)
COPY ./intellicare-auth /intellicare-auth
RUN pip install --no-cache-dir --user -e /intellicare-auth || true

# Install grahame dependencies (no install itself yet)
COPY ./intellicare-grahame/pyproject.toml ./intellicare-grahame/README.md* /build/
RUN pip install --no-cache-dir --user . || true

# Copy grahame source and install to /root/.local
COPY ./intellicare-grahame /build/intellicare-grahame
RUN pip install --no-cache-dir --user -e /build/intellicare-grahame

# Remove build-only Python packages with known CVEs from runtime layer copy.
RUN pip uninstall -y wheel jaraco.context || true

# Create wrapper script to use correct Python
RUN printf '#!/bin/sh\nexec /root/.local/bin/python3 "$@"' > /python-wrapper && \
    chmod +x /python-wrapper

# ----------------------------------------------------------------------------
# RUNTIME STAGE � Distroless, runs as nobody
# ----------------------------------------------------------------------------
FROM gcr.io/distroless/python3-debian13 AS runtime

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy app (if needed for static files, templates, etc.)
COPY --from=builder /build/intellicare-grahame /app/intellicare-grahame

# Copy Python wrapper from builder
COPY --from=builder /python-wrapper /python-wrapper

# Ensure Python finds user-installed packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/root/.local/lib/python3.11/site-packages:$PYTHONPATH

# Run as non-root user (distroless creates 'nobody' user)
USER nobody

# Expose port
EXPOSE 8000

# Health check (uses wget from distroless)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/v1/health || exit 1

# ----------------------------------------------------------------------------
# API TARGET � Runs uvicorn server
# ----------------------------------------------------------------------------
FROM runtime AS api

# Run uvicorn from /root/.local/bin using wrapper
CMD ["/python-wrapper", "-m", "uvicorn", "grahame.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
