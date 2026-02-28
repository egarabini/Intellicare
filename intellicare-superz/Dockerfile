FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction

COPY . .

EXPOSE 8009

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s \
    CMD curl -f http://localhost:8009/api/v1/health || exit 1

CMD ["uvicorn", "superz.api.app:app", "--host", "0.0.0.0", "--port", "8009", "--workers", "2"]
