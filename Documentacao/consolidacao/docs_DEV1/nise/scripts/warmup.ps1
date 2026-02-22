################################################################################
# NISE MVP - WARM-UP SCRIPT (PowerShell)
################################################################################
# Projeto: NISE - Treinamento Assistido
# Objetivo: Warm-up do sistema antes da validação
# Data: 27/03/2026
# Responsável: DEV1
################################################################################

Write-Host "🚀 NISE MVP - WARM-UP SCRIPT" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Base URL
$BaseUrl = "http://localhost:8000"

################################################################################
# 1. VERIFICAR SERVIÇOS
################################################################################

Write-Host "📋 1. Verificando serviços Docker..." -ForegroundColor Yellow
Write-Host ""

try {
    $containers = docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}" | Select-String "nise"
    if ($containers) {
        Write-Host "✅ Containers Docker rodando" -ForegroundColor Green
        docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}" | Select-String "nise"
    } else {
        Write-Host "❌ Nenhum container NISE encontrado!" -ForegroundColor Red
        Write-Host "Execute: docker-compose up -d" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Docker não está disponível!" -ForegroundColor Red
    exit 1
}

Write-Host ""

################################################################################
# 2. HEALTH CHECKS
################################################################################

Write-Host "🏥 2. Executando Health Checks..." -ForegroundColor Yellow
Write-Host ""

# Backend Health
Write-Host "   Backend: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/health" -Method Get -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ OK" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ FALHOU" -ForegroundColor Red
    exit 1
}

# Florence Health
Write-Host "   Florence: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/v1/florence/health" -Method Get -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ OK" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  AVISO: Florence pode não estar disponível" -ForegroundColor Yellow
}

# Ollama Health
Write-Host "   Ollama: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method Get -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ OK" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  AVISO: Ollama pode não estar disponível" -ForegroundColor Yellow
}

Write-Host ""

################################################################################
# 3. WARM-UP DE ENDPOINTS
################################################################################

Write-Host "🔥 3. Aquecendo endpoints (warm-up)..." -ForegroundColor Yellow
Write-Host ""

# Patient endpoints
Write-Host "   GET /api/v1/patients: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/v1/patients" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ $($response.StatusCode) OK" -ForegroundColor Green
} catch {
    Write-Host "❌ $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

# Observation endpoints
Write-Host "   GET /api/v1/observations: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/v1/observations" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ $($response.StatusCode) OK" -ForegroundColor Green
} catch {
    Write-Host "❌ $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

# Practitioner endpoints
Write-Host "   GET /api/v1/practitioners: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/v1/practitioners" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ $($response.StatusCode) OK" -ForegroundColor Green
} catch {
    Write-Host "❌ $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

# Encounter endpoints
Write-Host "   GET /api/v1/encounters: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/v1/encounters" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ $($response.StatusCode) OK" -ForegroundColor Green
} catch {
    Write-Host "❌ $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

Write-Host ""

################################################################################
# 4. WARM-UP FLORENCE
################################################################################

Write-Host "🤖 4. Aquecendo Florence AI..." -ForegroundColor Yellow
Write-Host ""

$florenceRequest = @{
    message = "teste de warm-up"
    session_id = "warmup-session"
} | ConvertTo-Json

Write-Host "   POST /api/v1/florence/chat: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/v1/florence/chat" `
        -Method Post `
        -Body $florenceRequest `
        -ContentType "application/json" `
        -UseBasicParsing `
        -TimeoutSec 30
    Write-Host "✅ $($response.StatusCode) OK" -ForegroundColor Green
} catch {
    Write-Host "⚠️  $($_.Exception.Response.StatusCode.value__) (Florence pode estar em modo fallback)" -ForegroundColor Yellow
}

Write-Host ""

################################################################################
# 5. VERIFICAR SWAGGER
################################################################################

Write-Host "📚 5. Verificando Swagger UI..." -ForegroundColor Yellow
Write-Host ""

Write-Host "   GET /docs: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/docs" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ $($response.StatusCode) OK" -ForegroundColor Green
} catch {
    Write-Host "❌ $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

Write-Host "   GET /openapi.json: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/api/v1/openapi.json" -Method Get -UseBasicParsing -TimeoutSec 10
    Write-Host "✅ $($response.StatusCode) OK" -ForegroundColor Green
} catch {
    Write-Host "❌ $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

Write-Host ""

################################################################################
# 6. RESUMO
################################################################################

Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ WARM-UP CONCLUÍDO!" -ForegroundColor Green
Write-Host ""
Write-Host "Sistema pronto para validação:" -ForegroundColor Cyan
Write-Host "  - Swagger UI: $BaseUrl/docs"
Write-Host "  - ReDoc: $BaseUrl/redoc"
Write-Host "  - Health: $BaseUrl/health"
Write-Host ""
Write-Host "Próximo passo: Executar validação completa" -ForegroundColor Yellow
Write-Host "  .\scripts\validate.ps1"
Write-Host ""

