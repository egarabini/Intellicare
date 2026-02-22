#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       CORREÇÃO AUTOMÁTICA: JITSI DNS RESOLUTION            ║${NC}"
echo -e "${BLUE}║          xmpp.meet.jitsi could not be resolved             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

JITSI_PATH="/install/desenvolvimento/docker-compose-v3/jitsi-docker-jitsi-meet-35879bb"

cd "$JITSI_PATH" || {
    echo -e "${RED}❌ Diretório não encontrado: $JITSI_PATH${NC}"
    exit 1
}

if [ ! -f "docker-compose-jitsi.yml" ]; then
    echo -e "${RED}❌ docker-compose-jitsi.yml não encontrado${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 1. BACKUP DO DOCKER-COMPOSE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BACKUP_FILE="docker-compose-jitsi.yml.backup.$(date +%Y%m%d_%H%M%S)"
cp docker-compose-jitsi.yml "$BACKUP_FILE"
echo -e "${GREEN}✅ Backup criado: $BACKUP_FILE${NC}"
echo ""

echo -e "${YELLOW}📋 2. ANALISANDO ESTRUTURA ATUAL${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if grep -q "xmpp\.meet\.jitsi" docker-compose-jitsi.yml; then
    echo -e "${YELLOW}⚠️  Alias 'xmpp.meet.jitsi' já existe no docker-compose${NC}"
    echo ""
    echo -e "${YELLOW}Verificando onde está definido:${NC}"
    grep -n "xmpp.meet.jitsi" docker-compose-jitsi.yml
    echo ""
else
    echo -e "${YELLOW}❌ Alias 'xmpp.meet.jitsi' NÃO encontrado${NC}"
fi

echo -e "${YELLOW}Verificando serviço prosody:${NC}"
if grep -q "^  prosody:" docker-compose-jitsi.yml; then
    echo -e "${GREEN}✅ Serviço 'prosody' encontrado${NC}"
    PROSODY_SERVICE="prosody"
elif grep -q "^  xmpp:" docker-compose-jitsi.yml; then
    echo -e "${GREEN}✅ Serviço 'xmpp' encontrado${NC}"
    PROSODY_SERVICE="xmpp"
else
    echo -e "${RED}❌ Serviço prosody/xmpp não encontrado${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}📋 3. APLICANDO CORREÇÃO${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cat > /tmp/fix-jitsi-dns.py << 'PYTHON_SCRIPT'
import yaml
import sys

def fix_jitsi_dns(file_path):
    with open(file_path, 'r') as f:
        compose = yaml.safe_load(f)
    
    if 'services' not in compose:
        print("❌ Chave 'services' não encontrada")
        return False
    
    prosody_service = None
    if 'prosody' in compose['services']:
        prosody_service = 'prosody'
    elif 'xmpp' in compose['services']:
        prosody_service = 'xmpp'
    else:
        print("❌ Serviço prosody/xmpp não encontrado")
        return False
    
    service = compose['services'][prosody_service]
    
    if 'networks' not in service:
        service['networks'] = {}
    
    network_name = None
    for net_key in service['networks']:
        if 'meet.jitsi' in net_key or 'jitsi' in net_key:
            network_name = net_key
            break
    
    if not network_name:
        for net in compose.get('networks', {}):
            if 'meet.jitsi' in net or 'jitsi' in net:
                network_name = net
                break
    
    if not network_name:
        network_name = 'meet.jitsi'
    
    if isinstance(service['networks'], dict):
        if network_name not in service['networks']:
            service['networks'][network_name] = {}
        
        if not isinstance(service['networks'][network_name], dict):
            service['networks'][network_name] = {}
        
        if 'aliases' not in service['networks'][network_name]:
            service['networks'][network_name]['aliases'] = []
        
        if 'xmpp.meet.jitsi' not in service['networks'][network_name]['aliases']:
            service['networks'][network_name]['aliases'].append('xmpp.meet.jitsi')
            print(f"✅ Adicionado alias 'xmpp.meet.jitsi' ao serviço '{prosody_service}'")
    elif isinstance(service['networks'], list):
        service['networks'] = {
            network_name: {
                'aliases': ['xmpp.meet.jitsi']
            }
        }
        print(f"✅ Convertido networks para dict e adicionado alias 'xmpp.meet.jitsi'")
    
    with open(file_path, 'w') as f:
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False)
    
    return True

