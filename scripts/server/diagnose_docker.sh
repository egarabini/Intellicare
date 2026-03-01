#!/bin/bash
# ============================================================================
# IntelliCare — Docker Diagnostics Quick Check
# ============================================================================
# Script rápido para diagnosticar problemas de versão do Docker
# ============================================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}IntelliCare — Diagnóstico Rápido do Docker${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ============================================================================
# FUNÇÃO PARA VERIFICAR VERSÃO
# ============================================================================
check_version() {
    local name=$1
    local current=$2
    local minimum=$3
    local result=$4

    echo -n "  $name: "

    if [ -z "$current" ]; then
        echo -e "${RED}NÃO INSTALADO${NC}"
        return 1
    fi

    echo -e "${GREEN}${current}${NC}"

    if [ "$result" = "fail" ]; then
        echo -e "    ${RED}✗ Mínimo requerido: $minimum${NC}"
        return 1
    else
        echo -e "    ${GREEN}✓ OK (mínimo: $minimum)${NC}"
        return 0
    fi
}

# ============================================================================
# VERIFICAR DOCKER
# ============================================================================
echo -e "${BLUE}[1/6] Docker Engine${NC}"
echo ""

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    DOCKER_API_VERSION=$(docker version --format '{{.Server.APIVersion}}' 2>/dev/null || echo "unknown")

    # Comparar versão API
    if [ "$DOCKER_API_VERSION" = "unknown" ]; then
        check_version "Docker" "$DOCKER_VERSION (API ???)" "24.0.0+" "fail"
        echo -e "    ${YELLOW}⚠ Não foi possível detectar versão da API${NC}"
    elif [ "${DOCKER_API_VERSION//./}" -lt "143" ]; then
        check_version "Docker" "$DOCKER_VERSION (API $DOCKER_API_VERSION)" "24.0.0+ (API 1.43+)" "fail"
        echo -e "    ${RED}✗ API muito antiga! Atualização necessária.${NC}"
    else
        check_version "Docker" "$DOCKER_VERSION (API $DOCKER_API_VERSION)" "24.0.0+ (API 1.43+)" "pass"
    fi
else
    check_version "Docker" "" "24.0.0+" "fail"
fi

echo ""

# ============================================================================
# VERIFICAR DOCKER COMPOSE
# ============================================================================
echo -e "${BLUE}[2/6] Docker Compose${NC}"
echo ""

if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | sed 's/,//')
    check_version "Docker Compose" "$COMPOSE_VERSION" "2.20.0+" "pass"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version | awk '{print $4}' | sed 's/,//')
    check_version "Docker Compose (plugin)" "$COMPOSE_VERSION" "2.20.0+" "pass"
else
    check_version "Docker Compose" "" "2.20.0+" "fail"
fi

echo ""

# ============================================================================
# VERIFICAR KERNEL
# ============================================================================
echo -e "${BLUE}[3/6] Kernel Linux${NC}"
echo ""

KERNEL_VERSION=$(uname -r | cut -d'-' -f1)
check_version "Kernel" "$KERNEL_VERSION" "4.19+" "pass"

echo ""

# ============================================================================
# VERIFICAR SISTEMA OPERACIONAL
# ============================================================================
echo -e "${BLUE}[4/6] Sistema Operacional${NC}"
echo ""

if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "  ${GREEN}${PRETTY_NAME}${NC}"
    echo "    ID: $ID"
    echo "    Version: $VERSION_ID"

    # Verificar suporte
    case "$ID" in
        ubuntu)
            if [ "${VERSION_ID//./}" -lt "2004" ]; then
                echo -e "    ${YELLOW}⚠ Versão do Ubuntu antiga. Recomendado: 20.04+${NC}"
            fi
            ;;
        debian)
            if [ "${VERSION_ID//./}" -lt "11" ]; then
                echo -e "    ${YELLOW}⚠ Versão do Debian antiga. Recomendado: 11+${NC}"
            fi
            ;;
        centos|rhel|rocky)
            if [ "${VERSION_ID//./}" -lt "80" ]; then
                echo -e "    ${YELLOW}⚠ Versão antiga. Recomendado: Rocky Linux 8+${NC}"
            fi
            ;;
        *)
            echo -e "    ${YELLOW}⚠ Sistema não testado oficialmente${NC}"
            ;;
    esac
