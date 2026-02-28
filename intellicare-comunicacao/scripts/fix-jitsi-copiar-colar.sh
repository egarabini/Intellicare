#!/bin/bash

# ============================================================================
# CORREÇÃO JITSI DNS - COPIE E COLE NO SERVIDOR
# ============================================================================
# Problema: xmpp.meet.jitsi could not be resolved
# Solução: Adicionar network alias no docker-compose
# ============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        CORREÇÃO JITSI DNS RESOLUTION ERROR            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

cd /install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb

echo -e "${YELLOW}1. Criando backup...${NC}"
cp docker-compose-jitsi.yml docker-compose-jitsi.yml.backup.$(date +%Y%m%d_%H%M%S)
echo -e "${GREEN}✅ Backup criado${NC}"
echo ""

echo -e "${YELLOW}2. Verificando estrutura atual...${NC}"
grep -A 10 "^  prosody:" docker-compose-jitsi.yml | head -15
echo ""

echo -e "${YELLOW}3. Verificando se já tem o alias...${NC}"
if grep -q "xmpp.meet.jitsi" docker-compose-jitsi.yml; then
    echo -e "${GREEN}✅ Alias já existe!${NC}"
    HAS_ALIAS=true
else
    echo -e "${RED}❌ Alias não encontrado - vamos adicionar${NC}"
    HAS_ALIAS=false
fi
echo ""

if [ "$HAS_ALIAS" = false ]; then
    echo -e "${YELLOW}4. Adicionando alias ao serviço prosody...${NC}"
    
    # Criar arquivo temporário com a correção
    awk '
    /^  prosody:/ {
        print $0
        in_prosody = 1
        prosody_indent = ""
        next
    }
    
    in_prosody && /^    [a-z_]/ {
        if (!added_network) {
            print "    networks:"
            print "      meet.jitsi:"
            print "        aliases:"
            print "          - xmpp.meet.jitsi"
            added_network = 1
        }
        in_prosody = 0
    }
    
    in_prosody && /^  [a-z]/ {
        if (!added_network) {
            print "    networks:"
            print "      meet.jitsi:"
            print "        aliases:"
            print "          - xmpp.meet.jitsi"
            added_network = 1
        }
        in_prosody = 0
    }
    
    { print $0 }
    ' docker-compose-jitsi.yml > docker-compose-jitsi.yml.new
    
    if [ -s docker-compose-jitsi.yml.new ]; then
        mv docker-compose-jitsi.yml.new docker-compose-jitsi.yml
        echo -e "${GREEN}✅ Alias adicionado${NC}"
    else
        echo -e "${RED}❌ Erro ao adicionar alias${NC}"
        rm -f docker-compose-jitsi.yml.new
        exit 1
    fi
    echo ""
fi

echo -e "${YELLOW}5. Verificando resultado...${NC}"
grep -A 10 "^  prosody:" docker-compose-jitsi.yml | head -15
echo ""

echo -e "${YELLOW}6. Reiniciando containers...${NC}"
echo "   Parando..."
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down

echo "   Iniciando..."
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

echo "   Aguardando 20 segundos..."
sleep 20

echo -e "${GREEN}✅ Containers reiniciados${NC}"
echo ""

echo -e "${YELLOW}7. Status dos containers:${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps
echo ""

echo -e "${YELLOW}8. Testando DNS...${NC}"
WEB_CONTAINER=$(docker ps -q -f name=jitsi-meet-web)

if [ -n "$WEB_CONTAINER" ]; then
    echo "   Resolução de xmpp.meet.jitsi:"
    if docker exec $WEB_CONTAINER getent hosts xmpp.meet.jitsi 2>/dev/null; then
        echo -e "${GREEN}   ✅ DNS OK!${NC}"
    else
        echo -e "${RED}   ❌ DNS não resolveu${NC}"
    fi
    
    echo ""
    echo "   Testando /http-bind:"
    docker exec $WEB_CONTAINER curl -I http://localhost/http-bind 2>&1 | head -1
    
    echo ""
    echo "   Verificando logs (últimas 10 linhas):"
    docker logs $WEB_CONTAINER --tail 10 2>&1 | grep -i "error\|could not be resolved" || echo -e "${GREEN}   ✅ Sem erros!${NC}"
else
    echo -e "${RED}   ❌ Container web não encontrado${NC}"
fi

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  CORREÇÃO CONCLUÍDA!                  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🌐 Teste no navegador:${NC} https://meet.gsi.srv.br"
echo ""
