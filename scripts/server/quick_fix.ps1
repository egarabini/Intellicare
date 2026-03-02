# ============================================================================
# IntelliCare — Server Fix Script (Local Execution)
# ============================================================================
# Este script deve ser executado no seu computador local (Windows)
# Ele se conectará ao servidor via SSH e executará as correções necessárias
# ============================================================================

# Configurações
$SERVER = "167.86.97.142"
$USER = "root"
$PASSWORD = "Soeuso410863"
$LOCAL_PATH = "C:\DOCSHARE\INTELLICARE"
$REMOTE_PATH = "/opt/intellicare/intellicare"

Write-Host "============================================================================" -ForegroundColor Blue
Write-Host "IntelliCare — Atualização do Servidor $SERVER" -ForegroundColor Blue
Write-Host "============================================================================" -ForegroundColor Blue
Write-Host ""

# Verificar se plink está disponível (PuTTY)
$PLINK_PATH = Get-Command plink -ErrorAction SilentlyContinue

if (-not $PLINK_PATH) {
    Write-Host "ERRO: plink não encontrado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Você precisa instalar o PuTTY ou usar ssh do Windows:"
    Write-Host "  1. Baixe PuTTY: https://www.putty.org/"
    Write-Host "  2. Ou use o SSH nativo do Windows 10/11"
    Write-Host ""
    exit 1
}

Write-Host "Plink encontrado: $($PLINK_PATH.Source)" -ForegroundColor Green
Write-Host ""

# ============================================================================
# FUNÇÃO PARA EXECUTAR COMANDO SSH
# ============================================================================
function Invoke-SSHCommand {
    param(
        [string]$Command
    )

    Write-Host "Executando: $Command" -ForegroundColor Yellow

    $output = echo y | plink -ssh -pw $PASSWORD $USER@$SERVER $Command 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ⚠ Erro (código $LASTEXITCODE)" -ForegroundColor Red
    }

    return $output
}

# ============================================================================
# PASSO 1: DIAGNÓSTICO
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "PASSO 1: Diagnóstico do Servidor" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "Verificando conexão com o servidor..." -ForegroundColor Cyan
$TEST_OUTPUT = Invoke-SSHCommand "echo 'Conexão OK'"
Write-Host "  ✓ Conexão estabelecida" -ForegroundColor Green
Write-Host ""

Write-Host "Verificando versão do Docker..." -ForegroundColor Cyan
$DOCKER_VERSION = Invoke-SSHCommand "docker --version 2>&1"
Write-Host "  $DOCKER_VERSION" -ForegroundColor White
Write-Host ""

Write-Host "Verificando containers..." -ForegroundColor Cyan
$CONTAINERS = Invoke-SSHCommand "docker ps --all --filter 'name=intellicare' --format 'table {{.Names}}\t{{.Status}}' 2>&1"
Write-Host $CONTAINERS -ForegroundColor White
Write-Host ""

# ============================================================================
# PASSO 2: PREPARAR ARQUIVOS
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "PASSO 2: Preparar Arquivos para Upload" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "Verificando repositório Git local..." -ForegroundColor Cyan
Set-Location $LOCAL_PATH

$GIT_STATUS = git status --porcelain 2>&1
if ($GIT_STATUS) {
    Write-Host "  ⚠ Há alterações não commitadas no repositório" -ForegroundColor Yellow
    Write-Host "  Deseja fazer commit antes de continuar? (y/N): " -NoNewline
    $COMMIT_ANSWER = Read-Host

    if ($COMMIT_ANSWER -eq 'y' -or $COMMIT_ANSWER -eq 'Y') {
        Write-Host "  Fazendo pull das alterações..." -ForegroundColor Cyan
        git pull
    }
} else {
    Write-Host "  ✓ Repositório limpo" -ForegroundColor Green
}

Write-Host ""
Write-Host "Sincronizando arquivos do repositório..." -ForegroundColor Cyan
git pull
Write-Host "  ✓ Repositório atualizado" -ForegroundColor Green
Write-Host ""

# ============================================================================
# PASSO 3: FAZER UPLOAD DOS ARQUIVOS
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "PASSO 3: Upload dos Arquivos Atualizados" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "Fazendo upload das configurações do Traefik..." -ForegroundColor Cyan

# Usar pscp (PuTTY SCP) para upload
$PSCP_PATH = Get-Command pscp -ErrorAction SilentlyContinue

