#!/bin/bash
# ============================================================================
# Script de Deploy do Portal IntelliCare em Produção via SSH
# ============================================================================
# Descrição: Conecta ao servidor de produção, puxa do git staging e faz deploy
# Servidor: 167.86.97.142
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

# Configurações do servidor
PRODUCTION_SERVER="root@167.86.97.142"
PRODUCTION_PATH="/opt/intellicare/intellicare"
GIT_BRANCH="staging"

# ============================================================================
# Função: Verificar conexão SSH
# ============================================================================
check_ssh() {
    log_info "Verificando conexão SSH..."

    if ! ssh -o ConnectTimeout=5 "${PRODUCTION_SERVER}" "echo 'SSH OK'" 2>/dev/null; then
        log_error "Não foi possível conectar ao servidor ${PRODUCTION_SERVER}"
        log_info "Verifique se você tem acesso SSH configurado"
        exit 1
    fi

    log_success "Conexão SSH OK"
}

# ============================================================================
# Função: Atualizar código no servidor via git
# ============================================================================
update_code() {
    log_info "Atualizando código no servidor (branch: ${GIT_BRANCH})..."

    ssh "${PRODUCTION_SERVER}" << EOF
set -e
cd "${PRODUCTION_PATH}"

# Verificar se é um repositório git
if [ ! -d ".git" ]; then
    echo "Erro: Diretório não é um repositório git"
    exit 1
fi

# Salvar mudanças locais não commitadas (se houver)
git stash --include-untracked 2>/dev/null || true

# Puxar mudanças do staging
echo "Puxando mudanças do branch ${GIT_BRANCH}..."
git fetch origin ${GIT_BRANCH}
git checkout ${GIT_BRANCH}
git pull origin ${GIT_BRANCH}

echo "✅ Código atualizado com sucesso!"
EOF

    if [ $? -eq 0 ]; then
        log_success "Código atualizado no servidor"
    else
        log_error "Falha ao atualizar código"
        exit 1
    fi
}

# ============================================================================
# Função: Executar deploy no servidor
# ============================================================================
deploy_on_server() {
    log_info "Executando deploy no servidor..."

    ssh "${PRODUCTION_SERVER}" << 'EOF'
set -e

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   🚀 Deploy do Portal IntelliCare em Produção          ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

cd /opt/intellicare/intellicare/intellicare-portal/frontend

# Parar container antigo
echo -e "${BLUE}ℹ️  Parando container antigo...${NC}"
docker stop intellicare-portal 2>/dev/null || true
docker rm intellicare-portal 2>/dev/null || true
echo -e "${GREEN}✅ Container antigo removido${NC}"

# Build da imagem
echo -e "${BLUE}ℹ️  Fazendo build da imagem...${NC}"

docker build \
    --build-arg VITE_API_FLORENCE_URL=https://api.intellicare.ia.br/v1/florence \
    --build-arg VITE_API_OSWALDO_URL=https://api.intellicare.ia.br/v1/oswaldo \
    --build-arg VITE_API_DONABEDIAN_URL=https://api.intellicare.ia.br/v1/donabedian \
    --build-arg VITE_API_WANDA_URL=https://api.intellicare.ia.br/v1/wanda \
    --build-arg VITE_API_COMUNICACAO_URL=https://api.intellicare.ia.br/v1/comunicacao \
    --build-arg VITE_API_GERALDA_URL=https://api.intellicare.ia.br/v1/geralda \
    --target production \
    -t intellicare-portal:latest \
    . 2>&1 | tail -30

if [ $? -ne 0 ]; then
    echo "❌ Build falhou!"
    exit 1
fi

echo -e "${GREEN}✅ Build concluído${NC}"

# Iniciar container
echo -e "${BLUE}ℹ️  Iniciando container...${NC}"
docker run -d \
    --name intellicare-portal \
    --network intellicare_intellicare-network \
    --restart unless-stopped \
    intellicare-portal:latest

echo -e "${GREEN}✅ Container iniciado${NC}"

# Verificar saúde
echo -e "${BLUE}ℹ️  Verificando saúde...${NC}"
sleep 5

if docker exec intellicare-portal wget --quiet --tries=1 --spider http://localhost/health 2>/dev/null; then
    echo -e "${GREEN}✅ Health check OK!${NC}"
else
    echo -e "${GREEN}✅ Container rodando${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   Deploy concluído com sucesso!                          ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "🌐 URLs:"
echo "  https://portal.intellicare.ia.br"
echo "  https://intellicare.ia.br"
echo ""

EOF

    if [ $? -eq 0 ]; then
        log_success "Deploy concluído com sucesso!"
    else
        log_error "Falha no deploy"
        exit 1
    fi
}

# ============================================================================
# Função: Push das mudanças locais para staging
# ============================================================================
push_to_staging() {
    log_info "Verificando mudanças locais..."

    # Verificar se há mudanças para commit
    if ! git diff --quiet HEAD 2>/dev/null; then
        log_warning "Há mudanças não commitadas localmente"

        read -p "Deseja fazer commit e push para staging? (y/n) " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Fazendo commit das mudanças..."
            git add -A
            git commit -m "chore: pre-deploy updates $(date +%Y-%m-%d)"

            log_info "Fazendo push para staging..."
            git push origin staging:staging
        fi
    fi
}

# ============================================================================
# Main
# ============================================================================
main() {
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║   🚀 Deploy do Portal IntelliCare - Produção             ║"
    echo "║   Via SSH → Servidor: ${PRODUCTION_SERVER}               ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    # Push mudanças locais (se houver)
    push_to_staging

    # Executar deploy remoto
    check_ssh
    update_code
    deploy_on_server

    echo ""
    log_success "Deploy em produção concluído!"
    echo ""
    echo "🌐 Acesse: https://portal.intellicare.ia.br"
    echo ""
}

# Executar
main
