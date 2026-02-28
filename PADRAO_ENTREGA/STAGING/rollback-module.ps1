# ============================================================================
# IntelliCare - Script de Rollback (Staging)
# ============================================================================
# Este script executa rollback de um módulo para o commit anterior
# em caso de falha de health/smoke test. Faz parte dos controles V2.
# ============================================================================
# Uso:
#   .\PADRAO_ENTREGA\STAGING\rollback-module.ps1 -Module <modulo> -Host <ip>
#
# Exemplo:
#   .\PADRAO_ENTREGA\STAGING\rollback-module.ps1 -Module portal -Host 167.86.97.142
# ============================================================================

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("portal", "admin", "wanda", "grahame", "oswaldo", "florence", "donabedian", "zilda", "geralda", "comunicacao", "nise")]
    [string]$Module,

    [Parameter(Mandatory = $true)]
    [string]$Host,

    [string]$User = "root",
    [string]$Branch = "main",
    [string]$RepoPath = "/opt/intellicare",
    [string]$ComposeFile = "docker-compose.full.yml",
    [string]$EnvFile = ".env.full",

    [int]$CommitsBack = 1,

    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Cores para output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Mapeamento de serviço Docker
$serviceMap = @{
    "portal" = @{
        Service = "portal"
        HealthUrl = "http://localhost:3001"
        Description = "Frontend Portal"
    }
    "admin" = @{
        Service = "admin"
        HealthUrl = "http://localhost:8010/api/v1/health"
        Description = "Admin API"
    }
    "wanda" = @{
        Service = "wanda"
        HealthUrl = "http://localhost:8004/api/v1/health"
        Description = "Wanda Orchestrator"
    }
    "grahame" = @{
        Service = "grahame"
        HealthUrl = "http://localhost:8012/api/v1/health"
        Description = "Grahame FHIR Server"
    }
    "oswaldo" = @{
        Service = "oswaldo"
        HealthUrl = "http://localhost:8002/api/v1/health"
        Description = "Oswaldo Chronic Disease"
    }
    "florence" = @{
        Service = "florence"
        HealthUrl = "http://localhost:8001/api/v1/health"
        Description = "Florence Clinical Intelligence"
    }
    "donabedian" = @{
        Service = "donabedian"
        HealthUrl = "http://localhost:8003/api/v1/health"
        Description = "Donabedian Quality Assessment"
    }
    "zilda" = @{
        Service = "zilda"
        HealthUrl = "http://localhost:8007/api/v1/health"
        Description = "Zilda Health Data"
    }
    "geralda" = @{
        Service = "geralda"
        HealthUrl = "http://localhost:8006/api/v1/health"
        Description = "Geralda Patient Accompaniment"
    }
    "comunicacao" = @{
        Service = "comunicacao"
        HealthUrl = "http://localhost:8005/api/v1/health"
        Description = "Comunicacao (Rocket.Chat+Jitsi)"
    }
    "nise" = @{
        Service = "nise"
        HealthUrl = "http://localhost:8013/api/v1/health"
        Description = "Nise Chatbot + Flowise"
    }
}

if (-not $serviceMap.ContainsKey($Module)) {
    throw "Unsupported module: $Module"
}

$service = $serviceMap[$Module].Service
$healthUrl = $serviceMap[$Module].HealthUrl
$description = $serviceMap[$Module].Description

# ============================================================================
# CONFIRMAÇÃO DE SEGURANÇA
# ============================================================================

Write-ColorOutput "`n" "White"
Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Yellow"
Write-ColorOutput "║         ⚠ ROLLBACK CONFIRMATION REQUIRED ⚠                ║" "Yellow"
Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Yellow"
Write-ColorOutput "`n" "White"

Write-ColorOutput "This operation will ROLLBACK module '$Module' ($description)" "Red"
Write-ColorOutput "on server '$Host' to $CommitsBack commit(s) ago." "Red"
Write-ColorOutput "`n" "White"

Write-ColorOutput "Details:" "Cyan"
Write-ColorOutput "  Module:     $Module" "White"
Write-ColorOutput "  Service:    $service" "White"
Write-ColorOutput "  Host:       $Host" "White"
Write-ColorOutput "  Branch:     $Branch" "White"
Write-ColorOutput "  Commits:    -$CommitsBack" "White"
Write-ColorOutput "  Health URL: $healthUrl" "White"
Write-ColorOutput "`n" "White"

if (-not $Force) {
    $confirmation = Read-Host "Type 'ROLLBACK' to confirm this operation"
    if ($confirmation -ne "ROLLBACK") {
        Write-ColorOutput "`n✗ Rollback cancelled by user." "Yellow"
        exit 1
    }
}

# ============================================================================
# SCRIPT REMOTO DE ROLLBACK
# ============================================================================

