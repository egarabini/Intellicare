#!/bin/bash
# ============================================================================
# IntelliCare — Docker Server Update Guide
# ============================================================================
# Script para atualizar Docker e Docker Compose no servidor de produção
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}IntelliCare — Atualização do Docker no Servidor${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

# ============================================================================
# VERSÕES MÍNIMAS REQUERIDAS
# ============================================================================
echo -e "${YELLOW}Versões mínimas requeridas:${NC}"
echo "  Docker Engine:     24.0.0+ (API 1.43+)"
echo "  Docker Compose:   2.20.0+"
echo "  Linux Kernel:     4.19+"
echo ""

# ============================================================================
# VERIFICAR VERSÃO ATUAL
# ============================================================================
echo -e "${YELLOW}Verificando versão atual...${NC}"
echo ""

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    DOCKER_API_VERSION=$(docker version --format '{{.Server.APIVersion}}' 2>/dev/null || echo "unknown")
    echo -e "Docker atual:     ${GREEN}${DOCKER_VERSION}${NC} (API ${DOCKER_API_VERSION})"
else
    echo -e "Docker atual:     ${RED}Não instalado${NC}"
fi

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
    echo -e "Docker Compose:  ${GREEN}${COMPOSE_VERSION}${NC}"
else
    echo -e "Docker Compose:  ${RED}Não instalado${NC}"
fi

KERNEL_VERSION=$(uname -r | cut -d'-' -f1)
echo -e "Kernel Linux:     ${GREEN}${KERNEL_VERSION}${NC}"
echo ""

# ============================================================================
# VERIFICAR SISTEMA OPERACIONAL
# ============================================================================
echo -e "${YELLOW}Verificando sistema operacional...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_VERSION=$VERSION_ID
    echo -e "Sistema:          ${GREEN}${NAME} ${VERSION_ID}${NC}"
    echo ""
fi

# ============================================================================
# BACKUP DE CONFIGURAÇÕES
# ============================================================================
echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}PASSO 1: Backup de Configurações${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo ""

BACKUP_DIR="/opt/intellicare/backups/docker-update-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Criando backup em: $BACKUP_DIR"
echo ""

# Backup das configurações do Docker
if [ -d /etc/docker ]; then
    echo -e "${GREEN}✓${NC} Backup de /etc/docker"
    cp -r /etc/docker "$BACKUP_DIR/" 2>/dev/null || true
fi

# Backup dos containers docker-compose.yml
if [ -d /opt/intellicare ]; then
    echo -e "${GREEN}✓${NC} Backup de docker-compose.yml"
    find /opt/intellicare -name "docker-compose*.yml" -exec cp --parents {} "$BACKUP_DIR/" \; 2>/dev/null || true
fi

# Backup das configurações do Traefik
if [ -d /opt/intellicare/traefik ]; then
    echo -e "${GREEN}✓${NC} Backup de configurações do Traefik"
    cp -r /opt/intellicare/traefik "$BACKUP_DIR/" 2>/dev/null || true
fi

# Lista de containers ativos
echo -e "${GREEN}✓${NC} Salvando lista de containers ativos"
docker ps --format "{{.Names}}" > "$BACKUP_DIR/running-containers.txt" 2>/dev/null || true

echo ""
echo -e "${GREEN}Backup concluído em: $BACKUP_DIR${NC}"
echo ""

# ============================================================================
# PARAR CONTAINERS (OPCIONAL)
# ============================================================================
echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}PASSO 2: Parar Containers (Opcional)${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo ""

read -p "Deseja parar todos os containers antes da atualização? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Parando containers..."
    cd /opt/intellicare/intellicare
    docker-compose -f docker-compose.full.yml down 2>/dev/null || true
    echo -e "${GREEN}✓${NC} Containers parados"
else
    echo -e "${YELLOW}⚠${NC}  Containers continuarão rodando (recomendado: atualização sem downtime)"
fi
echo ""

# ============================================================================
# ATUALIZAR DOCKER (DEBIAN/UBUNTU)
# ============================================================================
if [ "$OS" = "debian" ] || [ "$OS" = "ubuntu" ]; then
    echo -e "${YELLOW}============================================================================${NC}"
    echo -e "${YELLOW}PASSO 3: Atualizar Docker (${OS^})${NC}"
    echo -e "${YELLOW}============================================================================${NC}"
    echo ""

    echo -e "${YELLOW}a) Remover versão antiga do Docker${NC}"
    echo "sudo apt-get remove docker docker-engine docker.io containerd runc"
    echo ""

    echo -e "${YELLOW}b) Atualizar repositório e instalar dependências${NC}"
    echo "sudo apt-get update"
    echo "sudo apt-get install -y \\"
    echo "    ca-certificates \\"
    echo "    curl \\"
    echo "    gnupg \\"
    echo "    lsb-release"
    echo ""

    echo -e "${YELLOW}c) Adicionar chave GPG oficial do Docker${NC}"
    echo "sudo mkdir -p /etc/apt/keyrings"
    echo "curl -fsSL https://download.docker.com/linux/${OS}/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg"
    echo ""

    echo -e "${YELLOW}d) Configurar repositório${NC}"
    echo "echo \\"
    echo "  \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${OS} \\"
    echo "  $(lsb_release -cs) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null"
    echo ""

    echo -e "${YELLOW}e) Instalar Docker Engine${NC}"
    echo "sudo apt-get update"
    echo "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
    echo ""

    echo -e "${YELLOW}f) Habilitar e iniciar Docker${NC}"
    echo "sudo systemctl enable docker"
    echo "sudo systemctl start docker"
    echo ""

    echo -e "${GREEN}Comandos prontos para executar. Pressione ENTER para continuar ou Ctrl+C para cancelar${NC}"
    read

    # Executar atualização
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/${OS}/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${OS} \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl enable docker
    sudo systemctl start docker

# ============================================================================
# ATUALIZAR DOCKER (CENTOS/RHEL)
# ============================================================================
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "rocky" ]; then
    echo -e "${YELLOW}============================================================================${NC}"
    echo -e "${YELLOW}PASSO 3: Atualizar Docker (${OS^})${NC}"
    echo -e "${YELLOW}============================================================================${NC}"
    echo ""

    echo -e "${YELLOW}a) Remover versão antiga do Docker${NC}"
    echo "sudo yum remove docker docker-client docker-client-latest docker-common \\"
    echo "    docker-latest docker-latest-logrotate docker-logrotate docker-engine"
    echo ""

    echo -e "${YELLOW}b) Instalar dependências${NC}"
    echo "sudo yum install -y yum-utils"
    echo ""

    echo -e "${YELLOW}c) Adicionar repositório do Docker${NC}"
    echo "sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo"
    echo ""

    echo -e "${YELLOW}d) Instalar Docker Engine${NC}"
    echo "sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
    echo ""

    echo -e "${YELLOW}e) Habilitar e iniciar Docker${NC}"
    echo "sudo systemctl enable docker"
    echo "sudo systemctl start docker"
    echo ""

    echo -e "${GREEN}Comandos prontos para executar. Pressione ENTER para continuar ou Ctrl+C para cancelar${NC}"
    read

    # Executar atualização
    sudo yum remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine 2>/dev/null || true
    sudo yum install -y yum-utils
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo systemctl enable docker
    sudo systemctl start docker

