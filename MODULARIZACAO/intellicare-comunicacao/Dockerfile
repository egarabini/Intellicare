FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml README.md* ./

RUN pip install --no-cache-dir . || true

COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 8000

# ── API ────────────────────────────────────────────────────────
FROM base AS api

CMD ["uvicorn", "comunicacao.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

