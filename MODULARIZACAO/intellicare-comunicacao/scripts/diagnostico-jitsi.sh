#!/bin/bash

# ============================================================================
# SCRIPT DE DIAGNÓSTICO JITSI - SERVIDOR 161.97.141.186
# ============================================================================

set +e  # Não parar em erros

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           DIAGNÓSTICO JITSI - GATEWAY TIMEOUT              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

JITSI_PATH="/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

cd "$JITSI_PATH" 2>/dev/null || {
    echo -e "${RED}❌ Diretório não encontrado: $JITSI_PATH${NC}"
    exit 1
}

# ============================================================================
# 1. STATUS DOS CONTAINERS
# ============================================================================

echo -e "${YELLOW}📊 1. STATUS DOS CONTAINERS JITSI${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps
echo ""

# ============================================================================
# 2. VERIFICAR CONTAINER WEB
# ============================================================================

echo -e "${YELLOW}🌐 2. VERIFICAR CONTAINER WEB${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

WEB_CONTAINER=$(docker ps -q -f name=jitsi-meet-web)

if [ -z "$WEB_CONTAINER" ]; then
    echo -e "${RED}❌ Container web NÃO está rodando!${NC}"
    echo ""
    echo -e "${YELLOW}Logs do container web:${NC}"
    docker compose -f docker-compose-jitsi.yml -p jitsi-meet logs web --tail=30
else
    echo -e "${GREEN}✅ Container web está rodando: $WEB_CONTAINER${NC}"
    
    # Testar acesso interno
    echo ""
    echo -e "${YELLOW}Testando acesso interno (porta 80):${NC}"
    docker exec $WEB_CONTAINER curl -I http://localhost:80 2>&1 | head -10
    
    echo ""
    echo -e "${YELLOW}Testando acesso interno (porta 8000):${NC}"
    docker exec $WEB_CONTAINER curl -I http://localhost:8000 2>&1 | head -10
fi
echo ""

# ============================================================================
# 3. VERIFICAR REDES
# ============================================================================

echo -e "${YELLOW}🌐 3. VERIFICAR REDES${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}Redes disponíveis:${NC}"
docker network ls | grep -E "gsi|jitsi"
echo ""

if [ -n "$WEB_CONTAINER" ]; then
    echo -e "${YELLOW}Redes do container web:${NC}"
    docker inspect $WEB_CONTAINER | grep -A 10 "Networks"
fi
echo ""

# ============================================================================
# 4. VERIFICAR TRAEFIK
# ============================================================================

echo -e "${YELLOW}🔀 4. VERIFICAR TRAEFIK${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TRAEFIK_CONTAINER=$(docker ps -q -f name=traefik)

if [ -z "$TRAEFIK_CONTAINER" ]; then
    echo -e "${RED}❌ Traefik NÃO está rodando!${NC}"
else
    echo -e "${GREEN}✅ Traefik está rodando: $TRAEFIK_CONTAINER${NC}"
    echo ""
    echo -e "${YELLOW}Logs do Traefik relacionados ao Jitsi:${NC}"
    docker logs $TRAEFIK_CONTAINER 2>&1 | grep -i jitsi | tail -20
fi
echo ""

# ============================================================================
# 5. VERIFICAR LABELS DO TRAEFIK
# ============================================================================

echo -e "${YELLOW}🏷️  5. VERIFICAR LABELS DO TRAEFIK${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$WEB_CONTAINER" ]; then
    echo -e "${YELLOW}Labels do container web:${NC}"
    docker inspect $WEB_CONTAINER | grep -A 20 "Labels" | grep traefik
else
    echo -e "${RED}❌ Container web não está rodando${NC}"
fi
echo ""

# ============================================================================
# 6. VERIFICAR PORTA NO DOCKER-COMPOSE
# ============================================================================

echo -e "${YELLOW}🔌 6. VERIFICAR PORTA NO DOCKER-COMPOSE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}Porta configurada no Traefik label:${NC}"
grep "loadbalancer.server.port" docker-compose-jitsi.yml || echo "Não encontrado"
echo ""

# ============================================================================
# 7. TESTAR ACESSO LOCAL
# ============================================================================

echo -e "${YELLOW}🧪 7. TESTAR ACESSO LOCAL${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}Testando localhost:80${NC}"
curl -I http://localhost:80 2>&1 | head -5
echo ""

echo -e "${YELLOW}Testando localhost:8000${NC}"
curl -I http://localhost:8000 2>&1 | head -5
echo ""

# ============================================================================
# 8. VERIFICAR .ENV
# ============================================================================

echo -e "${YELLOW}⚙️  8. VERIFICAR .ENV${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}Configurações importantes:${NC}"
grep -E "PUBLIC_URL|XMPP_DOMAIN|ENABLE_AUTH|AUTH_TYPE" .env 2>/dev/null || echo "Arquivo .env não encontrado"
echo ""

# ============================================================================
# 9. RESUMO E RECOMENDAÇÕES
# ============================================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    RESUMO DO DIAGNÓSTICO                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar problemas comuns
PROBLEMS=0

if [ -z "$WEB_CONTAINER" ]; then
    echo -e "${RED}❌ PROBLEMA 1: Container web não está rodando${NC}"
    echo -e "   ${YELLOW}Solução: docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d${NC}"
    PROBLEMS=$((PROBLEMS + 1))
    echo ""
fi

if ! docker network ls | grep -q "docker-compose-v3_gsi_network"; then
    echo -e "${RED}❌ PROBLEMA 2: Rede gsi_network não encontrada${NC}"
    echo -e "   ${YELLOW}Solução: Verificar se Traefik está rodando e criou a rede${NC}"
    PROBLEMS=$((PROBLEMS + 1))
    echo ""
fi

if grep -q "loadbalancer.server.port=8000" docker-compose-jitsi.yml 2>/dev/null; then
    echo -e "${RED}❌ PROBLEMA 3: Porta incorreta no Traefik (8000 em vez de 80)${NC}"
    echo -e "   ${YELLOW}Solução: Alterar para port=80 no docker-compose-jitsi.yml${NC}"
    PROBLEMS=$((PROBLEMS + 1))
    echo ""
fi

if [ $PROBLEMS -eq 0 ]; then
    echo -e "${GREEN}✅ Nenhum problema óbvio detectado${NC}"
    echo -e "${YELLOW}Verifique os logs acima para mais detalhes${NC}"
else
    echo -e "${YELLOW}Total de problemas encontrados: ${PROBLEMS}${NC}"
fi

echo ""
echo -e "${YELLOW}📝 PRÓXIMOS PASSOS:${NC}"
echo "1. Corrija os problemas listados acima"
echo "2. Reinicie os containers: docker compose -f docker-compose-jitsi.yml -p jitsi-meet restart"
echo "3. Aguarde 30s e teste novamente: https://meet.gsi.srv.br"
echo ""

