#!/bin/bash
# ===================================================================
# Script para migrar Dockerfiles existentes para hardened (distroless)
# ===================================================================

set -e

MODULE_NAME="${1}"
MODULE_PORT="${2}"
MODULE_DIR="${3:-intellicare-${MODULE_NAME}}"

if [ -z "$MODULE_NAME" ] || [ -z "$MODULE_PORT" ]; then
    echo "Uso: $0 <nome_modulo> <porta> [diretorio]"
    echo "Exemplo: $0 wanda 8004"
    exit 1
fi

echo "=========================================="
echo "Migrando: $MODULE_NAME"
echo "Porta: $MODULE_PORT"
echo "Diretório: $MODULE_DIR"
echo "=========================================="

DOCKERFILE="${MODULE_DIR}/Dockerfile.hardened"

cat > "$DOCKERFILE" << 'EOF'
# ===================================================================
# IntelliCare MODULE - Hardened Docker Image
# Multi-stage build with distroless runtime for production security
#
# Build from repository root: docker build -f DIR/Dockerfile.hardened .
# ===================================================================

# --------------------------------------------------------------------------
# Build Stage — Compilação e instalação de dependências
# --------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Metadados de build
ARG BUILD_DATE
ARG VCS_REF
LABEL maintainer="IntelliCare <dev@intellicare.com.br>" \
      version="1.0.0" \
      description="IntelliCare MODULE - Build Stage"

# Instalar dependências do sistema para compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar e instalar intellicare-core
COPY ./intellicare-core /intellicare-core
RUN pip install --no-cache-dir --user -e /intellicare-core

# Copiar código do módulo
COPY ./$MODULE_DIR/pyproject.toml ./$MODULE_DIR/README.md* ./
RUN pip install --no-cache-dir --user poetry || true
COPY ./$MODULE_DIR .
RUN pip install --no-cache-dir --user . || true

# Garantir que uvicorn[standard] seja instalado
RUN pip install --no-cache-dir --user uvicorn[standard]

# Criar diretório para logs
RUN mkdir -p /app/logs && chmod 755 /app/logs

# --------------------------------------------------------------------------
# Runtime Stage — Imagem hardened minimalista (distroless)
# --------------------------------------------------------------------------
FROM gcr.io/distroless/python3-debian12

# Labels de metadados (Open Container Initiative)
LABEL maintainer="IntelliCare <dev@intellicare.com.br>" \
      version="1.0.0" \
      description="IntelliCare MODULE" \
      org.opencontainers.image.source="https://github.com/intellicare/MODULE" \
      org.opencontainers.image.revision="${VCS_REF:-main}" \
      org.opencontainers.image.created="${BUILD_DATE:-}" \
      org.opencontainers.image.documentation="https://docs.intellicare.com.br" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.vendor="IntelliCare"

# Copiar binários Python do builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Adicionar Python user bin ao PATH
ENV PATH="/root/.local/bin:${PATH}"

# Usar usuário não-root
USER nobody

# Expor porta
EXPOSE MODULE_PORT

# Health check usando Python puro
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:MODULE_PORT/api/v1/health').read()"

# Working directory
WORKDIR /app

# Executar aplicação
CMD ["python", "-m", "MODULE.api"]
EOF

# Substituir placeholders
sed -i "s/MODULE/${MODULE_NAME}/g" "$DOCKERFILE"
sed -i "s/MODULE_PORT/${MODULE_PORT}/g" "$DOCKERFILE"

echo "✅ Dockerfile.hardened criado: $DOCKERFILE"
echo ""
echo "Para buildar:"
echo "  docker build -f $DOCKERFILE -t intellicare-${MODULE_NAME}:hardened ."
echo ""
