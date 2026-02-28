#!/bin/bash
# ============================================================================
# Script de Deploy do Portal IntelliCare (usando dist/ local)
# ============================================================================
# Descrição: Deploy do portal usando build local já pronto
# Data: 2026-02-27
# Versão: 1.0.0
# ============================================================================

set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

CONTAINER_NAME="intellicare-portal"
NETWORK_NAME="intellicare_intellicare-network"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   🚀 Deploy do Portal IntelliCare (dist local)           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Parar container antigo
log_info "Parando container antigo..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true
log_success "Container antigo removido"

# Criar diretório temporário
log_info "Preparando arquivos..."
mkdir -p /tmp/portal-dist
rm -rf /tmp/portal-dist/*

# Copiar nginx.conf
cat > /tmp/portal-dist/nginx.conf << 'EOF'
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location ~* \.html$ {
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

log_success "Arquivos preparados"

# Subir container com volume
log_info "Iniciando container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    -v /opt/intellicare/portal-dist:/usr/share/nginx/html:ro \
    -v /tmp/portal-dist/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
    --restart unless-stopped \
    nginx:alpine

log_success "Container iniciado!"

# Verificar saúde
log_info "Verificando saúde..."
sleep 3

if docker exec "$CONTAINER_NAME" wget --quiet --tries=1 --spider http://localhost/health; then
    log_success "Health check OK!"
else
    echo "❌ Health check falhou!"
    docker logs "$CONTAINER_NAME"
    exit 1
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

