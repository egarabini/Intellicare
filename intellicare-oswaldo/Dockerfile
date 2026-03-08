FROM python:3.11-slim AS base

WORKDIR /app

# Instalar curl para healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Instalar intellicare-core primeiro
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir /tmp/intellicare-core

# Instalar intellicare-auth (opcional)
COPY ./intellicare-auth /tmp/intellicare-auth
RUN pip install --no-cache-dir /tmp/intellicare-auth || true

# Instalar o módulo
COPY ./intellicare-oswaldo/pyproject.toml ./intellicare-oswaldo/README.md* ./

RUN pip install --no-cache-dir . || true

COPY ./intellicare-oswaldo .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# API (porta 8000)
FROM base AS api
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1
CMD ["uvicorn", "oswaldo.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

# Streamlit UI (porta 8501)
FROM base AS ui
EXPOSE 8501
CMD ["streamlit", "run", "oswaldo/ui/main.py", "--server.port=8501", "--server.headless=true"]
