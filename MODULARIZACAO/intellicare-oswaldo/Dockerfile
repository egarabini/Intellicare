FROM python:3.11-slim AS base

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# Instalar intellicare-core primeiro (do diretorio local ou PyPI)
COPY ../intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir /tmp/intellicare-core && rm -rf /tmp/intellicare-core

# Instalar dependencias do Oswaldo
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[ui]"

COPY . .

# API (porta 8000)
FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "oswaldo.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

# Streamlit UI (porta 8501)
FROM base AS ui
EXPOSE 8501
CMD ["streamlit", "run", "oswaldo/ui/main.py", "--server.port=8501", "--server.headless=true"]
