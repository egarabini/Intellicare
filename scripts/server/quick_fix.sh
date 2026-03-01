#!/bin/bash
# ============================================================================
# IntelliCare — Quick Fix for Server 167.86.97.142
# ============================================================================
# Este script deve ser executado no servidor como root
# ============================================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}IntelliCare — Atualização do Servidor 167.86.97.142${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Verificar se está rodando como root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERRO: Este script deve ser executado como root${NC}"
    echo "Use: sudo bash $0"
    exit 1
fi

# ============================================================================
# PASSO 1: Diagnóstico
# ============================================================================
echo -e "${YELLOW}PASSO 1: Diagnóstico do Sistema${NC}"
echo "========================================"
echo ""

# Verificar versão do Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version 2>&1 || echo "ERRO")
    echo "Docker: $DOCKER_VERSION"
else
    echo "Docker: NÃO INSTALADO"
fi

# Verificar versão do Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version 2>&1 || echo "ERRO")
    echo "Docker Compose: $COMPOSE_VERSION"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version 2>&1 || echo "ERRO")
    echo "Docker Compose (plugin): $COMPOSE_VERSION"
else
    echo "Docker Compose: NÃO INSTALADO"
fi

# Verificar sistema operacional
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "Sistema: $PRETTY_NAME"
else
    echo "Sistema: Desconhecido"
fi

echo ""
echo -e "${YELLOW}Containers IntelliCare:${NC}"
docker ps --all --filter "name=intellicare" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null || echo "  Não foi possível listar containers"

echo ""
read -p "Pressione ENTER para continuar..."
echo ""

# ============================================================================
# PASSO 2: Atualizar Docker
# ============================================================================
echo -e "${YELLOW}PASSO 2: Atualizar Docker${NC}"
echo "========================================"
echo ""

read -p "Deseja atualizar o Docker agora? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW} Pulando atualização do Docker${NC}"
else
    echo -e "${GREEN}Iniciando atualização do Docker...${NC}"
    echo ""

    # Detectar sistema operacional
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        echo -e "${RED}Não foi possível detectar o sistema operacional${NC}"
        exit 1
    fi

    # Atualizar para Debian/Ubuntu
    if [ "$OS" = "debian" ] || [ "$OS" = "ubuntu" ]; then
        echo "Sistema detectado: ${OS^}"
        echo ""

        # Remover versão antiga
        echo "Removendo versão antiga..."
        apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

        # Atualizar repositório
        echo "Atualizando repositórios..."
        apt-get update -qq

        # Instalar dependências
        echo "Instalando dependências..."
        apt-get install -y -qq ca-certificates curl gnupg lsb-release > /dev/null

        # Adicionar chave GPG
        echo "Adicionando chave GPG do Docker..."
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/${OS}/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

        # Adicionar repositório
        echo "Adicionando repositório do Docker..."
        echo \
          "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${OS} \
          $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

        # Atualizar novamente
        apt-get update -qq

        # Instalar Docker
        echo "Instalando Docker Engine..."
        apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        # Habilitar e iniciar
        echo "Habilitando Docker..."
        systemctl enable docker
        systemctl start docker

        echo -e "${GREEN}✓ Docker atualizado com sucesso!${NC}"
        docker --version

    # Atualizar para CentOS/RHEL
    elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "rocky" ]; then
        echo "Sistema detectado: ${OS^}"
        echo ""

        # Remover versão antiga
        echo "Removendo versão antiga..."
        yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true

        # Instalar dependências
        echo "Instalando dependências..."
        yum install -y -q yum-utils

        # Adicionar repositório
        echo "Adicionando repositório do Docker..."
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo -y

        # Instalar Docker
        echo "Instalando Docker Engine..."
        yum install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

        # Habilitar e iniciar
        echo "Habilitando Docker..."
        systemctl enable docker
        systemctl start docker

        echo -e "${GREEN}✓ Docker atualizado com sucesso!${NC}"
        docker --version

    else
        echo -e "${RED}Sistema operacional não suportado: $OS${NC}"
        echo "Por favor, consulte a documentação em: https://docs.docker.com/engine/install/"
        exit 1
    fi
fi

echo ""
read -p "Pressione ENTER para continuar..."
echo ""

# ============================================================================
# PASSO 3: Verificar Rede Docker
# ============================================================================
echo -e "${YELLOW}PASSO 3: Verificar Rede Docker${NC}"
echo "========================================"
echo ""

if docker network inspect intellicare-network &> /dev/null; then
    echo -e "${GREEN}✓ Rede intellicare-network existe${NC}"
else
    echo -e "${YELLOW}⚠ Rede intellicare-network NÃO existe${NC}"
    echo "Criando rede..."
    docker network create intellicare-network --driver bridge
    echo -e "${GREEN}✓ Rede criada${NC}"
fi

echo ""
read -p "Pressione ENTER para continuar..."
echo ""

# ============================================================================
# PASSO 4: Sincronizar Arquivos do Repositório
# ============================================================================
echo -e "${YELLOW}PASSO 4: Sincronizar Arquivos do Repositório${NC}"
echo "========================================"
echo ""

INTELLICARE_PATH="/opt/intellicare/intellicare"

