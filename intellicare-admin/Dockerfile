FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install intellicare-core first
COPY ./intellicare-core /tmp/intellicare-core
RUN pip install --no-cache-dir /tmp/intellicare-core

# Install intellicare-auth (optional)
COPY ./intellicare-auth /tmp/intellicare-auth
RUN pip install --no-cache-dir /tmp/intellicare-auth || true

# Install the module
COPY ./intellicare-admin/pyproject.toml ./intellicare-admin/README.md* ./
RUN pip install --no-cache-dir . || true

COPY ./intellicare-admin ./
RUN pip install --no-cache-dir -e .

# Port
EXPOSE 8010

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8010/api/v1/health || exit 1

# Run
CMD ["uvicorn", "admin.api.app:app", "--host", "0.0.0.0", "--port", "8010"]