$remoteScript = @"
set -euo pipefail

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] `$1"
}

cd "$RepoPath"

# ============================================================================
# PASSO 1: Capturar estado atual
# ============================================================================
log "[1/7] Capturing current state..."

CURRENT_COMMIT=\$(git rev-parse HEAD)
CURRENT_COMMIT_MSG=\$(git log -1 --pretty=%B HEAD)
log "Current commit: \$CURRENT_COMMIT"
log "Current message: \$CURRENT_COMMIT_MSG"

# ============================================================================
# PASSO 2: Obter commit alvo
# ============================================================================
log "[2/7] Determining target commit..."

TARGET_COMMIT=\$(git rev-parse HEAD~$CommitsBack)
TARGET_COMMIT_MSG=\$(git log -1 --pretty=%B HEAD~$CommitsBack)
log "Target commit: \$TARGET_COMMIT"
log "Target message: \$TARGET_COMMIT_MSG"

# ============================================================================
# PASSO 3: Backup do estado atual (antes do rollback)
# ============================================================================
log "[3/7] Creating backup snapshot..."

BACKUP_DIR="/opt/intellicare/backups/rollback_$($Module)_\$(date +%Y%m%d_%H%M%S)"
mkdir -p "\$BACKUP_DIR"

# Salvar informações do deploy atual
cat > "\$BACKUP_DIR/rollback_info.txt" <<EOF
Rollback Information
====================
Date: \$(date)
Module: $Module
Service: $service
From Commit: \$CURRENT_COMMIT
From Message: \$CURRENT_COMMIT_MSG
To Commit: \$TARGET_COMMIT
To Message: \$TARGET_COMMIT_MSG
Triggered By: $env:USERNAME@$env:COMPUTERNAME
EOF

log "Backup created at: \$BACKUP_DIR"

# ============================================================================
# PASSO 4: Rollback Git
# ============================================================================
log "[4/7] Performing git rollback..."

git checkout "$Branch"
git reset --hard "\$TARGET_COMMIT"

log "Repository reset to target commit"

# ============================================================================
# PASSO 5: Recriar contêiner
# ============================================================================
log "[5/7] Recreating container for service $service..."

# Parar serviço
docker compose --env-file "$EnvFile" -f "$ComposeFile" stop "$service"

# Remover contêiner (mas não volumes)
docker compose --env-file "$EnvFile" -f "$ComposeFile" rm -f "$service"

# Recriar e iniciar
docker compose --env-file "$EnvFile" -f "$ComposeFile" up -d "$service"

log "Container recreated"

# ============================================================================
# PASSO 6: Aguardar startup
# ============================================================================
log "[6/7] Waiting for service startup..."

sleep 10

# Verificar status do contêiner
docker compose --env-file "$EnvFile" -f "$ComposeFile" ps "$service"

# ============================================================================
# PASSO 7: Health Check
# ============================================================================
log "[7/7] Performing health check..."

if command -v curl >/dev/null 2>&1; then
    MAX_RETRIES=12
    RETRY_DELAY=5
    RETRY_COUNT=0

    while [ \$RETRY_COUNT -lt \$MAX_RETRIES ]; do
        if curl -fsS "$healthUrl" >/dev/null 2>&1; then
            log "✓ Health check PASSED: $healthUrl"
            echo ""
            echo "=========================================="
            echo "✓ ROLLBACK SUCCESSFUL"
            echo "=========================================="
            echo "Module: $Module"
            echo "From: \$CURRENT_COMMIT"
            echo "To:   \$TARGET_COMMIT"
            echo "Backup: \$BACKUP_DIR"
            echo "=========================================="
            exit 0
        fi

        RETRY_COUNT=\$((RETRY_COUNT + 1))
        log "Health check attempt \$RETRY_COUNT/\$MAX_RETRIES failed. Retrying in \$RETRY_DELAY seconds..."
        sleep \$RETRY_DELAY
    done

    log "✗ Health check FAILED after \$MAX_RETRIES attempts"
    echo ""
    echo "=========================================="
    echo "✗ ROLLBACK INCOMPLETE"
    echo "=========================================="
    echo "Service failed health check"
    echo "Manual intervention required!"
    echo "Backup info: \$BACKUP_DIR/rollback_info.txt"
    echo "=========================================="
    exit 1
else
    log "⚠ curl not found; skipping HTTP health check"
    echo ""
    echo "=========================================="
    echo "⚠ ROLLBACK COMPLETE (Health check skipped)"
    echo "=========================================="
    echo "Please verify service manually: $healthUrl"
    echo "Backup: \$BACKUP_DIR"
    echo "=========================================="
fi
"@

# ============================================================================
# EXECUÇÃO REMOTA
# ============================================================================

Write-ColorOutput "`n" "White"
Write-ColorOutput "🚀 Starting rollback operation..." "Yellow"
Write-ColorOutput "`n" "White"

$target = "$User@$Host"

try {
    $remoteScript | ssh $target "bash -s"

    Write-ColorOutput "`n" "White"
    Write-ColorOutput "✓ Rollback completed successfully!" "Green"
    Write-ColorOutput "`n📝 Next steps:" "Cyan"
    Write-ColorOutput "  1. Verify service functionality manually" "White"
    Write-ColorOutput "  2. Check application logs for errors" "White"
    Write-ColorOutput "  3. Register rollback in technical diary" "White"
    Write-ColorOutput "  4. Investigate root cause of failure" "White"
    Write-ColorOutput "`n📖 Technical diary registration:" "Cyan"
    Write-ColorOutput "   Module: $Module" "Gray"
    Write-ColorOutput "   Action: Rollback -$CommitsBack commits" "Gray"
    Write-ColorOutput "   Reason: Post-deploy health/smoke test failure" "Gray"
    Write-ColorOutput "   Status: Completed" "Gray"

    exit 0
}
catch {
    Write-ColorOutput "`n✗ Rollback failed!" "Red"
    Write-ColorOutput "Error: $($_.Exception.Message)" "Red"
    Write-ColorOutput "`n⚠ Manual intervention required on server!" "Yellow"
    Write-ColorOutput "Server: $Host" "Gray"
    Write-ColorOutput "Module: $Module" "Gray"
    exit 1
}
