#!/bin/bash
# Script de Configuração do Servidor de Homologação
# Execute DIRETAMENTE no servidor após conectar via SSH
# ssh root@167.86.97.142
# Senha: Soeuso419863

set -e  # Exit on error

echo "=========================================="
echo "IntelliCare - Setup Servidor Homologação"
echo "Servidor: $(hostname -I | awk '{print $1}')"
echo "Data: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# ==========================================
# FASE A - PREPARAÇÃO DO SERVIDOR
# ==========================================

echo "=== FASE A - PREPARAÇÃO DO SERVIDOR ==="
echo ""

# A1. Atualizar sistema
echo "[A1] Atualizando sistema operacional..."
apt update
DEBIAN_FRONTEND=noninteractive apt upgrade -y
apt install -y curl wget git vim htop net-tools ufw
echo "✅ Sistema atualizado"
echo ""

# A2. Configurar firewall
echo "[A2] Configurando firewall (UFW)..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3001/tcp
ufw allow 8001:8006/tcp
ufw allow 3000/tcp
ufw allow 9090/tcp
echo "y" | ufw enable
echo "✅ Firewall configurado"
ufw status
echo ""

# A3. Instalar Docker
echo "[A3] Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker instalado"
else
    echo "⚠️ Docker já instalado"
fi
docker --version
echo ""

# A4. Instalar Docker Compose
echo "[A4] Instalando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose instalado"
else
    echo "⚠️ Docker Compose já instalado"
fi
docker-compose --version
echo ""

echo "✅ FASE A CONCLUÍDA"
echo ""

# ==========================================
# FASE B - CLONE E CONFIGURAÇÃO
# ==========================================

echo "=== FASE B - CLONE E CONFIGURAÇÃO ==="
echo ""

# B1. Criar diretório e clonar repositório
echo "[B1] Clonando repositório..."
mkdir -p /opt/intellicare
cd /opt/intellicare

if [ -d "intellicare" ]; then
    echo "⚠️ Repositório já existe. Atualizando..."
    cd intellicare
    git pull
else
    git clone https://github.com/eduardo/intellicare.git
    echo "✅ Repositório clonado"
fi

cd /opt/intellicare/intellicare
echo "Estrutura do repositório:"
ls -la
echo ""

# B2. Navegar para .
echo "[B2] Navegando para ...."
if [ -d "." ]; then
    cd .
    echo "✅ Diretório . encontrado"
else
    echo "❌ Diretório . não encontrado!"
    exit 1
fi

pwd
ls -la
echo ""

# B3. Configurar .env
echo "[B3] Configurando .env..."
if [ -f ".env.homologacao" ]; then
    cp .env.homologacao .env
    echo "✅ .env configurado (copiado de .env.homologacao)"
else
    echo "❌ Arquivo .env.homologacao não encontrado!"
    exit 1
fi

echo "Verificando .env (primeiras 10 linhas):"
head -n 10 .env
echo ""

echo "✅ FASE B CONCLUÍDA"
echo ""

# ==========================================
# FASE C - INFRAESTRUTURA
# ==========================================

echo "=== FASE C - INFRAESTRUTURA ==="
echo ""

# C1. Subir Postgres e Redis
echo "[C1] Subindo PostgreSQL e Redis..."
docker-compose -f docker-compose.full.yml up -d postgres redis

echo "Aguardando serviços iniciarem (30s)..."
sleep 30

echo "✅ Containers iniciados"
echo ""

# C2. Validar containers
echo "[C2] Validando containers..."
docker-compose -f docker-compose.full.yml ps

echo ""
echo "Logs do PostgreSQL (últimas 20 linhas):"
docker-compose -f docker-compose.full.yml logs --tail=20 postgres

echo ""
echo "Logs do Redis (últimas 20 linhas):"
docker-compose -f docker-compose.full.yml logs --tail=20 redis
echo ""

# C3. Criar schemas
echo "[C3] Criando schemas no PostgreSQL..."
docker exec -i $(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db <<EOF
CREATE SCHEMA IF NOT EXISTS intellicare_florence;
CREATE SCHEMA IF NOT EXISTS intellicare_oswaldo;
CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;
CREATE SCHEMA IF NOT EXISTS intellicare_wanda;
CREATE SCHEMA IF NOT EXISTS intellicare_comunicacao;
CREATE SCHEMA IF NOT EXISTS intellicare_geralda;
\dn
EOF

echo "✅ Schemas criados"
echo ""

echo "✅ FASE C CONCLUÍDA"
echo ""

# ==========================================
# RESUMO FINAL
# ==========================================

echo ""
echo "=========================================="
echo "✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================="
echo ""
echo "Fases executadas:"
echo "  ✅ Fase A - Preparação do Servidor"
echo "  ✅ Fase B - Clone e Configuração"
echo "  ✅ Fase C - Infraestrutura"
echo ""
echo "Serviços rodando:"
docker-compose -f docker-compose.full.yml ps
echo ""
echo "Próximos passos:"
echo "  1. Validar acesso aos serviços"
echo "  2. Executar Fase D (Deploy completo)"
echo "  3. Configurar backup e segurança (Fase E)"
echo ""
echo "URLs de acesso:"
echo "  - Portal: http://167.86.97.142:3001"
echo "  - Florence: http://167.86.97.142:8001/docs"
echo "  - Oswaldo: http://167.86.97.142:8002/docs"
echo ""
echo "Script concluído em: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