else
    echo -e "${RED}Sistema operacional não suportado automaticamente: $OS${NC}"
    echo "Por favor, consulte a documentação oficial do Docker:"
    echo "https://docs.docker.com/engine/install/"
    exit 1
fi

echo ""
echo -e "${GREEN}✓${NC} Docker atualizado com sucesso!"
echo ""

# ============================================================================
# VERIFICAR NOVA VERSÃO
# ============================================================================
echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}PASSO 4: Verificar Nova Versão${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo ""

NEW_DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
NEW_DOCKER_API_VERSION=$(docker version --format '{{.Server.APIVersion}}')

echo -e "Docker atualizado: ${GREEN}${NEW_DOCKER_VERSION}${NC} (API ${NEW_DOCKER_API_VERSION})"
echo ""

# ============================================================================
# REINICIAR CONTAINERS
# ============================================================================
echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}PASSO 5: Reiniciar Containers${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo ""

if [ -d /opt/intellicare/intellicare ]; then
    echo "Iniciando containers IntelliCare..."
    cd /opt/intellicare/intellicare
    docker-compose -f docker-compose.full.yml up -d
    echo -e "${GREEN}✓${NC} Containers reiniciados"
else
    echo -e "${YELLOW}⚠${NC}  Diretório /opt/intellicare/intellicare não encontrado"
    echo "Por favor, reinicie os containers manualmente"
fi

echo ""

# ============================================================================
# VERIFICAR SAÚDE DOS CONTAINERS
# ============================================================================
echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}PASSO 6: Verificar Saúde dos Containers${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo ""

sleep 10  # Aguardar containers iniciarem

echo "Status dos containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Verificar containers com problemas
FAILED_CONTAINERS=$(docker ps --all --format "{{.Names}}\t{{.Status}}" | grep -E "Exited|Created" || true)
if [ -n "$FAILED_CONTAINERS" ]; then
    echo -e "${RED}⚠${NC}  Containers com problemas detectados:"
    echo "$FAILED_CONTAINERS"
    echo ""
    echo "Para investigar:"
    echo "  docker logs <container-name> --tail 50"
else
    echo -e "${GREEN}✓${NC} Todos os containers estão rodando!"
fi

echo ""

# ============================================================================
# TESTAR FUNCIONALIDADE
# ============================================================================
echo -e "${YELLOW}============================================================================${NC}"
echo -e "${YELLOW}PASSO 7: Testar Funcionalidade${NC}"
echo -e "${YELLOW}============================================================================${NC}"
echo ""

echo "Testando endpoints críticos:"
echo ""

# Testar API Gateway
echo -n "  API Gateway (api.intellicare.ia.br):        "
if curl -s -o /dev/null -w "%{http_code}" https://api.intellicare.ia.br/v1/oswaldo/api/v1/health | grep -q "200\|404\|401"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ Falha (pode ser normal se Traefik não está rodando)${NC}"
fi

# Testar Portal
echo -n "  Portal (portal.intellicare.ia.br):           "
if curl -s -o /dev/null -w "%{http_code}" https://portal.intellicare.ia.br | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ Falha (pode ser normal se Traefik não está rodando)${NC}"
fi

# Testar Grafana
echo -n "  Grafana (grafana.intellicare.ia.br):         "
if curl -s -o /dev/null -w "%{http_code}" https://grafana.intellicare.ia.br | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ Falha (pode ser normal se Traefik não está rodando)${NC}"
fi

echo ""

# ============================================================================
# FINALIZAÇÃO
# ============================================================================
echo -e "${GREEN}============================================================================${NC}"
echo -e "${GREEN}Atualização Concluída!${NC}"
echo -e "${GREEN}============================================================================${NC}"
echo ""

echo "Resumo:"
echo "  Backup salvo em: $BACKUP_DIR"
echo "  Docker: $NEW_DOCKER_VERSION (API $NEW_DOCKER_API_VERSION)"
echo ""

echo "Próximos passos:"
echo "  1. Verificar logs dos containers: docker logs <container> --tail 50"
echo "  2. Acessar: https://grafana.intellicare.ia.br"
echo "  3. Acessar: https://portal.intellicare.ia.br"
echo ""

echo -e "${YELLOW}⚠${NC}  Se algum container não iniciar, verifique os logs e:"
echo "     - Compare com a configuração no backup: $BACKUP_DIR"
echo "     - Consulte documentação em: docs/INFRAESTRUTURA/"
echo ""

echo -e "${GREEN}============================================================================${NC}"
