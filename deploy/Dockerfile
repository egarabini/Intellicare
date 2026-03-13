# IntelliCare V3 - Imagem base do intellicare-service
# Empacota todos os modulos em um unico container

FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY packages/ packages/
COPY modules/ modules/
COPY configs/ configs/

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN if [ -f packages/intellicare-core/pyproject.toml ]; then \
        pip install --no-cache-dir -e packages/intellicare-core[all]; \
    fi
RUN for module in modules/*/; do \
        if [ -f "${module}pyproject.toml" ]; then \
            pip install --no-cache-dir -e "$module"; \
        fi; \
    done

RUN useradd -r -s /usr/sbin/nologin intellicare
USER intellicare

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "intellicare_service.app:app", "--host", "0.0.0.0", "--port", "8000"]
