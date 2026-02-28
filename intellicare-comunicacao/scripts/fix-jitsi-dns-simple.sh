#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            FIX RÁPIDO: JITSI DNS RESOLUTION                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

JITSI_PATH="/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

cd "$JITSI_PATH" || {
    echo -e "${RED}❌ Erro: Diretório não encontrado${NC}"
    exit 1
}

echo -e "${YELLOW}🔍 Problema identificado:${NC}"
echo "   O nginx não consegue resolver: xmpp.meet.jitsi"
echo ""

echo -e "${YELLOW}🔧 Solução:${NC}"
echo "   Adicionar alias 'xmpp.meet.jitsi' ao serviço prosody"
echo ""

echo -e "${YELLOW}📦 1. Backup...${NC}"
BACKUP="docker-compose-jitsi.yml.backup.$(date +%Y%m%d_%H%M%S)"
cp docker-compose-jitsi.yml "$BACKUP"
echo -e "${GREEN}✅ Backup: $BACKUP${NC}"
echo ""

echo -e "${YELLOW}📝 2. Verificando docker-compose...${NC}"

if grep -q "aliases:" docker-compose-jitsi.yml && grep -q "xmpp.meet.jitsi" docker-compose-jitsi.yml; then
    echo -e "${GREEN}✅ Alias já existe! Vamos apenas reiniciar...${NC}"
    NEEDS_FIX=false
else
    echo -e "${YELLOW}⚠️  Alias não encontrado. Aplicando correção...${NC}"
    NEEDS_FIX=true
fi
echo ""

if [ "$NEEDS_FIX" = true ]; then
    echo -e "${YELLOW}📝 3. Editando docker-compose-jitsi.yml...${NC}"
    
    cat > /tmp/add_alias.awk << 'AWK_SCRIPT'
/^  prosody:/ {
    print $0
    in_prosody = 1
    has_networks = 0
    next
}

in_prosody && /^  [a-z]/ {
    if (!has_networks) {
        print "    networks:"
        print "      meet.jitsi:"
        print "        aliases:"
        print "          - xmpp.meet.jitsi"
    }
    in_prosody = 0
    has_networks = 0
}

in_prosody && /^    networks:/ {
    print $0
    has_networks = 1
    next
}

in_prosody && has_networks && /^      meet\.jitsi:/ {
    print $0
    getline
    if ($0 !~ /aliases:/) {
        print "        aliases:"
        print "          - xmpp.meet.jitsi"
    }
    next
}

{ print $0 }
AWK_SCRIPT

    awk -f /tmp/add_alias.awk docker-compose-jitsi.yml > /tmp/docker-compose-jitsi-fixed.yml
    
    if [ -s /tmp/docker-compose-jitsi-fixed.yml ]; then
        mv /tmp/docker-compose-jitsi-fixed.yml docker-compose-jitsi.yml
        echo -e "${GREEN}✅ Arquivo atualizado${NC}"
    else
        echo -e "${RED}❌ Erro ao processar arquivo${NC}"
        rm -f /tmp/add_alias.awk /tmp/docker-compose-jitsi-fixed.yml
        exit 1
    fi
    
    rm -f /tmp/add_alias.awk
    echo ""
fi

echo -e "${YELLOW}📋 4. Verificando resultado...${NC}"
echo ""
grep -A 15 "^  prosody:" docker-compose-jitsi.yml | head -20
echo ""

echo -e "${YELLOW}🔄 5. Reiniciando containers...${NC}"
echo ""

echo -e "${YELLOW}   Parando...${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet down

echo ""
echo -e "${YELLOW}   Iniciando...${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d

echo ""
echo -e "${YELLOW}   Aguardando (20s)...${NC}"
sleep 20

echo ""
echo -e "${YELLOW}📊 6. Status:${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps

echo ""
echo -e "${YELLOW}🧪 7. Testando DNS...${NC}"
echo ""

WEB_CONTAINER=$(docker ps -q -f name=jitsi-meet-web)

if [ -n "$WEB_CONTAINER" ]; then
    echo -e "${YELLOW}   Resolução de xmpp.meet.jitsi:${NC}"
    if docker exec $WEB_CONTAINER getent hosts xmpp.meet.jitsi 2>/dev/null; then
        echo -e "${GREEN}   ✅ DNS OK!${NC}"
    else
        echo -e "${RED}   ❌ DNS falhou${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}   Testando /http-bind:${NC}"
    docker exec $WEB_CONTAINER curl -I http://localhost/http-bind 2>&1 | head -5
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                      CONCLUÍDO!                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos passos:${NC}"
echo "   1. Teste: https://meet.gsi.srv.br"
echo "   2. Se funcionar, configure Keycloak"
echo ""
echo -e "${YELLOW}💾 Backup salvo em:${NC}"
echo "   $BACKUP"
