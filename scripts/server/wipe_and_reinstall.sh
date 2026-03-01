#!/bin/bash
#
# IntelliCare - WIPE and Reinstall Script
# =======================================
# ATENÇÃO: Este script REMOVE TUDO do servidor e reinstala do zero
# Use apenas em servidores de staging/homologação dedicados
#
# O que será removido:
# - Todos os containers Docker (não apenas intellicare)
# - Todas as imagens Docker
# - Todos os volumes Docker
# - Todas as redes Docker
# - O diretório /opt/intellicare completo
#
# Uso: bash scripts/server/wipe_and_reinstall.sh
#

set -e

echo "============================================================================"
echo "⚠️  WIPE COMPLETE - REINSTALAÇÃO DO ZERO"
echo "============================================================================"
echo ""
echo "Este script vai:"
echo "  1. Parar e remover TODOS os containers Docker"
echo "  2. Remover TODAS as imagens Docker"
echo "  3. Remover TODOS os volumes Docker"
echo "  4. Remover TODAS as redes Docker"
echo "  5. Deletar /opt/intellicare"
echo "  6. Clonar novamente do Git"
echo "  7. Reinstalar do zero"
echo ""
echo "⚠️  TEM CERTEZA? Pressione CTRL+C para cancelar"
echo ""
read -p "Pressione ENTER para continuar ou CTRL+C para cancelar..."
echo ""

TARGET_DIR="/opt/intellicare"
GIT_REPO="https://github.com/egarabini/Intellicare.git"
BRANCH="staging"

# ========================================================================
# Step 1: Stop ALL containers
# ========================================================================
echo "Step 1: Parando TODOS os containers Docker..."
echo "============================================================================"

docker stop $(docker ps -aq) 2>/dev/null || true
echo "✓ Todos os containers parados"
echo ""

# ========================================================================
# Step 2: Remove ALL containers
# ========================================================================
echo "Step 2: Removendo TODOS os containers..."
echo "============================================================================"

docker rm -f $(docker ps -aq) 2>/dev/null || true
echo "✓ Todos os containers removidos"
echo ""

# ========================================================================
# Step 3: Remove ALL images
# ========================================================================
echo "Step 3: Removendo TODAS as imagens..."
echo "============================================================================"

docker rmi -f $(docker images -q) 2>/dev/null || true
echo "✓ Todas as imagens removidas"
echo ""

# ========================================================================
# Step 4: Remove ALL volumes
# ========================================================================
echo "Step 4: Removendo TODOS os volumes..."
echo "============================================================================"

docker volume rm $(docker volume ls -q) 2>/dev/null || true
echo "✓ Todos os volumes removidos"
echo ""

# ========================================================================
# Step 5: Remove ALL networks
# ========================================================================
echo "Step 5: Removendo TODAS as redes..."
echo "============================================================================"

docker network ls -q | xargs -r docker network rm 2>/dev/null || true
echo "✓ Todas as redes removidas"
echo ""

# ========================================================================
# Step 6: Prune Docker system
# ========================================================================
echo "Step 6: Limpando sistema Docker..."
echo "============================================================================"

docker system prune -a -f --volumes
echo "✓ Sistema Docker limpo"
echo ""

# ========================================================================
# Step 7: Remove /opt/intellicare directory
# ========================================================================
echo "Step 7: Removendo diretório /opt/intellicare..."
echo "============================================================================"

if [ -d "$TARGET_DIR" ]; then
    rm -rf "$TARGET_DIR"
    echo "✓ Diretório removido"
else
    echo "✓ Diretório não existia"
fi

echo ""

# ========================================================================
# Step 8: Clone from Git
# ========================================================================
echo "Step 8: Clonando do Git..."
echo "============================================================================"

mkdir -p /opt
cd /opt
git clone --branch "$BRANCH" --single-branch "$GIT_REPO" intellicare
cd intellicare
echo "✓ Repositório clonado"
echo ""

# ========================================================================
# Step 9: Setup environment
# ========================================================================
echo "Step 9: Configurando ambiente..."
echo "============================================================================"

bash scripts/server/setup_env.sh
echo "✓ Ambiente configurado"
echo ""

# ========================================================================
# Step 10: Build and start
# ========================================================================
echo "Step 10: Build e start dos containers..."
echo "============================================================================"
echo "Isso pode levar vários minutos..."
echo ""

docker-compose -f docker-compose.full.yml build
docker-compose -f docker-compose.full.yml up -d

echo ""
echo "✓ Containers iniciados"
echo ""

# Wait for containers to initialize
echo "Aguardando inicialização dos containers..."
sleep 15

# ========================================================================
# Step 11: Show status
# ========================================================================
echo "Step 11: Status final..."
echo "============================================================================"
echo ""

docker ps

echo ""
echo "============================================================================"
echo "✅ REINSTALAÇÃO COMPLETA!"
echo "============================================================================"
echo ""

# Count containers
RUNNING=$(docker ps --format "{{.Names}}" | grep -c "intellicare" || true)
TOTAL=$(docker-compose -f docker-compose.full.yml ps -q 2>/dev/null | wc -l)

echo "Containers: $RUNNING rodando (esperado: ~$TOTAL)"
echo ""

# Check for restarting
RESTARTING=$(docker ps -a --format "{{.Names}}\t{{.Status}}" | grep "Restarting" | grep "intellicare" || true)
if [ -n "$RESTARTING" ]; then
    echo "⚠️  WARNING: Containers reiniciando:"
    echo "$RESTARTING"
    echo ""
    echo "Verifique os logs:"
    echo "  docker logs <container-name>"
else
    echo "✓ Todos os containers saudáveis!"
fi

echo ""
echo "============================================================================"
echo "Servidor staging pronto!"
echo "============================================================================"
echo ""
echo "Próximos passos:"
echo "  - Testar health checks: bash scripts/smoke_test.sh"
echo "  - Ver logs: docker-compose -f docker-compose.full.yml logs -f"
echo ""
