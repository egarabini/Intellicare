# IntelliCare V3 - Multi-stage build
# Stage 1: Node.js builda todos os frontends
# Stage 2: Python + statics copiados do Stage 1

# ── Stage 1: Build dos frontends ────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /build

# Copiar todos os frontends
COPY frontend/ frontend/

# Criar o diretório de destino que o vite.config.ts referencia via ../../packages/...
RUN mkdir -p packages/intellicare-core/intellicare_core/static

# Build Portal  → static/portal/
RUN cd frontend/Portal \
    && npm ci --prefer-offline \
    && npx vite build

# Build AdminUI → static/admin-ui/
RUN cd frontend/AdminUI \
    && npm ci --prefer-offline \
    && npx vite build

# Build GestorUI → static/gestor-ui/
RUN cd frontend/GestorUI \
    && npm ci --prefer-offline \
    && npx vite build

# Build ClinicoUI → static/clinico-ui/
RUN cd frontend/ClinicoUI \
    && npm ci --prefer-offline \
    && npx vite build

# Build PacienteUI → static/paciente-ui/
RUN cd frontend/PacienteUI \
    && npm ci --prefer-offline \
    && npx vite build


# ── Stage 2: Aplicação Python ────────────────────────────────────────────────
FROM python:3.11-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar código Python (inclui packages/ com o diretório static/ ainda vazio)
COPY packages/ packages/
COPY modules/ modules/
COPY configs/ configs/

# Sobrescrever o static/ vazio com os arquivos buildados no stage Node
COPY --from=frontend-builder \
    /build/packages/intellicare-core/intellicare_core/static/ \
    packages/intellicare-core/intellicare_core/static/

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
