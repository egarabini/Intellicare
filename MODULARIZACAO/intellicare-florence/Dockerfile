FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# API target
FROM base AS api
CMD ["uvicorn", "florence.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

# UI target (futuro)
FROM base AS ui
EXPOSE 8502
CMD ["streamlit", "run", "florence/ui/main.py", "--server.port=8502", "--server.headless=true"]
