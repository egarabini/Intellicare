#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# Script para executar testes E2E de workflows Kestra
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

# ── Cores para output ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Funções auxiliares ─────────────────────────────────────────────────────

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# ── Banner ─────────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "  IntelliCare NISE - Testes E2E de Workflows Kestra"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# ── Verificar dependências ─────────────────────────────────────────────────

log_info "Verificando dependências..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker não encontrado. Instale o Docker primeiro."
    exit 1
fi
log_success "Docker encontrado"

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose não encontrado. Instale o Docker Compose primeiro."
    exit 1
fi
log_success "Docker Compose encontrado"

# Verificar pytest
if ! command -v pytest &> /dev/null; then
    log_warning "pytest não encontrado. Instalando..."
    pip install pytest pytest-asyncio pytest-cov
fi
log_success "pytest encontrado"

# ── Verificar serviços Docker ──────────────────────────────────────────────

log_info "Verificando serviços Docker..."

# Verificar se NISE está rodando
if ! docker ps | grep -q intellicare-nise; then
    log_warning "NISE não está rodando. Iniciando stack Docker..."
    docker-compose up -d
    log_info "Aguardando serviços iniciarem (30s)..."
    sleep 30
else
    log_success "NISE está rodando"
fi

# Verificar se Kestra está rodando
if ! docker ps | grep -q intellicare-kestra; then
    log_error "Kestra não está rodando. Execute 'docker-compose up -d kestra' primeiro."
    exit 1
fi
log_success "Kestra está rodando"

# ── Health checks ──────────────────────────────────────────────────────────

log_info "Verificando health dos serviços..."

# Health check NISE
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "NISE está saudável"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_error "NISE não respondeu ao health check"
        exit 1
    fi
    log_warning "Aguardando NISE... (tentativa $RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done

# Health check Kestra
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s http://localhost:8080/api/v1/health > /dev/null 2>&1; then
        log_success "Kestra está saudável"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_error "Kestra não respondeu ao health check"
        exit 1
    fi
    log_warning "Aguardando Kestra... (tentativa $RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

# ── Executar testes E2E ────────────────────────────────────────────────────

echo ""
log_info "Executando testes E2E..."
echo ""

# Executar testes com pytest
pytest tests/test_e2e_workflows.py \
    -v \
    -m e2e \
    --tb=short \
    --color=yes \
    --durations=10 \
    --cov=nise \
    --cov-report=term-missing \
    --cov-report=html:htmlcov/e2e

TEST_EXIT_CODE=$?

echo ""

# ── Resultados ─────────────────────────────────────────────────────────────

if [ $TEST_EXIT_CODE -eq 0 ]; then
    log_success "Todos os testes E2E passaram!"
    echo ""
    log_info "Relatório de cobertura: htmlcov/e2e/index.html"
    exit 0
else
    log_error "Alguns testes E2E falharam!"
    exit $TEST_EXIT_CODE
fi

