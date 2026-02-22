FROM python:3.11-slim AS base

WORKDIR /app

# Instalar intellicare-core primeiro
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir -e /tmp/intellicare-core

# Instalar o módulo
COPY ./intellicare-florence/pyproject.toml ./intellicare-florence/README.md* ./

RUN pip install --no-cache-dir . || true

COPY ./intellicare-florence .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# API target
FROM base AS api
CMD ["uvicorn", "florence.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

# UI target (futuro)
FROM base AS ui
EXPOSE 8502
CMD ["streamlit", "run", "florence/ui/main.py", "--server.port=8502", "--server.headless=true"]
