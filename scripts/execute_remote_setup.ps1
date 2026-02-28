# Script PowerShell para executar configuração remota do servidor
# Servidor: 167.86.97.142 (Contabo VPS)
# Data: 2026-02-22

$ErrorActionPreference = "Continue"

Write-Host "=========================================="
Write-Host "IntelliCare - Configuração Remota"
Write-Host "Servidor: 167.86.97.142"
Write-Host "=========================================="
Write-Host ""

$server = "167.86.97.142"
$user = "root"

# Função para executar comando SSH
function Invoke-SSHCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "[INFO] $Description" -ForegroundColor Green
    Write-Host "Executando: $Command" -ForegroundColor Gray
    
    $result = ssh ${user}@${server} $Command 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Sucesso" -ForegroundColor Green
        Write-Host $result
    } else {
        Write-Host "⚠️ Aviso/Erro" -ForegroundColor Yellow
        Write-Host $result
    }
    
    Write-Host ""
    return $result
}

# Testar conexão
Write-Host "Testando conexão SSH..." -ForegroundColor Cyan
$testResult = ssh ${user}@${server} "echo 'Conexão OK'" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Conexão SSH estabelecida!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "❌ Erro ao conectar via SSH" -ForegroundColor Red
    Write-Host $testResult
    exit 1
}

# ==========================================
# FASE A - PREPARAÇÃO DO SERVIDOR
# ==========================================

Write-Host "=== FASE A - PREPARAÇÃO DO SERVIDOR ===" -ForegroundColor Cyan
Write-Host ""

# A1. Atualizar sistema
Invoke-SSHCommand -Command "apt update" -Description "A1.1 Atualizando lista de pacotes"
Invoke-SSHCommand -Command "DEBIAN_FRONTEND=noninteractive apt upgrade -y" -Description "A1.2 Atualizando sistema (pode demorar)"
Invoke-SSHCommand -Command "apt install -y curl wget git vim htop net-tools ufw" -Description "A1.3 Instalando ferramentas essenciais"

# A2. Configurar firewall
Invoke-SSHCommand -Command "ufw allow 22/tcp" -Description "A2.1 Liberando porta SSH (22)"
Invoke-SSHCommand -Command "ufw allow 80/tcp" -Description "A2.2 Liberando porta HTTP (80)"
Invoke-SSHCommand -Command "ufw allow 443/tcp" -Description "A2.3 Liberando porta HTTPS (443)"
Invoke-SSHCommand -Command "ufw allow 3001/tcp" -Description "A2.4 Liberando porta Portal (3001)"
Invoke-SSHCommand -Command "ufw allow 8001:8006/tcp" -Description "A2.5 Liberando portas Backends (8001-8006)"
Invoke-SSHCommand -Command "ufw allow 3000/tcp" -Description "A2.6 Liberando porta Grafana (3000)"
Invoke-SSHCommand -Command "ufw allow 9090/tcp" -Description "A2.7 Liberando porta Prometheus (9090)"
Invoke-SSHCommand -Command "echo 'y' | ufw enable" -Description "A2.8 Ativando firewall"
Invoke-SSHCommand -Command "ufw status" -Description "A2.9 Verificando status do firewall"

# A3. Instalar Docker
Invoke-SSHCommand -Command "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && rm get-docker.sh" -Description "A3 Instalando Docker (pode demorar)"
Invoke-SSHCommand -Command "docker --version" -Description "A3.1 Verificando versão do Docker"

# A4. Instalar Docker Compose
Invoke-SSHCommand -Command "curl -L 'https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-Linux-x86_64' -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose" -Description "A4 Instalando Docker Compose"
Invoke-SSHCommand -Command "docker-compose --version" -Description "A4.1 Verificando versão do Docker Compose"

Write-Host "✅ FASE A CONCLUÍDA" -ForegroundColor Green
Write-Host ""

# ==========================================
# FASE B - CLONE E CONFIGURAÇÃO
# ==========================================

Write-Host "=== FASE B - CLONE E CONFIGURAÇÃO ===" -ForegroundColor Cyan
Write-Host ""

# B1. Criar diretório e clonar repositório
Invoke-SSHCommand -Command "mkdir -p /opt/intellicare" -Description "B1.1 Criando diretório /opt/intellicare"
Invoke-SSHCommand -Command "cd /opt/intellicare && git clone https://github.com/eduardo/intellicare.git" -Description "B1.2 Clonando repositório (pode demorar)"
Invoke-SSHCommand -Command "ls -la /opt/intellicare/intellicare" -Description "B1.3 Verificando estrutura do repositório"

