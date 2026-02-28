#!/bin/bash
# Script de Correção dos Erros Docker no Servidor de Staging
# Data: 2026-02-22
# Baseado em: 20260222-1400_RELATORIO_ANALISE_ERROS_DOCKER_STAGING.md

set -e  # Exit on error

echo "=========================================="
echo "CORREÇÃO DOS ERROS DOCKER - STAGING"
echo "=========================================="
echo ""

# Diretório do projeto
PROJECT_DIR="/opt/intellicare/intellicare"
cd "$PROJECT_DIR"

echo "📍 Diretório atual: $(pwd)"
echo ""

# ============================================
# 1. OSWALDO - Corrigir DATABASE_URL
# ============================================
echo "🔧 [1/3] Corrigindo DATABASE_URL do Oswaldo..."
echo "   Alterando de postgresql+asyncpg:// para postgresql+psycopg://"

# Backup do .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Substituir asyncpg por psycopg em todas as URLs do Oswaldo
sed -i 's|postgresql+asyncpg://|postgresql+psycopg://|g' .env

echo "   ✅ DATABASE_URL atualizada"
echo ""

# ============================================
# 2. REBUILD DAS IMAGENS
# ============================================
echo "🔨 [2/3] Rebuild das imagens Docker (sem cache)..."
echo "   Módulos: oswaldo, donabedian, comunicacao"
echo ""

docker-compose -f docker-compose.full.yml build --no-cache oswaldo donabedian comunicacao

echo "   ✅ Imagens reconstruídas"
echo ""

# ============================================
# 3. RESTART DOS CONTAINERS
# ============================================
echo "🔄 [3/3] Recriando containers..."

docker-compose -f docker-compose.full.yml up -d --force-recreate oswaldo donabedian comunicacao

echo "   ✅ Containers recriados"
echo ""

# ============================================
# 4. AGUARDAR INICIALIZAÇÃO
# ============================================
echo "⏳ Aguardando 30 segundos para inicialização..."
sleep 30
echo ""

# ============================================
# 5. VERIFICAÇÃO
# ============================================
echo "=========================================="
echo "VERIFICAÇÃO DE STATUS"
echo "=========================================="
echo ""

echo "📊 Status dos containers:"
docker-compose -f docker-compose.full.yml ps
echo ""

echo "📋 Logs do Oswaldo (últimas 20 linhas):"
echo "----------------------------------------"
docker logs intellicare-oswaldo --tail 20
echo ""

echo "📋 Logs do Donabedian (últimas 20 linhas):"
echo "----------------------------------------"
docker logs intellicare-donabedian --tail 20
echo ""

echo "📋 Logs do Comunicacao (últimas 20 linhas):"
echo "----------------------------------------"
docker logs intellicare-comunicacao --tail 20
echo ""

echo "=========================================="
echo "✅ CORREÇÃO CONCLUÍDA"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Verificar se os containers estão 'Up (healthy)'"
echo "2. Testar endpoints de health de cada módulo"
echo "3. Se houver erros, verificar logs completos com:"
echo "   docker logs intellicare-<modulo>"
echo ""

