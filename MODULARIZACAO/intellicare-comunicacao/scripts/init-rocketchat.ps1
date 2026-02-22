# ============================================================================
# SCRIPT DE INICIALIZAÇÃO - ROCKET.CHAT (PowerShell)
# ============================================================================
# Projeto 05: Sistema de Comunicação e Workflow Integrado
# Responsável: DEV1
# Data: 26/03/2026
# ============================================================================

$ErrorActionPreference = "Stop"

Write-Host "🚀 Iniciando configuração do Rocket.Chat..." -ForegroundColor Cyan

# Carregar variáveis de ambiente
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
} else {
    Write-Host "❌ Arquivo .env não encontrado!" -ForegroundColor Red
    exit 1
}

# Função para aguardar serviço
function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$MaxAttempts = 30
    )
    
    Write-Host "⏳ Aguardando $ServiceName..." -ForegroundColor Yellow
    
    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $ServiceName está pronto!" -ForegroundColor Green
                return $true
            }
        } catch {
            # Ignorar erros e tentar novamente
        }
        
        Write-Host "   Tentativa $attempt/$MaxAttempts..." -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
    
    Write-Host "❌ $ServiceName não respondeu após $MaxAttempts tentativas" -ForegroundColor Red
    return $false
}

# 1. Verificar se containers estão rodando
Write-Host ""
Write-Host "📦 Verificando containers..." -ForegroundColor Cyan
docker-compose ps

# 2. Aguardar Rocket.Chat
Write-Host ""
$rocketchatReady = Wait-ForService -ServiceName "Rocket.Chat" -Url "http://localhost:3000/api/info"

if (-not $rocketchatReady) {
    Write-Host "⚠️  Rocket.Chat não está respondendo. Verifique os logs:" -ForegroundColor Yellow
    Write-Host "   docker-compose logs rocketchat" -ForegroundColor Gray
}

# 3. Obter informações de login
Write-Host ""
Write-Host "🔐 Informações de Login:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "URL:      " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor Yellow
Write-Host "Usuário:  " -NoNewline; Write-Host "$env:ROCKETCHAT_ADMIN_USER" -ForegroundColor Yellow
Write-Host "Senha:    " -NoNewline; Write-Host "$env:ROCKETCHAT_ADMIN_PASSWORD" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green

# 4. Instruções para criar canais
Write-Host ""
Write-Host "📝 Para criar canais automaticamente:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   1. Acesse: http://localhost:3000" -ForegroundColor Gray
Write-Host "   2. Faça login com as credenciais acima" -ForegroundColor Gray
Write-Host "   3. Vá em: Perfil → Minha Conta → Tokens Pessoais" -ForegroundColor Gray
Write-Host "   4. Crie um token e execute:" -ForegroundColor Gray
Write-Host ""
Write-Host "      `$env:ROCKETCHAT_TOKEN='seu-token'" -ForegroundColor White
Write-Host "      `$env:ROCKETCHAT_USER_ID='seu-user-id'" -ForegroundColor White
Write-Host "      .\scripts\create-channels.ps1" -ForegroundColor White
Write-Host ""

# 5. Verificar Jitsi
Write-Host ""
Write-Host "🎥 Verificando Jitsi..." -ForegroundColor Cyan
try {
    $jitsiResponse = Invoke-WebRequest -Uri "http://localhost:8443" -Method Get -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue
    if ($jitsiResponse.StatusCode -eq 200) {
        Write-Host "✅ Jitsi está rodando!" -ForegroundColor Green
        Write-Host "URL: " -NoNewline; Write-Host "http://localhost:8443" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Jitsi ainda não está pronto (pode levar alguns minutos)" -ForegroundColor Yellow
}

# 6. Resumo
Write-Host ""
Write-Host "🎊 Configuração Inicial Completa!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos Passos:" -ForegroundColor Cyan
Write-Host "   1. ✅ Rocket.Chat rodando em http://localhost:3000" -ForegroundColor Gray
Write-Host "   2. ✅ Jitsi rodando em http://localhost:8443" -ForegroundColor Gray
Write-Host "   3. ⏳ Fazer login no Rocket.Chat" -ForegroundColor Gray
Write-Host "   4. ⏳ Criar canais: #geral, #alertas, #suporte" -ForegroundColor Gray
Write-Host "   5. ⏳ Testar integração com Jitsi" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 Documentação: README.md" -ForegroundColor Cyan
Write-Host ""

# Abrir navegador automaticamente
Write-Host "🌐 Abrindo Rocket.Chat no navegador..." -ForegroundColor Cyan
Start-Process "http://localhost:3000"