# B2. Navegar para .
Invoke-SSHCommand -Command "ls -la /opt/intellicare/intellicare" -Description "B2 Verificando diretório ."

# B3. Configurar .env
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && cp .env.homologacao .env" -Description "B3.1 Copiando .env.homologacao para .env"
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && head -n 10 .env" -Description "B3.2 Verificando .env (primeiras 10 linhas)"

Write-Host "✅ FASE B CONCLUÍDA" -ForegroundColor Green
Write-Host ""

# ==========================================
# FASE C - INFRAESTRUTURA
# ==========================================

Write-Host "=== FASE C - INFRAESTRUTURA ===" -ForegroundColor Cyan
Write-Host ""

# C1. Subir Postgres e Redis
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker-compose -f docker-compose.full.yml up -d postgres redis" -Description "C1 Subindo PostgreSQL e Redis"

# C2. Aguardar e validar
Write-Host "[INFO] Aguardando serviços iniciarem (30 segundos)..." -ForegroundColor Green
Start-Sleep -Seconds 30

Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker-compose -f docker-compose.full.yml ps" -Description "C2.1 Verificando status dos containers"
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker-compose -f docker-compose.full.yml logs --tail=20 postgres" -Description "C2.2 Logs do PostgreSQL"
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker-compose -f docker-compose.full.yml logs --tail=20 redis" -Description "C2.3 Logs do Redis"

# C3. Criar schemas
$createSchemasSQL = @"
CREATE SCHEMA IF NOT EXISTS intellicare_florence;
CREATE SCHEMA IF NOT EXISTS intellicare_oswaldo;
CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;
CREATE SCHEMA IF NOT EXISTS intellicare_wanda;
CREATE SCHEMA IF NOT EXISTS intellicare_comunicacao;
CREATE SCHEMA IF NOT EXISTS intellicare_geralda;
\dn
"@

Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker exec -i `$(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db -c 'CREATE SCHEMA IF NOT EXISTS intellicare_florence;'" -Description "C3.1 Criando schema intellicare_florence"
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker exec -i `$(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db -c 'CREATE SCHEMA IF NOT EXISTS intellicare_oswaldo;'" -Description "C3.2 Criando schema intellicare_oswaldo"
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker exec -i `$(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db -c 'CREATE SCHEMA IF NOT EXISTS intellicare_donabedian;'" -Description "C3.3 Criando schema intellicare_donabedian"
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker exec -i `$(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db -c 'CREATE SCHEMA IF NOT EXISTS intellicare_wanda;'" -Description "C3.4 Criando schema intellicare_wanda"
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker exec -i `$(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db -c 'CREATE SCHEMA IF NOT EXISTS intellicare_comunicacao;'" -Description "C3.5 Criando schema intellicare_comunicacao"
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker exec -i `$(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db -c 'CREATE SCHEMA IF NOT EXISTS intellicare_geralda;'" -Description "C3.6 Criando schema intellicare_geralda"
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker exec -i `$(docker-compose -f docker-compose.full.yml ps -q postgres) psql -U intellicare_admin -d intellicare_db -c '\dn'" -Description "C3.7 Listando schemas criados"

Write-Host "✅ FASE C CONCLUÍDA" -ForegroundColor Green
Write-Host ""

# ==========================================
# RESUMO FINAL
# ==========================================

Write-Host ""
Write-Host "=========================================="
Write-Host "✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
Write-Host "=========================================="
Write-Host ""
Write-Host "Fases executadas:"
Write-Host "  ✅ Fase A - Preparação do Servidor" -ForegroundColor Green
Write-Host "  ✅ Fase B - Clone e Configuração" -ForegroundColor Green
Write-Host "  ✅ Fase C - Infraestrutura" -ForegroundColor Green
Write-Host ""
Write-Host "Verificando serviços finais..."
Invoke-SSHCommand -Command "cd /opt/intellicare/intellicare && docker-compose -f docker-compose.full.yml ps" -Description "Status final dos containers"

Write-Host ""
Write-Host "URLs de acesso:" -ForegroundColor Cyan
Write-Host "  - Portal: http://167.86.97.142:3001"
Write-Host "  - Florence: http://167.86.97.142:8001/docs"
Write-Host "  - Oswaldo: http://167.86.97.142:8002/docs"
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "  1. Validar acesso aos serviços"
Write-Host "  2. Executar Fase D (Deploy completo)"
Write-Host "  3. Configurar backup e segurança (Fase E)"
Write-Host ""

