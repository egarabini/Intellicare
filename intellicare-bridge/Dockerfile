# intellicare-bridge — Adaptadores HIS para FHIR R4 (stub)
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar intellicare-core
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir /tmp/intellicare-core

# Instalar intellicare-auth (opcional)
COPY ./intellicare-auth /tmp/intellicare-auth
RUN pip install --no-cache-dir /tmp/intellicare-auth || true

# Copiar bridge
COPY ./intellicare-bridge/pyproject.toml ./
COPY ./intellicare-bridge/bridge/ ./bridge/

# Instalar dependências
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .

# ── Stage 2: Runtime ──────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Dependências de runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar pacotes instalados
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código da aplicação
COPY --from=builder /app/bridge/ ./bridge/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "bridge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
