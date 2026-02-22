FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml .

RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir .

COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# ── API ────────────────────────────────────────────────────────
FROM base AS api

CMD ["uvicorn", "comunicacao.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

