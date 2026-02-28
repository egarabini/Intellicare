#!/bin/bash
# ============================================================================
# Script de Deploy do Portal IntelliCare
# ============================================================================
# Descrição: Build e deploy do portal React em produção
# Data: 2026-02-27
# Versão: 1.0.0
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

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PORTAL_DIR="$PROJECT_ROOT/intellicare-portal/frontend"

# Configurações
CONTAINER_NAME="intellicare-portal"
IMAGE_NAME="intellicare-portal:latest"
NETWORK_NAME="intellicare_intellicare-network"

# ============================================================================
# Função: Verificar pré-requisitos
# ============================================================================
check_prerequisites() {
    log_info "Verificando pré-requisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker não está instalado!"
        exit 1
    fi
    
    # Verificar se diretório do portal existe
    if [ ! -d "$PORTAL_DIR" ]; then
        log_error "Diretório do portal não encontrado: $PORTAL_DIR"
        exit 1
    fi
    
    # Verificar se Dockerfile existe
    if [ ! -f "$PORTAL_DIR/Dockerfile" ]; then
        log_error "Dockerfile não encontrado: $PORTAL_DIR/Dockerfile"
        exit 1
    fi
    
    log_success "Pré-requisitos OK"
}

# ============================================================================
# Função: Parar e remover container antigo
# ============================================================================
stop_old_container() {
    log_info "Parando container antigo..."
    
    if docker ps -a | grep -q "$CONTAINER_NAME"; then
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
        log_success "Container antigo removido"
    else
        log_info "Nenhum container antigo encontrado"
    fi
}

# ============================================================================
# Função: Build da imagem Docker
# ============================================================================
build_image() {
    log_info "Iniciando build da imagem Docker..."
    
    cd "$PORTAL_DIR"
    
    # Build com argumentos de ambiente para produção
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
        -t "$IMAGE_NAME" \
        .
    
    log_success "Build concluído com sucesso!"
}

# ============================================================================
# Função: Criar rede se não existir
# ============================================================================
create_network() {
    log_info "Verificando rede Docker..."
    
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        log_warning "Rede $NETWORK_NAME não encontrada. Criando..."
        docker network create "$NETWORK_NAME"
        log_success "Rede criada"
    else
        log_success "Rede já existe"
    fi
}

# ============================================================================
# Função: Subir novo container
# ============================================================================
start_container() {
    log_info "Iniciando novo container..."
    
    docker run -d \
        --name "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        --restart unless-stopped \
        "$IMAGE_NAME"
    
    log_success "Container iniciado!"
}

# ============================================================================
# Função: Verificar saúde do container
# ============================================================================
check_health() {
    log_info "Verificando saúde do container..."
    
    sleep 5
    
    # Verificar se container está rodando
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        log_error "Container não está rodando!"
        docker logs "$CONTAINER_NAME" --tail 50
        exit 1
    fi
    
    # Testar endpoint de health
    if docker exec "$CONTAINER_NAME" wget --quiet --tries=1 --spider http://localhost/health; then
        log_success "Health check OK!"
    else
        log_error "Health check falhou!"
        docker logs "$CONTAINER_NAME" --tail 50
        exit 1
    fi
}

# ============================================================================
# Função: Exibir informações do deploy
# ============================================================================
show_info() {
    log_success "Deploy concluído com sucesso!"
    echo ""
    echo "📊 Informações do Deploy:"
    echo "  Container: $CONTAINER_NAME"
    echo "  Imagem: $IMAGE_NAME"
    echo "  Rede: $NETWORK_NAME"
    echo ""
    echo "🌐 URLs de Acesso:"
    echo "  https://portal.intellicare.ia.br"
    echo "  https://intellicare.ia.br (redireciona)"
    echo "  https://www.intellicare.ia.br (redireciona)"
    echo "  https://saudeplanner.com.br (redireciona)"
    echo "  https://www.saudeplanner.com.br (redireciona)"
    echo ""
    echo "🔍 Comandos Úteis:"
    echo "  docker logs $CONTAINER_NAME -f"
    echo "  docker exec -it $CONTAINER_NAME sh"
    echo "  docker restart $CONTAINER_NAME"
}

# ============================================================================
# Main
# ============================================================================
main() {
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║   🚀 Deploy do Portal IntelliCare                        ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    
    check_prerequisites
    create_network
    stop_old_container
    build_image
    start_container
    check_health
    show_info
}

# Executar
main