if [ -d "$INTELLICARE_PATH" ]; then
    echo "Diretório encontrado: $INTELLICARE_PATH"
    echo ""
    echo "Atenção: Este script NÃO pode baixar arquivos do Git automaticamente."
    echo "Você precisará copiar os arquivos manualmente:"
    echo ""
    echo "1. No seu computador local:"
    echo "   cd c:\\DOCSHARE\\INTELLICARE"
    echo "   git pull"
    echo ""
    echo "2. Copiar os arquivos atualizados para o servidor:"
    echo "   scp traefik/dynamic/*.yml root@167.86.97.142:/opt/intellicare/intellicare/traefik/dynamic/"
    echo ""
else
    echo -e "${RED}Diretório não encontrado: $INTELLICARE_PATH${NC}"
    echo "Por favor, verifique o caminho do projeto no servidor."
fi

echo ""
read -p "Pressione ENTER para continuar..."
echo ""

# ============================================================================
# PASSO 5: Reiniciar Containers
# ============================================================================
echo -e "${YELLOW}PASSO 5: Reiniciar Containers${NC}"
echo "========================================"
echo ""

read -p "Deseja reiniciar todos os containers? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "$INTELLICARE_PATH" ]; then
        echo "Reiniciando containers..."
        cd "$INTELLICARE_PATH"

        # Parar containers
        echo "Parando containers..."
        docker-compose -f docker-compose.full.yml down 2>/dev/null || \
        docker compose -f docker-compose.full.yml down 2>/dev/null || \
        echo "  Aviso: Não foi possível parar os containers"

        # Iniciar containers
        echo "Iniciando containers..."
        docker-compose -f docker-compose.full.yml up -d 2>/dev/null || \
        docker compose -f docker-compose.full.yml up -d 2>/dev/null || \
        echo "  Aviso: Não foi possível iniciar os containers"

        echo -e "${GREEN}✓ Containers reiniciados${NC}"
    else
        echo -e "${RED}Diretório do projeto não encontrado${NC}"
    fi
else
    echo -e "${YELLOW} Pulando reinício dos containers${NC}"
fi

echo ""
read -p "Pressione ENTER para continuar..."
echo ""

# ============================================================================
# PASSO 6: Verificar Status Final
# ============================================================================
echo -e "${YELLOW}PASSO 6: Verificar Status Final${NC}"
echo "========================================"
echo ""

echo "Aguardando containers iniciarem (10 segundos)..."
sleep 10

echo ""
echo "Status dos Containers:"
echo "======================"
docker ps --filter "name=intellicare" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "Containers com problemas:"
echo "========================"
FAILED_CONTAINERS=$(docker ps --all --filter "name=intellicare" --format "{{.Names}}\t{{.Status}}" | grep -v "Up" || true)
if [ -n "$FAILED_CONTAINERS" ]; then
    echo "$FAILED_CONTAINERS"
    echo ""
    echo "Para investigar:"
    echo "  docker logs <container-name> --tail 50"
else
    echo -e "${GREEN}Nenhum problema detectado!${NC}"
fi

echo ""

# ============================================================================
# PASSO 7: Testar Endpoints
# ============================================================================
echo -e "${YELLOW}PASSO 7: Testar Endpoints${NC}"
echo "========================================"
echo ""

echo "Testando endpoints críticos (aguarde...)"
echo ""

# Testar API Gateway
echo -n "  API Gateway (api.intellicare.ia.br):        "
if curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://api.intellicare.ia.br/v1/oswaldo/api/v1/health 2>/dev/null | grep -q "200\|404\|401"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ FALHOU (pode ser normal se Traefik não está rodando)${NC}"
fi

# Testar Portal
echo -n "  Portal (portal.intellicare.ia.br):           "
if curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://portal.intellicare.ia.br 2>/dev/null | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ FALHOU (pode ser normal se Traefik não está rodando)${NC}"
fi

# Testar Grafana
echo -n "  Grafana (grafana.intellicare.ia.br):         "
if curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://grafana.intellicare.ia.br 2>/dev/null | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ FALHOU (pode ser normal se Traefik não está rodando)${NC}"
fi

echo ""

# ============================================================================
# FINALIZAÇÃO
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Processo Concluído!${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

echo "Resumo:"
echo "======="
if command -v docker &> /dev/null; then
    NEW_DOCKER_VERSION=$(docker --version 2>&1 || echo "ERRO")
    echo "  Docker: $NEW_DOCKER_VERSION"
fi
echo "  Servidor: 167.86.97.142"
echo ""

echo "Próximos passos:"
echo "  1. Se houver containers com problemas, investigue os logs:"
echo "     docker logs <container-name> --tail 50"
echo ""
echo "  2. Sincronize os arquivos do repositório Git:"
echo "     cd c:\\DOCSHARE\\INTELLICARE"
echo "     git pull"
echo "     scp traefik/dynamic/*.yml root@167.86.97.142:/opt/intellicare/intellicare/traefik/dynamic/"
echo ""
echo "  3. Reinicie o Traefik:"
echo "     docker restart intellicare-traefik"
echo ""
echo "  4. Acesse:"
echo "     https://grafana.intellicare.ia.br"
echo "     https://portal.intellicare.ia.br"
echo ""

echo -e "${BLUE}============================================================================${NC}"
