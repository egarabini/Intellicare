#!/bin/bash

# ============================================================================
# SCRIPT DE INICIALIZAÇÃO - ROCKET.CHAT
# ============================================================================
# Projeto 05: Sistema de Comunicação e Workflow Integrado
# Responsável: DEV1
# Data: 26/03/2026
# ============================================================================

set -e

echo "🚀 Iniciando configuração do Rocket.Chat..."

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Carregar variáveis de ambiente
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}❌ Arquivo .env não encontrado!${NC}"
    exit 1
fi

# Função para aguardar serviço
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ Aguardando $service...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service está pronto!${NC}"
            return 0
        fi
        echo "   Tentativa $attempt/$max_attempts..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service não respondeu após $max_attempts tentativas${NC}"
    return 1
}

# 1. Verificar se containers estão rodando
echo ""
echo "📦 Verificando containers..."
docker-compose ps

# 2. Aguardar MongoDB
echo ""
wait_for_service "MongoDB" "http://localhost:27017" || true

# 3. Aguardar Rocket.Chat
echo ""
wait_for_service "Rocket.Chat" "http://localhost:3000/api/info"

# 4. Obter informações de login
echo ""
echo "🔐 Informações de Login:"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "URL:      ${YELLOW}http://localhost:3000${NC}"
echo -e "Usuário:  ${YELLOW}${ROCKETCHAT_ADMIN_USER}${NC}"
echo -e "Senha:    ${YELLOW}${ROCKETCHAT_ADMIN_PASSWORD}${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 5. Aguardar login manual e obter token
echo ""
echo "📝 Para criar canais automaticamente, faça login e execute:"
echo ""
echo "   1. Acesse: http://localhost:3000"
echo "   2. Faça login com as credenciais acima"
echo "   3. Vá em: Perfil → Minha Conta → Tokens Pessoais"
echo "   4. Crie um token e execute:"
echo ""
echo "      export ROCKETCHAT_TOKEN='seu-token'"
echo "      export ROCKETCHAT_USER_ID='seu-user-id'"
echo "      ./scripts/create-channels.sh"
echo ""

# 6. Verificar Jitsi
echo ""
echo "🎥 Verificando Jitsi..."
if curl -s -f "http://localhost:8443" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Jitsi está rodando!${NC}"
    echo -e "URL: ${YELLOW}http://localhost:8443${NC}"
else
    echo -e "${YELLOW}⚠️  Jitsi ainda não está pronto (pode levar alguns minutos)${NC}"
fi

# 7. Resumo
echo ""
echo "🎊 Configuração Inicial Completa!"
echo ""
echo "📋 Próximos Passos:"
echo "   1. ✅ Rocket.Chat rodando em http://localhost:3000"
echo "   2. ✅ Jitsi rodando em http://localhost:8443"
echo "   3. ⏳ Fazer login no Rocket.Chat"
echo "   4. ⏳ Criar canais: #geral, #alertas, #suporte"
echo "   5. ⏳ Testar integração com Jitsi"
echo ""
echo "📚 Documentação: README.md"
echo ""

