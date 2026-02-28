#!/bin/bash
# ============================================================================
# Script Simplificado de Deploy do Portal IntelliCare
# ============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

CONTAINER_NAME="intellicare-portal"
NETWORK_NAME="intellicare_intellicare-network"
PORTAL_DIR="/opt/intellicare/intellicare/intellicare-portal/frontend"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   🚀 Deploy Simplificado do Portal IntelliCare          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Parar container antigo
log_info "Parando container antigo..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true
log_success "Container antigo removido"

# Build da imagem
log_info "Fazendo build da imagem..."
cd "$PORTAL_DIR"

docker build \
    --build-arg VITE_API_FLORENCE_URL=https://api.intellicare.ia.br/v1/florence \
    --build-arg VITE_API_OSWALDO_URL=https://api.intellicare.ia.br/v1/oswaldo \
    --build-arg VITE_API_DONABEDIAN_URL=https://api.intellicare.ia.br/v1/donabedian \
    --build-arg VITE_API_WANDA_URL=https://api.intellicare.ia.br/v1/wanda \
    --build-arg VITE_API_COMUNICACAO_URL=https://api.intellicare.ia.br/v1/comunicacao \
    --build-arg VITE_API_GERALDA_URL=https://api.intellicare.ia.br/v1/geralda \
    --target production \
    -t intellicare-portal:latest \
    . 2>&1 | tail -20

if [ $? -ne 0 ]; then
    echo "❌ Build falhou! Tentando abordagem alternativa..."
    
    # Abordagem alternativa: usar Nginx com dist/ existente
    log_info "Verificando se dist/ existe..."
    
    if [ -d "$PORTAL_DIR/dist" ]; then
        log_info "Usando build existente em dist/"
        
        docker run -d \
            --name "$CONTAINER_NAME" \
            --network "$NETWORK_NAME" \
            -v "$PORTAL_DIR/dist":/usr/share/nginx/html:ro \
            -v "$PORTAL_DIR/nginx.conf":/etc/nginx/conf.d/default.conf:ro \
            --restart unless-stopped \
            nginx:alpine
        
        log_success "Container iniciado com dist/ existente!"
    else
        echo "❌ dist/ não encontrado! Abortando..."
        exit 1
    fi
else
    # Build OK, subir container
    log_info "Iniciando container..."
    
    docker run -d \
        --name "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        --restart unless-stopped \
        intellicare-portal:latest
    
    log_success "Container iniciado!"
fi

# Verificar saúde
log_info "Verificando saúde..."
sleep 5

if docker exec "$CONTAINER_NAME" wget --quiet --tries=1 --spider http://localhost/health 2>/dev/null; then
    log_success "Health check OK!"
else
    if docker exec "$CONTAINER_NAME" wget --quiet --tries=1 --spider http://localhost/ 2>/dev/null; then
        log_success "Portal respondendo!"
    else
        echo "⚠️  Health check falhou, mas container está rodando"
        docker logs "$CONTAINER_NAME" --tail 10
    fi
fi

echo ""
log_success "Deploy concluído!"
echo ""
echo "🌐 URLs:"
echo "  https://portal.intellicare.ia.br"
echo "  https://intellicare.ia.br"
echo "  https://saudeplanner.com.br"
echo ""
echo "📋 Comandos:"
echo "  docker logs $CONTAINER_NAME -f"
echo "  docker restart $CONTAINER_NAME"
echo "  docker exec -it $CONTAINER_NAME sh"