if ($PSCP_PATH) {
    Write-Host "  Upload de routes-intellicare.yml..." -ForegroundColor Cyan
    echo y | pscp -pw $PASSWORD "$LOCAL_PATH\traefik\dynamic\routes-intellicare.yml" "${USER}@${SERVER}:${REMOTE_PATH}/traefik/dynamic/"

    Write-Host "  Upload de routes-saudeconectada.yml..." -ForegroundColor Cyan
    echo y | pscp -pw $PASSWORD "$LOCAL_PATH\traefik\dynamic\routes-saudeconectada.yml" "${USER}@${SERVER}:${REMOTE_PATH}/traefik/dynamic/"

    Write-Host "  ✓ Arquivos atualizados no servidor" -ForegroundColor Green
} else {
    Write-Host "  ⚠ pscp não encontrado, pulando upload" -ForegroundColor Yellow
    Write-Host "  Você precisará fazer upload manualmente:" -ForegroundColor Yellow
    Write-Host "    pscp -pw $PASSWORD traefik\dynamic\*.yml ${USER}@${SERVER}:${REMOTE_PATH}/traefik/dynamic/" -ForegroundColor White
}

Write-Host ""

# ============================================================================
# PASSO 4: ENVIAR SCRIPT DE CORREÇÃO
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "PASSO 4: Enviar Script de Correção" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

$SCRIPT_PATH = "$LOCAL_PATH\scripts\server\quick_fix.sh"

if (Test-Path $SCRIPT_PATH) {
    Write-Host "Enviando script quick_fix.sh para o servidor..." -ForegroundColor Cyan

    if ($PSCP_PATH) {
        echo y | pscp -pw $PASSWORD $SCRIPT_PATH "${USER}@${SERVER}:/tmp/"
        Write-Host "  ✓ Script enviado" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ pscp não encontrado" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ Script não encontrado: $SCRIPT_PATH" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# PASSO 5: EXECUTAR CORREÇÃO NO SERVIDOR
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "PASSO 5: Executar Correção no Servidor" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "Deseja executar o script de correção no servidor agora? (y/N): " -NoNewline -ForegroundColor Cyan
$EXECUTE_ANSWER = Read-Host

if ($EXECUTE_ANSWER -eq 'y' -or $EXECUTE_ANSWER -eq 'Y') {
    Write-Host ""
    Write-Host "Executando script de correção..." -ForegroundColor Cyan
    Write-Host "  Isso pode levar vários minutos..." -ForegroundColor Yellow
    Write-Host ""

    $FIX_OUTPUT = Invoke-SSHCommand "bash /tmp/quick_fix.sh"

    Write-Host $FIX_OUTPUT -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "  Pulando execução automática" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para executar manualmente:" -ForegroundColor Cyan
    Write-Host "    1. Conecte-se ao servidor: plink -ssh -pw $PASSWORD $USER@$SERVER" -ForegroundColor White
    Write-Host "    2. Execute o script: bash /tmp/quick_fix.sh" -ForegroundColor White
}

Write-Host ""

# ============================================================================
# PASSO 6: VERIFICAR STATUS FINAL
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host "PASSO 6: Verificar Status Final" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "Aguardando 10 segundos para os containers iniciarem..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "Status dos containers:" -ForegroundColor Cyan
$FINAL_CONTAINERS = Invoke-SSHCommand "docker ps --filter 'name=intellicare' --format 'table {{.Names}}\t{{.Status}}'"
Write-Host $FINAL_CONTAINERS -ForegroundColor White
Write-Host ""

# ============================================================================
# FINALIZAÇÃO
# ============================================================================
Write-Host ""
Write-Host "============================================================================" -ForegroundColor Blue
Write-Host "Processo Concluído!" -ForegroundColor Blue
Write-Host "============================================================================" -ForegroundColor Blue
Write-Host ""

Write-Host "Resumo:" -ForegroundColor Cyan
Write-Host "  Servidor: $SERVER" -ForegroundColor White
Write-Host "  Usuário: $USER" -ForegroundColor White
Write-Host ""

Write-Host "Próximos passos:" -ForegroundColor Cyan
Write-Host "  1. Acesse o servidor para investigar problemas:" -ForegroundColor White
Write-Host "     plink -ssh -pw $PASSWORD $USER@$SERVER" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Verifique os logs dos containers com problemas:" -ForegroundColor White
Write-Host "     docker logs <container-name> --tail 50" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Reinicie o Traefik:" -ForegroundColor White
Write-Host "     docker restart intellicare-traefik" -ForegroundColor Yellow
Write-Host ""
Write-Host "  4. Acesse:" -ForegroundColor White
Write-Host "     https://grafana.intellicare.ia.br" -ForegroundColor Green
Write-Host "     https://portal.intellicare.ia.br" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================================" -ForegroundColor Blue
