FROM python:3.11-slim AS base

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Instalar intellicare-core
COPY ./intellicare-core /intellicare-core
RUN pip install --no-cache-dir -e /intellicare-core


# Instalar o módulo
COPY ./intellicare-gestor/pyproject.toml ./intellicare-gestor/README.md* ./
RUN pip install --no-cache-dir . || true
COPY ./intellicare-gestor .
RUN pip install --no-cache-dir -e .

EXPOSE 8011

# ── API ────────────────────────────────────────────────────────
FROM base AS api

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8011/api/v1/health || exit 1

CMD ["uvicorn", "gestor.api.app:app", "--host", "0.0.0.0", "--port", "8011"]
