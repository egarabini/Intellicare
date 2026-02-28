FROM python:3.11-slim AS base

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Instalar intellicare-core primeiro
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir -e /tmp/intellicare-core

# Instalar intellicare-auth (opcional)
COPY ./intellicare-auth /tmp/intellicare-auth
RUN pip install --no-cache-dir -e /tmp/intellicare-auth || true

# Instalar o módulo
COPY ./intellicare-wanda/pyproject.toml ./intellicare-wanda/README.md* ./

RUN pip install --no-cache-dir . || true

COPY ./intellicare-wanda .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# ── API ────────────────────────────────────────────────────────
FROM base AS api

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "wanda.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
