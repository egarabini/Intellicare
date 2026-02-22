#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

SERVER_IP="161.97.141.186"
SERVER_USER="root"
SERVER_PORT="22"
JITSI_PATH="/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          EXECUTAR CORREÇÃO JITSI DNS - REMOTO             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}🌐 Servidor:${NC} $SERVER_USER@$SERVER_IP:$SERVER_PORT"
echo -e "${YELLOW}📁 Diretório:${NC} $JITSI_PATH"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ ! -f "$SCRIPT_DIR/fix-jitsi-dns-simple.sh" ]; then
    echo -e "${RED}❌ Script fix-jitsi-dns-simple.sh não encontrado${NC}"
    exit 1
fi

echo -e "${YELLOW}📤 1. Transferindo script para o servidor...${NC}"

scp -P $SERVER_PORT "$SCRIPT_DIR/fix-jitsi-dns-simple.sh" $SERVER_USER@$SERVER_IP:$JITSI_PATH/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Script transferido${NC}"
else
    echo -e "${RED}❌ Erro ao transferir script${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🚀 2. Executando correção no servidor...${NC}"
echo ""

ssh -p $SERVER_PORT $SERVER_USER@$SERVER_IP << 'ENDSSH'
cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "EXECUTANDO CORREÇÃO..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

chmod +x fix-jitsi-dns-simple.sh
./fix-jitsi-dns-simple.sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TESTE FINAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sleep 5

WEB_CONTAINER=$(docker ps -q -f name=jitsi-meet-web)

if [ -n "$WEB_CONTAINER" ]; then
    echo ""
    echo "✅ Testando DNS resolution..."
    docker exec $WEB_CONTAINER getent hosts xmpp.meet.jitsi || echo "❌ DNS falhou"
    
    echo ""
    echo "✅ Testando /http-bind endpoint..."
    docker exec $WEB_CONTAINER curl -s -I http://localhost/http-bind | head -1
    
    echo ""
    echo "📋 Últimos logs (procurando erros)..."
    docker logs $WEB_CONTAINER 2>&1 | tail -10 | grep -i "error\|could not be resolved" || echo "✅ Sem erros!"
fi

ENDSSH

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   EXECUÇÃO CONCLUÍDA!                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🌐 Teste no navegador:${NC}"
echo "   https://meet.gsi.srv.br"
echo ""
echo -e "${YELLOW}📝 Se funcionou, próximo passo:${NC}"
echo "   Configurar autenticação Keycloak"
echo ""
