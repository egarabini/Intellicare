FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir pip --upgrade && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false

# Copy local dependencies first (for Docker layer caching)
COPY . .

# Install without dev deps
RUN poetry install --no-dev --no-interaction 2>/dev/null || pip install -e .

# Port
EXPOSE 8010

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8010/api/v1/health || exit 1

# Run
CMD ["uvicorn", "admin.api.app:app", "--host", "0.0.0.0", "--port", "8010"]
