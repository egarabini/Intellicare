FROM python:3.11-slim AS base

WORKDIR /app

# Instalar intellicare-core primeiro
COPY ../intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir -e /tmp/intellicare-core

# Instalar o módulo
COPY pyproject.toml README.md* ./

RUN pip install --no-cache-dir . || true

COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# API (porta 8000)
FROM base AS api
CMD ["uvicorn", "oswaldo.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

# Streamlit UI (porta 8501)
FROM base AS ui
EXPOSE 8501
CMD ["streamlit", "run", "oswaldo/ui/main.py", "--server.port=8501", "--server.headless=true"]
