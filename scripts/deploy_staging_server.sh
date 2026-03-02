#!/bin/bash
# ============================================================================
# Script de Deploy do Portal IntelliCare - Servidor Staging
# ============================================================================
# Descrição: Atualiza o Docker no servidor STAGING puxando do git
# Uso: Execute no servidor de staging: ./deploy_staging_server.sh
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

# URLs de STAGING
STAGING_API_URL="https://staging.intellicare.ia.br"

# ============================================================================
# Header
# ============================================================================
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║   🚀 Deploy do Portal IntelliCare - STAGING              ║"
echo "║   Atualizando do git: ${GIT_BRANCH}                      ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# Verificar se estamos no diretório correto
# ============================================================================
if [ ! -d "${INTELLICARE_PATH}" ]; then
    log_error "Diretório IntelliCare não encontrado: ${INTELLICARE_PATH}"
    log_info "Execute este script no servidor de staging"
    exit 1
fi

cd "${INTELLICARE_PATH}"

# ============================================================================
# Resolver branches divergentes e atualizar código
# ============================================================================
log_info "Atualizando código do git (${GIT_BRANCH})..."

# Reset para o staging remoto (mais seguro para staging)
log_info "Resetando para origin/${GIT_BRANCH}..."
git fetch origin ${GIT_BRANCH}
git reset --hard origin/${GIT_BRANCH}

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

# Build com URLs de STAGING
log_info "Executando docker build (urls de staging)..."
docker build \
    --build-arg VITE_API_FLORENCE_URL=${STAGING_API_URL}/v1/florence \
    --build-arg VITE_API_OSWALDO_URL=${STAGING_API_URL}/v1/oswaldo \
    --build-arg VITE_API_DONABEDIAN_URL=${STAGING_API_URL}/v1/donabedian \
    --build-arg VITE_API_WANDA_URL=${STAGING_API_URL}/v1/wanda \
    --build-arg VITE_API_COMUNICACAO_URL=${STAGING_API_URL}/v1/comunicacao \
    --build-arg VITE_API_GERALDA_URL=${STAGING_API_URL}/v1/geralda \
    --build-arg VITE_API_TIMEOUT=30000 \
    --build-arg VITE_ENABLE_ANALYTICS=false \
    --build-arg VITE_APP_VERSION=2.0.0-staging \
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
log_success "Deploy em STAGING concluído com sucesso!"
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   🌐 Portal IntelliCare - STAGING                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "URL de acesso:"
echo "  • https://staging.intellicare.ia.br"
echo ""
echo "Comandos úteis:"
echo "  docker logs ${CONTAINER_NAME} -f"
echo "  docker exec -it ${CONTAINER_NAME} sh"
echo "  docker restart ${CONTAINER_NAME}"
echo ""
