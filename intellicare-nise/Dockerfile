# ── Stage 1: Builder ──────────────────────────────────────────────
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar intellicare-core
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir /tmp/intellicare-core

# Instalar intellicare-auth (opcional)
COPY ./intellicare-auth /tmp/intellicare-auth
RUN pip install --no-cache-dir /tmp/intellicare-auth || true

# Copy requirements and source
COPY ./intellicare-nise/pyproject.toml ./
COPY ./intellicare-nise/nise/ ./nise/

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .

# ── Stage 2: Runtime ──────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code from builder
COPY --from=builder /app/nise/ ./nise/

# Create non-root user
RUN useradd -m -u 1000 nise && \
    chown -R nise:nise /app

USER nise

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "nise.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

