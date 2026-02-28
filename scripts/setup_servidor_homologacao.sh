#!/bin/bash
# Script de Configuração do Servidor de Homologação
# Servidor: 167.86.97.142 (Contabo VPS)
# Data: 2026-02-22
# Fases: A, B, C (Preparação, Clone, Infraestrutura)

set -e  # Exit on error

echo "=========================================="
echo "IntelliCare - Setup Servidor Homologação"
echo "=========================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para log
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==========================================
# FASE A - PREPARAÇÃO DO SERVIDOR
# ==========================================

log_info "=== FASE A - PREPARAÇÃO DO SERVIDOR ==="
echo ""

# A1. Atualizar sistema
log_info "A1. Atualizando sistema operacional..."
apt update
apt upgrade -y
apt install -y curl wget git vim htop net-tools ufw

log_info "✅ Sistema atualizado"
echo ""

# A2. Configurar firewall
log_info "A2. Configurando firewall (UFW)..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 3001/tcp  # Portal
ufw allow 8001:8006/tcp  # Backends
ufw allow 3000/tcp  # Grafana
ufw allow 9090/tcp  # Prometheus
ufw --force enable

log_info "✅ Firewall configurado"
ufw status
echo ""

# A3. Instalar Docker
log_info "A3. Instalando Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    log_info "✅ Docker instalado"
else
    log_warn "Docker já instalado"
fi
docker --version
echo ""

# A4. Instalar Docker Compose
log_info "A4. Instalando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    log_info "✅ Docker Compose instalado"
else
    log_warn "Docker Compose já instalado"
fi
docker-compose --version
echo ""

log_info "✅ FASE A CONCLUÍDA"
echo ""

# ==========================================
# FASE B - CLONE E CONFIGURAÇÃO
# ==========================================

log_info "=== FASE B - CLONE E CONFIGURAÇÃO ==="
echo ""

# B1. Criar diretório e clonar repositório
log_info "B1. Clonando repositório..."
mkdir -p /opt/intellicare
cd /opt/intellicare

if [ -d "intellicare" ]; then
    log_warn "Repositório já existe. Atualizando..."
    cd intellicare
    git pull
else
    git clone https://github.com/eduardo/intellicare.git
    log_info "✅ Repositório clonado"
fi

cd /opt/intellicare/intellicare
log_info "Estrutura do repositório:"
ls -la
echo ""

# B2. Navegar para .
log_info "B2. Navegando para ...."
if [ -d "." ]; then
    cd .
    log_info "✅ Diretório . encontrado"
else
    log_error "Diretório . não encontrado!"
    exit 1
fi

pwd
ls -la
echo ""

# B3. Configurar .env
log_info "B3. Configurando .env..."
if [ -f ".env.homologacao" ]; then
    cp .env.homologacao .env
    log_info "✅ .env configurado (copiado de .env.homologacao)"
else
    log_error "Arquivo .env.homologacao não encontrado!"
    exit 1
fi

log_info "Verificando .env:"
head -n 10 .env
echo ""

log_info "✅ FASE B CONCLUÍDA"
echo ""

# ==========================================
# FASE C - INFRAESTRUTURA
# ==========================================

log_info "=== FASE C - INFRAESTRUTURA ==="
echo ""

# C1. Subir Postgres e Redis
log_info "C1. Subindo PostgreSQL e Redis..."
docker-compose -f docker-compose.full.yml up -d postgres redis

log_info "Aguardando serviços iniciarem (30s)..."
sleep 30

log_info "✅ Containers iniciados"
echo ""

# C2. Validar containers
log_info "C2. Validando containers..."
docker-compose -f docker-compose.full.yml ps

echo ""
log_info "Logs do PostgreSQL:"
docker-compose -f docker-compose.full.yml logs --tail=20 postgres

echo ""
log_info "Logs do Redis:"
docker-compose -f docker-compose.full.yml logs --tail=20 redis
echo ""

# C3. Criar schemas
log_info "C3. Criando schemas no PostgreSQL..."
docker exec -i $(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db <<EOF
CREATE SCHEMA IF NOT EXISTS intellicare_florence;
CREATE SCHEMA IF NOT EXISTS intellicare_oswaldo;
CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;
CREATE SCHEMA IF NOT EXISTS intellicare_wanda;
CREATE SCHEMA IF NOT EXISTS intellicare_comunicacao;
CREATE SCHEMA IF NOT EXISTS intellicare_geralda;
\dn
EOF

log_info "✅ Schemas criados"
echo ""

log_info "✅ FASE C CONCLUÍDA"
echo ""

# ==========================================
# RESUMO FINAL
# ==========================================

echo ""
echo "=========================================="
log_info "✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!"
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
echo "  2. Executar Fase D (Deploy completo) quando estabilização concluída"
echo "  3. Configurar backup e segurança (Fase E)"
echo ""
echo "URLs de acesso:"
echo "  - Portal: http://167.86.97.142:3001"
echo "  - Florence: http://167.86.97.142:8001/docs"
echo "  - Oswaldo: http://167.86.97.142:8002/docs"
echo ""

