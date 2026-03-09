# Carga completa de dados — IntelliCare
# Executa: seed_staging_data → seed_keycloak_staging → load_fhir_bundle
# Ver docs/CARGA_DADOS/ para documentação completa.

param(
    [string]$KeycloakAdminPass = $env:KEYCLOAK_ADMIN_PASSWORD,
    [switch]$SkipKeycloak,
    [int]$Workers = 10
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "=== Carga Completa IntelliCare ===" -ForegroundColor Cyan
Write-Host ""

# 1. Gerar dados FHIR
Write-Host "[1/3] Gerando dados FHIR (toda a base)..." -ForegroundColor Yellow
Push-Location $RepoRoot
python scripts/seed_staging_data.py --approach V2.0.0-KEYCLOAK
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host ""

# 2. Carregar Keycloak (opcional)
if (-not $SkipKeycloak) {
    if (-not $KeycloakAdminPass) {
        Write-Host "[2/3] Keycloak: senha admin nao informada." -ForegroundColor Yellow
        Write-Host "      Use: `$env:KEYCLOAK_ADMIN_PASSWORD='sua_senha'; .\scripts\carga_completa.ps1" -ForegroundColor Gray
        Write-Host "      Ou: .\scripts\carga_completa.ps1 -KeycloakAdminPass 'sua_senha'" -ForegroundColor Gray
        Write-Host "      Ou: .\scripts\carga_completa.ps1 -SkipKeycloak (pular Keycloak)" -ForegroundColor Gray
    } else {
        Write-Host "[2/3] Carregando usuarios no Keycloak..." -ForegroundColor Yellow
        python scripts/seed_keycloak_staging.py --admin-pass $KeycloakAdminPass
        if ($LASTEXITCODE -ne 0) { exit 1 }
    }
} else {
    Write-Host "[2/3] Keycloak: pulado (-SkipKeycloak)" -ForegroundColor Gray
}
Write-Host ""

# 3. Carregar FHIR no GRAHAME
Write-Host "[3/3] Carregando recursos FHIR no GRAHAME (workers=$Workers)..." -ForegroundColor Yellow
python scripts/load_fhir_bundle.py data/V2.0.0-KEYCLOAK/fhir --base-url http://localhost:8012 --workers $Workers
if ($LASTEXITCODE -ne 0) { exit 1 }

Pop-Location
Write-Host ""
Write-Host "=== Carga concluida ===" -ForegroundColor Green