else
    echo -e "  ${RED}Não foi possível identificar o sistema operacional${NC}"
fi

echo ""

# ============================================================================
# VERIFICAR STATUS DO SERVIÇO DOCKER
# ============================================================================
echo -e "${BLUE}[5/6] Status do Serviço Docker${NC}"
echo ""

if systemctl is-active --quiet docker; then
    echo -e "  ${GREEN}✓ Serviço Docker está rodando${NC}"
else
    echo -e "  ${RED}✗ Serviço Docker está PARADO${NC}"
    echo "    Para iniciar: sudo systemctl start docker"
fi

if systemctl is-enabled --quiet docker; then
    echo -e "  ${GREEN}✓ Serviço Docker está habilitado para iniciar no boot${NC}"
else
    echo -e "  ${YELLOW}⚠ Serviço Docker não está habilitado no boot${NC}"
    echo "    Para habilitar: sudo systemctl enable docker"
fi

echo ""

# ============================================================================
# VERIFICAR CONTAINERS
# ============================================================================
echo -e "${BLUE}[6/6] Status dos Containers IntelliCare${NC}"
echo ""

CONTAINER_COUNT=$(docker ps --format "{{.Names}}" | grep intellicare | wc -l)
TOTAL_CONTAINERS=$(docker ps --all --format "{{.Names}}" | grep intellicare | wc -l)

echo "  Containers rodando: ${GREEN}${CONTAINER_COUNT}${NC}"
echo "  Containers totais:  ${TOTAL_CONTAINERS}"
echo ""

# Containers com problemas
if [ "$CONTAINER_COUNT" -lt "$TOTAL_CONTAINERS" ]; then
    echo -e "  ${YELLOW}⚠ Containers parados ou com problemas:${NC}"
    docker ps --all --format "{{.Names}}\t{{.Status}}" | grep intellicare | grep -v "Up" | while read line; do
        echo "    - $line"
    done
fi

echo ""

# ============================================================================
# VERIFICAR REDE DOCKER
# ============================================================================
echo -e "${BLUE}[7/6] Rede Docker${NC}"
echo ""

if docker network inspect intellicare-network &> /dev/null; then
    echo -e "  ${GREEN}✓ Rede intellicare-network existe${NC}"
else
    echo -e "  ${RED}✗ Rede intellicare-network NÃO existe${NC}"
    echo "    Para criar: docker network create intellicare-network"
fi

echo ""

# ============================================================================
# DIAGNÓSTICO FINAL
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}Diagnóstico Final${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

NEEDS_UPDATE=false

# Verificar se precisa atualizar
if [ "${DOCKER_API_VERSION//./}" -lt "143" ] 2>/dev/null; then
    NEEDS_UPDATE=true
    echo -e "${RED}✗ PROBLEMA CRÍTICO: Docker API muito antiga${NC}"
    echo "  O servidor precisa ser atualizado."
    echo ""
    echo "  Solução:"
    echo "    1. Execute o script de atualização:"
    echo "       bash scripts/server/UPDATE_DOCKER_SERVER.sh"
    echo "    2. Ou manualmente seguindo:"
    echo "       https://docs.docker.com/engine/install/"
    echo ""
fi

if [ "$CONTAINER_COUNT" -eq 0 ]; then
    NEEDS_UPDATE=true
    echo -e "${YELLOW}⚠ AVISO: Nenhum container IntelliCare está rodando${NC}"
    echo "  Verifique se os containers estão rodando:"
    echo "    docker ps"
    echo ""
    echo "  Para reiniciar:"
    echo "    cd /opt/intellicare/intellicare"
    echo "    docker-compose -f docker-compose.full.yml up -d"
    echo ""
fi

if [ "$NEEDS_UPDATE" = false ]; then
    echo -e "${GREEN}✓ Sistema parece OK!${NC}"
    echo ""
    echo "Versões:"
    echo "  Docker:    $DOCKER_VERSION (API $DOCKER_API_VERSION)"
    echo "  Compose:   $COMPOSE_VERSION"
    echo "  Kernel:    $KERNEL_VERSION"
    echo "  Containers: $CONTAINER_COUNT rodando"
    echo ""
else
    echo -e "${RED}✗ Ações necessárias detectadas${NC}"
    echo ""
fi

echo -e "${BLUE}============================================================================${NC}"