if __name__ == '__main__':
    success = fix_jitsi_dns(sys.argv[1])
    sys.exit(0 if success else 1)
PYTHON_SCRIPT

if command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Aplicando correção com Python...${NC}"
    if python3 /tmp/fix-jitsi-dns.py docker-compose-jitsi.yml; then
        echo -e "${GREEN}✅ Correção aplicada com sucesso${NC}"
        FIXED=true
    else
        echo -e "${RED}❌ Falha ao aplicar correção com Python${NC}"
        FIXED=false
    fi
else
    echo -e "${YELLOW}Python3 não disponível, aplicando correção manual...${NC}"
    
    sed -i "/^  $PROSODY_SERVICE:/a\\    networks:\\n      meet.jitsi:\\n        aliases:\\n          - xmpp.meet.jitsi" docker-compose-jitsi.yml
    
    echo -e "${GREEN}✅ Correção aplicada${NC}"
    FIXED=true
fi

rm -f /tmp/fix-jitsi-dns.py
echo ""

echo -e "${YELLOW}📋 4. VERIFICANDO CORREÇÃO${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "${YELLOW}Configuração do serviço prosody após correção:${NC}"
grep -A 10 "^  $PROSODY_SERVICE:" docker-compose-jitsi.yml | head -15
echo ""

echo -e "${YELLOW}📋 5. REINICIAR CONTAINERS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

read -p "Deseja reiniciar os containers agora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo -e "${YELLOW}Parando containers...${NC}"
    docker compose -f docker-compose-jitsi.yml -p jitsi-meet down
    
    echo ""
    echo -e "${YELLOW}Iniciando containers...${NC}"
    docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d
    
    echo ""
    echo -e "${YELLOW}Aguardando containers iniciarem (15 segundos)...${NC}"
    sleep 15
    
    echo ""
    echo -e "${YELLOW}Status dos containers:${NC}"
    docker compose -f docker-compose-jitsi.yml -p jitsi-meet ps
    
    echo ""
    echo -e "${YELLOW}📋 6. TESTE DE CONECTIVIDADE${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    WEB_CONTAINER=$(docker ps -q -f name=jitsi-meet-web)
    
    if [ -n "$WEB_CONTAINER" ]; then
        echo -e "${YELLOW}Testando resolução DNS de 'xmpp.meet.jitsi':${NC}"
        if docker exec $WEB_CONTAINER getent hosts xmpp.meet.jitsi; then
            echo -e "${GREEN}✅ DNS funciona!${NC}"
        else
            echo -e "${RED}❌ DNS ainda não funciona${NC}"
        fi
        
        echo ""
        echo -e "${YELLOW}Testando HTTP bind:${NC}"
        docker exec $WEB_CONTAINER curl -I http://localhost/http-bind
        
        echo ""
        echo -e "${YELLOW}Logs recentes do web:${NC}"
        docker logs $WEB_CONTAINER --tail 10
    fi
else
    echo ""
    echo -e "${YELLOW}⚠️  Para aplicar as mudanças, execute:${NC}"
    echo "   cd $JITSI_PATH"
    echo "   docker compose -f docker-compose-jitsi.yml -p jitsi-meet down"
    echo "   docker compose -f docker-compose-jitsi.yml -p jitsi-meet up -d"
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    CORREÇÃO COMPLETA!                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Arquivo de backup:${NC} $BACKUP_FILE"
echo ""
echo -e "${YELLOW}Para testar acesse:${NC} https://meet.gsi.srv.br"
