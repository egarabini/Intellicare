# ═══════════════════════════════════════════════════════════════════════════
# Script para executar testes E2E de workflows Kestra (PowerShell)
# ═══════════════════════════════════════════════════════════════════════════

$ErrorActionPreference = "Stop"

# ── Funções auxiliares ─────────────────────────────────────────────────────

function Log-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

function Log-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Log-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Log-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# ── Banner ─────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════"
Write-Host "  IntelliCare NISE - Testes E2E de Workflows Kestra"
Write-Host "═══════════════════════════════════════════════════════════════════════════"
Write-Host ""

# ── Verificar dependências ─────────────────────────────────────────────────

Log-Info "Verificando dependências..."

# Verificar Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Log-Error "Docker não encontrado. Instale o Docker Desktop primeiro."
    exit 1
}
Log-Success "Docker encontrado"

# Verificar Docker Compose
if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Log-Error "Docker Compose não encontrado. Instale o Docker Compose primeiro."
    exit 1
}
Log-Success "Docker Compose encontrado"

# Verificar pytest
if (-not (Get-Command pytest -ErrorAction SilentlyContinue)) {
    Log-Warning "pytest não encontrado. Instalando..."
    pip install pytest pytest-asyncio pytest-cov
}
Log-Success "pytest encontrado"

# ── Verificar serviços Docker ──────────────────────────────────────────────

Log-Info "Verificando serviços Docker..."

# Verificar se NISE está rodando
$niseRunning = docker ps | Select-String "intellicare-nise"
if (-not $niseRunning) {
    Log-Warning "NISE não está rodando. Iniciando stack Docker..."
    docker-compose up -d
    Log-Info "Aguardando serviços iniciarem (30s)..."
    Start-Sleep -Seconds 30
} else {
    Log-Success "NISE está rodando"
}

# Verificar se Kestra está rodando
$kestraRunning = docker ps | Select-String "intellicare-kestra"
if (-not $kestraRunning) {
    Log-Error "Kestra não está rodando. Execute 'docker-compose up -d kestra' primeiro."
    exit 1
}
Log-Success "Kestra está rodando"

# ── Health checks ──────────────────────────────────────────────────────────

Log-Info "Verificando health dos serviços..."

# Health check NISE
$maxRetries = 10
$retryCount = 0
$niseHealthy = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            Log-Success "NISE está saudável"
            $niseHealthy = $true
            break
        }
    } catch {
        # Ignorar erro e tentar novamente
    }
    
    $retryCount++
    if ($retryCount -eq $maxRetries) {
        Log-Error "NISE não respondeu ao health check"
        exit 1
    }
    Log-Warning "Aguardando NISE... (tentativa $retryCount/$maxRetries)"
    Start-Sleep -Seconds 3
}

# Health check Kestra
$retryCount = 0
$kestraHealthy = $false

while ($retryCount -lt $maxRetries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/api/v1/health" -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            Log-Success "Kestra está saudável"
            $kestraHealthy = $true
            break
        }
    } catch {
        # Ignorar erro e tentar novamente
    }
    
    $retryCount++
    if ($retryCount -eq $maxRetries) {
        Log-Error "Kestra não respondeu ao health check"
        exit 1
    }
    Log-Warning "Aguardando Kestra... (tentativa $retryCount/$maxRetries)"
    Start-Sleep -Seconds 5
}

# ── Executar testes E2E ────────────────────────────────────────────────────

Write-Host ""
Log-Info "Executando testes E2E..."
Write-Host ""

# Executar testes com pytest
pytest tests/test_e2e_workflows.py `
    -v `
    -m e2e `
    --tb=short `
    --color=yes `
    --durations=10 `
    --cov=nise `
    --cov-report=term-missing `
    --cov-report=html:htmlcov/e2e

$testExitCode = $LASTEXITCODE

Write-Host ""

# ── Resultados ─────────────────────────────────────────────────────────────

if ($testExitCode -eq 0) {
    Log-Success "Todos os testes E2E passaram!"
    Write-Host ""
    Log-Info "Relatório de cobertura: htmlcov/e2e/index.html"
    exit 0
} else {
    Log-Error "Alguns testes E2E falharam!"
    exit $testExitCode
}

