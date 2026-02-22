FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml .
COPY zilda/ zilda/

RUN pip install --no-cache-dir -e .

# --- API ---
FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "zilda.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
