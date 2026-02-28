#!/bin/bash
# ============================================================================
# Script de Deploy do Portal IntelliCare (Executar no Servidor)
# ============================================================================
# Descrição: Atualiza o Docker puxando do git staging
# Uso: Copie este script para o servidor e execute: ./deploy_from_staging.sh
# Data: 2026-02-27
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Configurações
INTELLICARE_PATH="/opt/intellicare/intellicare"
PORTAL_PATH="${INTELLICARE_PATH}/intellicare-portal/frontend"
GIT_BRANCH="staging"
CONTAINER_NAME="intellicare-portal"
IMAGE_NAME="intellicare-portal:latest"
NETWORK_NAME="intellicare_intellicare-network"

# ============================================================================
# Header
# ============================================================================
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   🚀 Deploy do Portal IntelliCare                         ║"
echo "║   Atualizando do git: ${GIT_BRANCH}                      ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Verificar se estamos no diretório correto
# ============================================================================
if [ ! -d "${INTELLICARE_PATH}" ]; then
    log_error "Diretório IntelliCare não encontrado: ${INTELLICARE_PATH}"
    log_info "Execute este script no servidor de produção"
    exit 1
fi

cd "${INTELLICARE_PATH}"

# ============================================================================
# Atualizar código do git staging
# ============================================================================
log_info "Atualizando código do git (${GIT_BRANCH})..."

# Verificar se há mudanças não commitadas
if ! git diff --quiet HEAD 2>/dev/null; then
    log_warning "Há mudanças locais não commitadas. Fazendo stash..."
    git stash --include-untracked
fi

# Puxar do staging
log_info "Fazendo pull do branch ${GIT_BRANCH}..."
git fetch origin ${GIT_BRANCH}
git checkout ${GIT_BRANCH}
git pull origin ${GIT_BRANCH}

log_success "Código atualizado!"

# ============================================================================
# Build da imagem Docker
# ============================================================================
log_info "Fazendo build da imagem Docker..."

cd "${PORTAL_PATH}"

# Parar e remover container antigo
log_info "Parando container antigo..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# Build com URLs de produção
log_info "Executando docker build..."
docker build \
    --build-arg VITE_API_FLORENCE_URL=https://api.intellicare.ia.br/v1/florence \
    --build-arg VITE_API_OSWALDO_URL=https://api.intellicare.ia.br/v1/oswaldo \
    --build-arg VITE_API_DONABEDIAN_URL=https://api.intellicare.ia.br/v1/donabedian \
    --build-arg VITE_API_WANDA_URL=https://api.intellicare.ia.br/v1/wanda \
    --build-arg VITE_API_COMUNICACAO_URL=https://api.intellicare.ia.br/v1/comunicacao \
    --build-arg VITE_API_GERALDA_URL=https://api.intellicare.ia.br/v1/geralda \
    --build-arg VITE_API_TIMEOUT=30000 \
    --build-arg VITE_ENABLE_ANALYTICS=true \
    --build-arg VITE_APP_VERSION=2.0.0 \
    --target production \
    -t ${IMAGE_NAME} \
    . 2>&1 | tail -20

if [ $? -ne 0 ]; then
    log_error "Build falhou!"
    exit 1
fi

log_success "Build concluído!"

# ============================================================================
# Criar rede se não existir
# ============================================================================
if ! docker network ls | grep -q "${NETWORK_NAME}"; then
    log_info "Criando rede Docker..."
    docker network create "${NETWORK_NAME}"
fi

# ============================================================================
# Iniciar novo container
# ============================================================================
log_info "Iniciando container..."

docker run -d \
    --name ${CONTAINER_NAME} \
    --network ${NETWORK_NAME} \
    --restart unless-stopped \
    ${IMAGE_NAME}

log_success "Container iniciado!"

# ============================================================================
# Health check
# ============================================================================
log_info "Verificando saúde do container..."
sleep 5

if docker ps | grep -q ${CONTAINER_NAME}; then
    if docker exec ${CONTAINER_NAME} wget --quiet --tries=1 --spider http://localhost/health 2>/dev/null; then
        log_success "Health check OK!"
    else
        log_warning "Health check falhou, mas container está rodando"
        log_info "Verifique: docker logs ${CONTAINER_NAME}"
    fi
else
    log_error "Container não está rodando!"
    docker logs ${CONTAINER_NAME} --tail 50
    exit 1
fi

# ============================================================================
# Informações finais
# ============================================================================
echo ""
log_success "Deploy concluído com sucesso!"
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   🌐 Portal IntelliCare - Produção                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "URLs de acesso:"
echo "  • https://portal.intellicare.ia.br"
echo "  • https://intellicare.ia.br"
echo "  • https://www.intellicare.ia.br"
echo "  • https://saudeplanner.com.br"
echo ""
echo "Comandos úteis:"
echo "  docker logs ${CONTAINER_NAME} -f"
echo "  docker exec -it ${CONTAINER_NAME} sh"
echo "  docker restart ${CONTAINER_NAME}"
echo ""
