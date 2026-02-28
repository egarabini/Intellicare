#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     CORREÇÃO: JITSI DNS - xmpp.meet.jitsi not found       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

JITSI_PATH="/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

cd "$JITSI_PATH" || {
    echo -e "${RED}❌ Diretório não encontrado: $JITSI_PATH${NC}"
    exit 1
}

echo -e "${YELLOW}📋 1. DIAGNÓSTICO INICIAL${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}Status dos containers:${NC}"
docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps

echo ""
echo -e "${YELLOW}📋 2. VERIFICAR REDES${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

WEB_CONTAINER=$(docker ps -q -f name=jitsi-meet-web)
PROSODY_CONTAINER=$(docker ps -q -f name=jitsi-meet-prosody)

if [ -z "$WEB_CONTAINER" ]; then
    echo -e "${RED}❌ Container web não está rodando!${NC}"
    exit 1
fi

if [ -z "$PROSODY_CONTAINER" ]; then
    echo -e "${RED}❌ Container prosody não está rodando!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Containers encontrados:${NC}"
echo "   Web: $WEB_CONTAINER"
echo "   Prosody: $PROSODY_CONTAINER"
echo ""

echo -e "${YELLOW}Verificando redes do container WEB:${NC}"
WEB_NETWORKS=$(docker inspect $WEB_CONTAINER --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}')
echo "   Redes: $WEB_NETWORKS"
echo ""

echo -e "${YELLOW}Verificando redes do container PROSODY:${NC}"
PROSODY_NETWORKS=$(docker inspect $PROSODY_CONTAINER --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}} {{end}}')
echo "   Redes: $PROSODY_NETWORKS"
echo ""

echo -e "${YELLOW}📋 3. TESTAR RESOLUÇÃO DNS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}Testando resolução de 'xmpp.meet.jitsi' no container web:${NC}"
if docker exec $WEB_CONTAINER nslookup xmpp.meet.jitsi 2>&1; then
    echo -e "${GREEN}✅ DNS funcionando!${NC}"
else
    echo -e "${RED}❌ DNS não funciona - vamos corrigir${NC}"
fi
echo ""

echo -e "${YELLOW}Testando resolução de 'prosody' no container web:${NC}"
if docker exec $WEB_CONTAINER nslookup prosody 2>&1; then
    echo -e "${GREEN}✅ DNS para 'prosody' funciona!${NC}"
else
    echo -e "${RED}❌ DNS para 'prosody' não funciona${NC}"
fi
echo ""

echo -e "${YELLOW}📋 4. VERIFICAR NOME DOS SERVIÇOS NO DOCKER-COMPOSE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}Nomes de serviços definidos:${NC}"
grep "^  [a-z]" docker-compose-jitsi.yml | grep -v "version:" | head -10
echo ""

echo -e "${YELLOW}📋 5. VERIFICAR HOSTNAME DO PROSODY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PROSODY_HOSTNAME=$(docker inspect $PROSODY_CONTAINER --format='{{.Config.Hostname}}')
echo "   Hostname: $PROSODY_HOSTNAME"
echo ""

echo -e "${YELLOW}Aliases de rede do Prosody:${NC}"
docker inspect $PROSODY_CONTAINER --format='{{range $key, $value := .NetworkSettings.Networks}}{{$key}}: {{$value.Aliases}}{{"\n"}}{{end}}'
echo ""

echo -e "${YELLOW}📋 6. SOLUÇÕES POSSÍVEIS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}O problema é que o nginx no container web tenta se conectar a:${NC}"
echo "   http://xmpp.meet.jitsi:5280/http-bind"
echo ""
echo -e "${BLUE}Mas esse hostname não existe na rede Docker!${NC}"
echo ""
echo -e "${YELLOW}SOLUÇÃO 1: Adicionar network_alias no docker-compose${NC}"
echo "   Adicionar 'xmpp.meet.jitsi' como alias do serviço prosody"
echo ""
echo -e "${YELLOW}SOLUÇÃO 2: Modificar configuração do nginx${NC}"
echo "   Trocar 'xmpp.meet.jitsi' pelo nome correto do serviço"
echo ""

read -p "Deseja aplicar SOLUÇÃO 1 (adicionar network alias)? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo -e "${YELLOW}📋 7. APLICANDO SOLUÇÃO 1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo -e "${YELLOW}Backup do docker-compose:${NC}"
    BACKUP_FILE="docker-compose-jitsi.yml.backup.$(date +%Y%m%d_%H%M%S)"
    cp docker-compose-jitsi.yml "$BACKUP_FILE"
    echo -e "${GREEN}✅ Backup: $BACKUP_FILE${NC}"
    echo ""
    
    echo -e "${YELLOW}Verificando estrutura atual do serviço prosody:${NC}"
    grep -A 20 "^  prosody:" docker-compose-jitsi.yml
    echo ""
    
    echo -e "${RED}ATENÇÃO: Você precisa editar manualmente o docker-compose-jitsi.yml${NC}"
    echo ""
    echo -e "${YELLOW}Adicione as seguintes linhas no serviço 'prosody':${NC}"
    echo ""
    echo "  prosody:"
    echo "    networks:"
    echo "      meet.jitsi:"
    echo "        aliases:"
    echo "          - xmpp.meet.jitsi"
    echo ""
    echo -e "${YELLOW}Depois execute:${NC}"
    echo "  docker compose -f docker-compose-jitsi.yml -p jitsi-meet down"
    echo "  docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d"
    echo ""
fi

read -p "Deseja aplicar SOLUÇÃO 2 (modificar nginx config)? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo -e "${YELLOW}📋 8. APLICANDO SOLUÇÃO 2${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo -e "${YELLOW}Verificando configuração nginx atual:${NC}"
    docker exec $WEB_CONTAINER cat /config/nginx/meet.conf | grep -A 5 "location = /http-bind"
    echo ""
    
    echo -e "${YELLOW}Qual é o nome correto do serviço prosody no docker-compose?${NC}"
    echo "Opções comuns:"
    echo "  1. prosody"
    echo "  2. jitsi-meet-prosody-1"
    echo "  3. prosody.meet.jitsi"
    read -p "Digite o nome: " PROSODY_SERVICE_NAME
    
    if [ -n "$PROSODY_SERVICE_NAME" ]; then
        echo ""
        echo -e "${YELLOW}Modificando configuração nginx...${NC}"
        
        docker exec $WEB_CONTAINER sed -i "s|http://xmpp.meet.jitsi:5280|http://$PROSODY_SERVICE_NAME:5280|g" /config/nginx/meet.conf
        
        echo -e "${GREEN}✅ Configuração modificada${NC}"
        echo ""
        echo -e "${YELLOW}Nova configuração:${NC}"
        docker exec $WEB_CONTAINER cat /config/nginx/meet.conf | grep -A 5 "location = /http-bind"
        echo ""
        
        echo -e "${YELLOW}Recarregando nginx...${NC}"
        docker exec $WEB_CONTAINER nginx -s reload
        echo -e "${GREEN}✅ Nginx recarregado${NC}"
        echo ""
        
        echo -e "${YELLOW}Testando conexão:${NC}"
        docker exec $WEB_CONTAINER curl -I http://localhost/http-bind
        echo ""
    fi
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    DIAGNÓSTICO COMPLETO                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
