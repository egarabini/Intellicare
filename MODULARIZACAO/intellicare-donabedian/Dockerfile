FROM python:3.11-slim AS base

WORKDIR /app

# Instalar intellicare-core primeiro
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir -e /tmp/intellicare-core

# Instalar intellicare-auth (opcional, mas necessário se usado no código)
COPY ./intellicare-auth /tmp/intellicare-auth
RUN pip install --no-cache-dir -e /tmp/intellicare-auth

# Instalar o módulo
COPY ./intellicare-donabedian/pyproject.toml ./intellicare-donabedian/README.md* ./

RUN pip install --no-cache-dir . || true

# Copiar código fonte (está em src/donabedian)
COPY ./intellicare-donabedian/src ./src
COPY ./intellicare-donabedian/migrations ./migrations

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# ── API ────────────────────────────────────────────────────────
FROM base AS api

CMD ["uvicorn", "donabedian.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

