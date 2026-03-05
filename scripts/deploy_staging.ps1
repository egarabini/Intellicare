#!/usr/bin/env pwsh
# ==============================================================================
# IntelliCare - Deploy Staging (Executa LOCALMENTE)
# ==============================================================================
# Fluxo: commit local → push git staging → SSH servidor → docker restart
#
# USO:
#   .\scripts\deploy_staging.ps1
#   .\scripts\deploy_staging.ps1 -Message "feat: nova funcionalidade"
#   .\scripts\deploy_staging.ps1 -Message "fix: correcao" -RebuildPortal
#   .\scripts\deploy_staging.ps1 -SkipCommit   # só deploy, sem commit
#
# PRÉ-REQUISITO: SSH key configurada para o servidor (sem senha)
#   ssh-keygen -t ed25519 -C "dev@intellicare"
#   ssh-copy-id root@167.86.97.142
# ==============================================================================

param(
    [string]$Message = "",
    [switch]$RebuildPortal,
    [switch]$RebuildAdmin,
    [switch]$SkipCommit,
    [switch]$Help
)

# --- Configurações ---
$SERVER_HOST = "167.86.97.142"
$SERVER_USER = "root"
$SERVER_PATH = "/opt/intellicare"
$GIT_BRANCH = "staging"

# --- Cores ---
function Info($msg) { Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Ok($msg) { Write-Host "✅ $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Err($msg) { Write-Host "❌ $msg" -ForegroundColor Red }
function Step($n, $msg) { Write-Host "`n[$n] $msg" -ForegroundColor Magenta }

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║   🚀 IntelliCare - Deploy Staging                        ║" -ForegroundColor Blue
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""

# ==============================================================================
# PASSO 1 — Git commit + push
# ==============================================================================
Step "1/4" "Git: commit + push → origin/$GIT_BRANCH"

if (-not $SkipCommit) {
    # Verificar se estamos no branch certo
    $currentBranch = git branch --show-current
    if ($currentBranch -ne $GIT_BRANCH) {
        Warn "Branch atual: '$currentBranch'. Mudando para '$GIT_BRANCH'..."
        git checkout $GIT_BRANCH
        if ($LASTEXITCODE -ne 0) { Err "Falhou ao mudar de branch."; exit 1 }
    }

    # Ver se há mudanças
    $status = git status --porcelain
    if ($status) {
        if ($Message -eq "") {
            $Message = Read-Host "  Mensagem do commit (ou Enter para 'chore: update')"
            if ($Message -eq "") { $Message = "chore: update" }
        }
        git add -A
        git commit -m $Message
        if ($LASTEXITCODE -ne 0) { Err "Commit falhou."; exit 1 }
        Ok "Commit realizado: $Message"
    }
    else {
        Info "Nenhuma mudança local para commitar."
    }

    # Push
    Info "Enviando para origin/$GIT_BRANCH..."
    git push origin $GIT_BRANCH
    if ($LASTEXITCODE -ne 0) { Err "Push falhou."; exit 1 }
    Ok "Push concluído."
}
else {
    Info "SkipCommit ativo — pulando commit e push."
}

# ==============================================================================
# PASSO 2 — Verificar SSH sem senha
# ==============================================================================
Step "2/4" "Verificando conexão SSH com o servidor"

$sshTest = ssh -o ConnectTimeout=5 -o BatchMode=yes "${SERVER_USER}@${SERVER_HOST}" "echo OK" 2>&1
if ($sshTest -ne "OK") {
    Err "Não foi possível conectar ao servidor SEM senha."
    Err "Configure a chave SSH:"
    Write-Host "  ssh-keygen -t ed25519 -C 'dev@intellicare'" -ForegroundColor Yellow
    Write-Host "  ssh-copy-id ${SERVER_USER}@${SERVER_HOST}" -ForegroundColor Yellow
    exit 1
}
Ok "SSH OK — conexão sem senha funcionando."

# ==============================================================================
# PASSO 3 — Deploy no servidor via SSH
# ==============================================================================
Step "3/4" "Deploy no servidor remoto"

# Detectar se portal mudou (para decidir se precisa rebuild)
$portalChanged = $false
$adminChanged = $false
if (-not $SkipCommit) {
    $changedFiles = git diff --name-only HEAD~1 HEAD 2>/dev/null
    if ($changedFiles -match "intellicare-portal|docker-compose.full.yml") {
        $portalChanged = $true
    }
    if ($changedFiles -match "intellicare-admin") {
        $adminChanged = $true
    }
}
if ($RebuildPortal) { $portalChanged = $true }
if ($RebuildAdmin) { $adminChanged = $true }

if ($portalChanged -or $adminChanged) {
    Info "Mudanças em imagens (Portal ou Admin) detectadas — rebuild necessário."
}
else {
    Info "Sem mudanças estruturais — apenas restart dos containers."
}

# Montar script remoto
$remoteScript = @"
set -e
cd $SERVER_PATH

echo '--- git pull ---'
git fetch origin
git reset --hard origin/$GIT_BRANCH
echo "Commit atual: \$(git log -1 --oneline)"

echo '--- docker restart ---'
"@

if ($portalChanged) {
    $remoteScript += @"

echo 'Rebuild do portal (pode levar alguns minutos)...'
docker compose -f docker-compose.full.yml build portal
"@
}

if ($adminChanged) {
    $remoteScript += @"

echo 'Rebuild do admin (pode levar alguns minutos)...'
docker compose -f docker-compose.full.yml build admin
"@
}

$remoteScript += @"

docker compose -f docker-compose.full.yml -f docker-compose.traefik.yml up -d --remove-orphans
docker compose -f docker-compose.keycloak.yml --env-file .env.full up -d

echo '--- status ---'
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'intellicare|keycloak|NAMES'
"@

ssh "${SERVER_USER}@${SERVER_HOST}" $remoteScript
if ($LASTEXITCODE -ne 0) { Err "Deploy no servidor falhou."; exit 1 }

# ==============================================================================
# PASSO 4 — Resultado
# ==============================================================================
Step "4/4" "Deploy concluído"
Write-Host ""
Ok "Tudo pronto! Acesse:"
Write-Host "  🌐 Portal:   https://portal.intellicare.ia.br" -ForegroundColor Cyan
Write-Host "  🔑 Keycloak: http://${SERVER_HOST}:8080" -ForegroundColor Cyan
Write-Host "  📊 Grafana:  http://${SERVER_HOST}:3000" -ForegroundColor Cyan
Write-Host "  🌐 Admin:    https://admin.intellicare.ia.br" -ForegroundColor Cyan
Write-Host "  🔗 API:      https://api.intellicare.ia.br" -ForegroundColor Cyan
Write-Host ""

