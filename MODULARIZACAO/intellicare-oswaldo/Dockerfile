FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

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
