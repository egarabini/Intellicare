# ============================================================================
# IntelliCare - Script de Validação Mínima (Pré-Push)
# ============================================================================
# Este script executa validações mínimas obrigatórias antes de permitir push
# para o repositório. Faz parte dos controles operacionais V2.
# ============================================================================
# Uso:
#   .\PADRAO_ENTREGA\GIT\validacao-minima.ps1 [-Module <modulo>]
#
# Se Module não for especificado, valida todos os módulos com mudanças
# ============================================================================

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("portal", "admin", "wanda", "grahame", "oswaldo", "florence", "donabedian", "zilda", "geralda", "comunicacao", "nise", "")]
    [string]$Module = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..\..")

# Cores para output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Configuração de validação por módulo
$moduleConfig = @{
    "portal" = @{
        Path = "intellicare-portal"
        Tests = @(
            @{ Command = "npm"; Args = @("--prefix", "intellicare-portal/frontend", "run", "build"); Description = "Build frontend" }
        )
    }
    "admin" = @{
        Path = "intellicare-admin"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
    "wanda" = @{
        Path = "intellicare-wanda"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
    "grahame" = @{
        Path = "intellicare-grahame"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
    "oswaldo" = @{
        Path = "intellicare-oswaldo"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
    "florence" = @{
        Path = "intellicare-florence"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
    "donabedian" = @{
        Path = "intellicare-donabedian"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
    "zilda" = @{
        Path = "intellicare-zilda"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
    "geralda" = @{
        Path = "intellicare-geralda"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
    "comunicacao" = @{
        Path = "intellicare-comunicacao"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
    "nise" = @{
        Path = "intellicare-nise"
        Tests = @(
            @{ Command = "python"; Args = @("-m", "pytest", "-q", "tests/"); Description = "Unit tests" }
        )
    }
}

function Invoke-ValidationTest {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [string]$Description,
        [string]$Workdir
    )

    Write-ColorOutput "  ▶ Running: $Description" "Cyan"

    $originalLocation = Get-Location
    try {
        if ($Workdir) {
            Set-Location (Join-Path $repoRoot $Workdir)
        } else {
            Set-Location $repoRoot
        }

        & $Command @Arguments 2>&1 | Tee-Object -Variable output
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "  ✗ FAILED: $Description" "Red"
            return $false
        }

        Write-ColorOutput "  ✓ PASSED: $Description" "Green"
        return $true
    }
    catch {
        Write-ColorOutput "  ✗ ERROR: $Description - $($_.Exception.Message)" "Red"
        return $false
    }
    finally {
        Set-Location $originalLocation
    }
}

function Test-ModuleChanges {
    param([string]$ModulePath)

    Push-Location $repoRoot
    try {
        $changes = git status --porcelain -- $ModulePath 2>$null
        return $changes
    }
    finally {
        Pop-Location
    }
}

function Invoke-ModuleValidation {
    param([string]$ModuleName)

    if (-not $moduleConfig.ContainsKey($ModuleName)) {
        Write-ColorOutput "⚠ Module '$ModuleName' not configured for validation. Skipping..." "Yellow"
        return $true
    }

    $config = $moduleConfig[$ModuleName]
    $modulePath = $config.Path

    Write-ColorOutput "`n📦 Validating module: $ModuleName ($modulePath)" "Cyan"

    # Verificar se há mudanças
    $changes = Test-ModuleChanges -ModulePath $modulePath
    if (-not $changes) {
        Write-ColorOutput "  No changes detected. Skipping validation." "Gray"
        return $true
    }

    Write-ColorOutput "  Changes detected:" "Yellow"
    Write-ColorOutput $changes "Gray"

    # Executar testes configurados
    $allPassed = $true
    foreach ($test in $config.Tests) {
        $result = Invoke-ValidationTest `
            -Command $test.Command `
            -Arguments $test.Args `
            -Description $test.Description `
            -Workdir $modulePath

        if (-not $result) {
            $allPassed = $false
        }
    }

    return $allPassed
}

# ============================================================================
# MAIN
# ============================================================================

Write-ColorOutput "`n" "White"
Write-ColorOutput "╔════════════════════════════════════════════════════════════╗" "Cyan"
Write-ColorOutput "║  IntelliCare - Validação Mínima (Pré-Push)                ║" "Cyan"
Write-ColorOutput "║  Padrão V2 - Controles Operacionais Obrigatórios          ║" "Cyan"
Write-ColorOutput "╚════════════════════════════════════════════════════════════╝" "Cyan"
Write-ColorOutput "`n" "White"

$failedModules = @()

if ($Module) {
    # Validar módulo específico
    $result = Invoke-ModuleValidation -ModuleName $Module
    if (-not $result) {
        $failedModules += $Module
    }
}
else {
    # Validar todos os módulos com mudanças
    Write-ColorOutput "🔍 Scanning for changed modules..." "Yellow"

    foreach ($moduleName in $moduleConfig.Keys) {
        $modulePath = $moduleConfig[$moduleName].Path
        $changes = Test-ModuleChanges -ModulePath $modulePath

        if ($changes) {
            $result = Invoke-ModuleValidation -ModuleName $moduleName
            if (-not $result) {
                $failedModules += $moduleName
            }
        }
    }
}

# Resultado final
Write-ColorOutput "`n" "White"
Write-ColorOutput "═══════════════════════════════════════════════════════════" "Cyan"

if ($failedModules.Count -eq 0) {
    Write-ColorOutput "✓ ALL VALIDATIONS PASSED" "Green"
    Write-ColorOutput "✓ Safe to proceed with git push" "Green"
    Write-ColorOutput "`n📝 Next step: Run publish-module.ps1 to commit and push" "Cyan"
    exit 0
}
else {
    Write-ColorOutput "✗ VALIDATION FAILED for modules: $($failedModules -join ', ')" "Red"
    Write-ColorOutput "`n⚠ DO NOT PUSH. Fix the errors above before proceeding." "Yellow"
    Write-ColorOutput "`n💡 To skip validation (NOT RECOMMENDED):" "Yellow"
    Write-ColorOutput "   .\PADRAO_ENTREGA\GIT\publish-module.ps1 -Module <X> -SkipValidation" "Gray"
    exit 1
}
