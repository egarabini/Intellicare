# ============================================================================
# Deploy Completo: apresentacao.intellicare.ia.br
# ============================================================================
# Este script faz o deploy completo do módulo de apresentação
# Executar: powershell -ExecutionPolicy Bypass -File deploy_apresentacao_completo.ps1
# ============================================================================

$ErrorActionPreference = "Continue"
$SERVER = "root@167.86.97.142"

Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🚀 Deploy: apresentacao.intellicare.ia.br              ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# ============================================================================
# Passo 1: Remover arquivo conflitante
# ============================================================================
Write-Host "`n📝 Passo 1/5: Removendo arquivo conflitante..." -ForegroundColor Yellow
ssh $SERVER "cd /opt/intellicare/intellicare; rm -f traefik/dynamic/routes-intellicare.yml"

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Arquivo removido" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Erro ao remover arquivo (pode não existir)" -ForegroundColor Yellow
}

# ============================================================================
# Passo 2: Git Pull
# ============================================================================
Write-Host "`n📥 Passo 2/5: Fazendo pull das mudanças..." -ForegroundColor Yellow
ssh $SERVER "cd /opt/intellicare/intellicare; git pull origin master"

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Pull concluído" -ForegroundColor Green
} else {
    Write-Host "   ❌ Erro no pull" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Passo 3: Docker Compose Up
# ============================================================================
Write-Host "`n🐳 Passo 3/5: Iniciando container..." -ForegroundColor Yellow
ssh $SERVER "cd /opt/intellicare/intellicare/intellicare-apresentacao; docker-compose up -d"

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Container iniciado" -ForegroundColor Green
} else {
    Write-Host "   ❌ Erro ao iniciar container" -ForegroundColor Red
    exit 1
}

# ============================================================================
# Passo 4: Verificar Container
# ============================================================================
Write-Host "`n🔍 Passo 4/5: Verificando container..." -ForegroundColor Yellow
ssh $SERVER "docker ps --filter name=apresentacao --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# ============================================================================
# Passo 5: Aguardar e Testar
# ============================================================================
Write-Host "`n⏳ Passo 5/5: Aguardando certificado SSL (30 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "`n🧪 Testando endpoint..." -ForegroundColor Yellow
$response = curl -Ik https://apresentacao.intellicare.ia.br 2>&1 | Select-String -Pattern "HTTP|Content-Type" | Select-Object -First 3

if ($response -match "HTTP/2 200") {
    Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║   ✅ DEPLOY CONCLUÍDO COM SUCESSO!                       ║" -ForegroundColor Green
    Write-Host "║                                                           ║" -ForegroundColor Green
    Write-Host "║   🌐 https://apresentacao.intellicare.ia.br              ║" -ForegroundColor Green
    Write-Host "║   📊 Reveal.js Slides                                    ║" -ForegroundColor Green
    Write-Host "║   🔐 HTTPS: Lets Encrypt                                 ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Resposta do servidor:" -ForegroundColor Yellow
    Write-Host $response
    Write-Host "`nℹ️  O certificado SSL pode levar alguns minutos para ser emitido." -ForegroundColor Cyan
    Write-Host "   Aguarde 2-3 minutos e tente acessar novamente." -ForegroundColor Cyan
}

Write-Host "`n✨ Script concluído!" -ForegroundColor Cyan

