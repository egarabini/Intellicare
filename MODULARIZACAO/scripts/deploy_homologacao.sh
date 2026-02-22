#!/bin/bash

# ============================================================================
# IntelliCare - Script de Deploy Automático para Homologação
# ============================================================================
# Servidor: 167.86.97.142 (Contabo VPS)
# Uso: ./scripts/deploy_homologacao.sh
# ============================================================================

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções auxiliares
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "============================================================================"
echo "  IntelliCare - Deploy Homologação"
echo "  Servidor: 167.86.97.142"
echo "============================================================================"
echo ""

# Verificar se está no diretório correto
if [ ! -f "docker-compose.full.yml" ]; then
    log_error "Arquivo docker-compose.full.yml não encontrado!"
    log_error "Execute este script do diretório MODULARIZACAO/"
    exit 1
fi

# Verificar se .env existe
if [ ! -f ".env" ]; then
    log_warning "Arquivo .env não encontrado!"
    log_info "Copiando .env.homologacao para .env..."
    cp .env.homologacao .env
    log_warning "IMPORTANTE: Revise o arquivo .env e configure as senhas!"
    read -p "Pressione ENTER para continuar após revisar o .env..."
fi

# Verificar Docker
log_info "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    log_error "Docker não está instalado!"
    exit 1
fi
log_success "Docker encontrado: $(docker --version)"

# Verificar Docker Compose
log_info "Verificando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose não está instalado!"
    exit 1
fi
log_success "Docker Compose encontrado: $(docker-compose --version)"

# Parar containers existentes
log_info "Parando containers existentes..."
docker-compose -f docker-compose.full.yml down || true
log_success "Containers parados"

# Limpar volumes antigos (CUIDADO!)
read -p "Deseja limpar volumes antigos? Isso apagará TODOS os dados! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Removendo volumes..."
    docker-compose -f docker-compose.full.yml down -v
    log_success "Volumes removidos"
fi

# Pull das imagens
log_info "Baixando imagens Docker..."
docker-compose -f docker-compose.full.yml pull || true
log_success "Imagens atualizadas"

# Build das imagens locais
log_info "Construindo imagens locais..."
docker-compose -f docker-compose.full.yml build
log_success "Build concluído"

# Subir infraestrutura (PostgreSQL, Redis)
log_info "Subindo infraestrutura (PostgreSQL, Redis)..."
docker-compose -f docker-compose.full.yml up -d postgres redis
log_success "Infraestrutura iniciada"

# Aguardar PostgreSQL ficar pronto
log_info "Aguardando PostgreSQL ficar pronto..."
sleep 30

# Criar schemas
log_info "Criando schemas no PostgreSQL..."
docker exec -i $(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db <<EOF
CREATE SCHEMA IF NOT EXISTS intellicare_florence;
CREATE SCHEMA IF NOT EXISTS intellicare_oswaldo;
CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;
CREATE SCHEMA IF NOT EXISTS intellicare_wanda;
CREATE SCHEMA IF NOT EXISTS intellicare_comunicacao;
CREATE SCHEMA IF NOT EXISTS intellicare_geralda;
EOF
log_success "Schemas criados"

# Subir backends
log_info "Subindo serviços backend..."
docker-compose -f docker-compose.full.yml up -d \
    florence \
    oswaldo \
    donabedian \
    wanda \
    comunicacao \
    geralda
log_success "Backends iniciados"

# Aguardar backends ficarem prontos
log_info "Aguardando backends ficarem prontos..."
sleep 60

# Subir frontend
log_info "Subindo frontend (Portal)..."
docker-compose -f docker-compose.full.yml up -d portal
log_success "Frontend iniciado"

# Subir monitoring (opcional)
read -p "Deseja subir Prometheus e Grafana? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    log_info "Subindo Prometheus e Grafana..."
    docker-compose -f docker-compose.full.yml up -d prometheus grafana
    log_success "Monitoring iniciado"
fi

# Verificar status
log_info "Verificando status dos containers..."
docker-compose -f docker-compose.full.yml ps

# Executar smoke tests
log_info "Executando smoke tests..."
sleep 10
if [ -f "scripts/smoke_tests.py" ]; then
    python scripts/smoke_tests.py --url http://167.86.97.142 || log_warning "Alguns testes falharam"
elif [ -f "scripts/smoke_tests.sh" ]; then
    chmod +x scripts/smoke_tests.sh
    ./scripts/smoke_tests.sh || log_warning "Alguns testes falharam"
else
    log_warning "Script de smoke tests não encontrado (scripts/smoke_tests.py ou .sh)"
fi

# Resumo
echo ""
echo "============================================================================"
echo "  Deploy Concluído!"
echo "============================================================================"
echo ""
log_success "Serviços disponíveis em:"
echo ""
echo "  Portal Frontend:    http://167.86.97.142:3001"
echo "  Florence API:       http://167.86.97.142:8001/docs"
echo "  Oswaldo API:        http://167.86.97.142:8002/docs"
echo "  Donabedian API:     http://167.86.97.142:8003/docs"
echo "  Wanda API:          http://167.86.97.142:8004/docs"
echo "  Comunicacao API:    http://167.86.97.142:8005/docs"
echo "  Geralda API:        http://167.86.97.142:8006/docs"
echo ""

