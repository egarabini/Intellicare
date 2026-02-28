# Script PowerShell para executar testes de integração Keycloak
# Este script inicia o servidor e executa os testes automaticamente

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TESTES DE INTEGRAÇÃO KEYCLOAK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navegar para o diretório correto
Set-Location $PSScriptRoot

# Ativar ambiente virtual
Write-Host "Ativando ambiente virtual..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Iniciar servidor em background
Write-Host "Iniciando servidor em background..." -ForegroundColor Yellow
$serverJob = Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    & .\venv\Scripts\python.exe -m uvicorn src.donabedian.api.main:app --host 0.0.0.0 --port 8003
} -ArgumentList $PSScriptRoot

# Aguardar servidor iniciar
Write-Host "Aguardando servidor iniciar (15 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Verificar se servidor está rodando
Write-Host "Verificando se servidor está rodando..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Servidor está rodando!" -ForegroundColor Green
} catch {
    Write-Host "❌ Servidor não está respondendo. Verifique os logs." -ForegroundColor Red
    Stop-Job $serverJob
    Remove-Job $serverJob
    exit 1
}

# Executar testes
Write-Host ""
Write-Host "Executando testes..." -ForegroundColor Yellow
Write-Host ""

python test_keycloak_integration.py

# Parar servidor
Write-Host ""
Write-Host "Parando servidor..." -ForegroundColor Yellow
Stop-Job $serverJob
Remove-Job $serverJob

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TESTES CONCLUÍDOS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Read-Host "Pressione ENTER para sair"

