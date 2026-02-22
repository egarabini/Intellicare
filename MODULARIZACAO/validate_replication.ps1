# Script de Validação da Replicação - Fase 2.5

$basePath = "C:\DOCSHARE\INTELLICARE\MODULARIZACAO"

$modules = @(
    @{ dir = "intellicare-florence"; name = "Florence"; module = "florence" }
    @{ dir = "intellicare-oswaldo"; name = "Oswaldo"; module = "oswaldo" }
    @{ dir = "intellicare-zilda"; name = "Zilda"; module = "zilda" }
    @{ dir = "intellicare-geralda"; name = "Geralda"; module = "geralda" }
    @{ dir = "intellicare-comunicacao"; name = "Comunicação"; module = "comunicacao" }
    @{ dir = "intellicare-auth"; name = "Auth"; module = "auth" }
    @{ dir = "intellicare-portal"; name = "Portal"; module = "portal" }
    @{ dir = "intellicare-wanda"; name = "Wanda"; module = "wanda" }
)

$requiredDirs = @(
    "src",
    "migrations",
    "migrations/versions",
    "tests",
    "docs",
    "docker"
)

$requiredFiles = @(
    ".gitignore",
    ".dockerignore",
    ".env.example",
    ".env.keycloak",
    "pyproject.toml",
    "pytest.ini"
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "VALIDAÇÃO DA REPLICAÇÃO - FASE 2.5" -ForegroundColor Magenta
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$validationResults = @()
$totalChecks = 0
$passedChecks = 0

foreach ($module in $modules) {
    $modulePath = Join-Path $basePath $module.dir
    $moduleName = $module.name
    $moduleInternalName = $module.module
    
    Write-Host "🔍 Validando: $moduleName" -ForegroundColor Yellow
    
    $dirStatus = @()
    $fileStatus = @()
    
    # Verificar diretórios
    foreach ($dir in $requiredDirs) {
        $dirPath = if ($dir -like "src*") {
            Join-Path $modulePath "src\$moduleInternalName"
        } else {
            Join-Path $modulePath $dir
        }
        
        $exists = Test-Path $dirPath
        $totalChecks++
        if ($exists) { $passedChecks++ }
        
        $dirStatus += @{
            path = $dir
            exists = $exists
        }
        
        $status = if ($exists) { "✅" } else { "❌" }
        Write-Host "   $status Dir: $dir" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
    }
    
    # Verificar arquivos
    foreach ($file in $requiredFiles) {
        $filePath = Join-Path $modulePath $file
        $exists = Test-Path $filePath
        $totalChecks++
        if ($exists) { $passedChecks++ }
        
        $fileStatus += @{
            file = $file
            exists = $exists
        }
        
        $status = if ($exists) { "✅" } else { "❌" }
        Write-Host "   $status File: $file" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
    }
    
    # Verificar __init__.py
    $initPath = Join-Path $modulePath "src\$moduleInternalName\__init__.py"
    $initExists = Test-Path $initPath
    $totalChecks++
    if ($initExists) { $passedChecks++ }
    
    $status = if ($initExists) { "✅" } else { "❌" }
    Write-Host "   $status Init: src/$moduleInternalName/__init__.py" -ForegroundColor $(if ($initExists) { "Green" } else { "Red" })
    
    # Verificar subdirectórios do módulo
    $subDirs = @("api", "database", "models", "schemas", "services", "data_access", "consolidation", "events", "dashboard")
    
    Write-Host "   📁 Estrutura interna:" -ForegroundColor Gray
    foreach ($subDir in $subDirs) {
        $subPath = Join-Path $modulePath "src\$moduleInternalName\$subDir"
        $subExists = Test-Path $subPath
        $totalChecks++
        if ($subExists) { $passedChecks++ }
        
        $subInitPath = Join-Path $subPath "__init__.py"
        $subInitExists = Test-Path $subInitPath
        $totalChecks++
        if ($subInitExists) { $passedChecks++ }
        
        $subStatus = if ($subExists -and $subInitExists) { "✅" } else { "❌" }
        Write-Host "      $subStatus $subDir" -ForegroundColor $(if ($subExists -and $subInitExists) { "Green" } else { "Red" })
    }
    
    Write-Host ""
}

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "RESULTADO DA VALIDAÇÃO" -ForegroundColor Magenta
Write-Host "=====================================" -ForegroundColor Cyan

$percentage = [math]::Round(($passedChecks / $totalChecks) * 100)

Write-Host "✅ Testes Aprovados: $passedChecks / $totalChecks ($percentage%)" -ForegroundColor Green
Write-Host ""

if ($percentage -eq 100) {
    Write-Host "🎉 TODOS OS MÓDULOS VALIDADOS COM SUCESSO!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Resumo da Replicação:" -ForegroundColor Cyan
    Write-Host "  • 8 módulos replicados ✅"
    Write-Host "  • Estrutura completa ✅"
    Write-Host "  • Integridade validada ✅"
    Write-Host ""
    Write-Host "Próximas Ações (Fase 2.5 Continua):" -ForegroundColor Yellow
    Write-Host "  [1] Customizar models.py para cada domínio"
    Write-Host "  [2] Definir rotas específicas da API"
    Write-Host "  [3] Configurar dashboard Streamlit"
    Write-Host "  [4] Executar testes de integração"
    Write-Host "  [5] Documentação técnica por módulo"
    Write-Host ""
} else {
    Write-Host "⚠️  Alguns testes falharam ($(100 - $percentage)% de problemas)" -ForegroundColor Red
}

Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
