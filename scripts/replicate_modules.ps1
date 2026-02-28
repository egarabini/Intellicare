# Script de Replicação da Fase 2.5
# Template: Donabedian → 7 Módulos

$basePath = "C:\DOCSHARE\INTELLICARE"
$templatePath = Join-Path $basePath "intellicare-donabedian"

# Mapeamento de módulos (directório → nome amigável)
$modules = @{
    "intellicare-florence" = @{
        name = "Florence"
        title = "Análise Clínica"
        module_name = "florence"
    }
    "intellicare-oswaldo" = @{
        name = "Oswaldo"
        title = "Gestão de Pacientes"
        module_name = "oswaldo"
    }
    "intellicare-zilda" = @{
        name = "Zilda"
        title = "Epidemiologia"
        module_name = "zilda"
    }
    "intellicare-geralda" = @{
        name = "Geralda"
        title = "Notas Clínicas"
        module_name = "geralda"
    }
    "intellicare-comunicacao" = @{
        name = "Comunicação"
        title = "Mensagens"
        module_name = "comunicacao"
    }
    "intellicare-auth" = @{
        name = "Auth"
        title = "Autenticação"
        module_name = "auth"
    }
    "intellicare-portal" = @{
        name = "Portal"
        title = "Dashboard"
        module_name = "portal"
    }
    "intellicare-wanda" = @{
        name = "Wanda"
        title = "IA Assistente"
        module_name = "wanda"
    }
}

# Estrutura de diretórios base a replicar
$directoriesToCreate = @(
    "src/{module_name}",
    "src/{module_name}/api",
    "src/{module_name}/database",
    "src/{module_name}/models",
    "src/{module_name}/schemas",
    "src/{module_name}/services",
    "src/{module_name}/data_access",
    "src/{module_name}/consolidation",
    "src/{module_name}/events",
    "src/{module_name}/dashboard",
    "migrations/versions",
    "tests",
    "docs",
    "docker"
)

# Arquivos a copiar e customizar
$filesToCopy = @(
    ".gitignore",
    ".dockerignore",
    ".env.example",
    ".env.keycloak",
    "pyproject.toml",
    "pytest.ini",
    "alembic.ini"
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "FASE 2.5: REPLICAÇÃO DE MÓDULOS" -ForegroundColor Magenta
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Template: Donabedian" -ForegroundColor Yellow
Write-Host "Destino: 7 módulos" -ForegroundColor Yellow
Write-Host ""

# Função para replicar um módulo
function Replicate-Module {
    param(
        [string]$ModuleDir,
        [hashtable]$ModuleInfo
    )
    
    $modulePath = Join-Path $basePath $ModuleDir
    $moduleName = $ModuleInfo.module_name
    $moduleFriendlyName = $ModuleInfo.name
    $moduleTitle = $ModuleInfo.title
    
    Write-Host "📦 Replicando: $moduleFriendlyName ($moduleTitle)" -ForegroundColor Cyan
    Write-Host "   Diretório: $ModuleDir" -ForegroundColor Gray
    
    # 1. Criar estrutura de diretórios
    Write-Host "   [1/3] Criando estrutura de diretórios..." -ForegroundColor White
    
    foreach ($dir in $directoriesToCreate) {
        $fullPath = $dir -replace "{module_name}", $moduleName
        $dirPath = Join-Path $modulePath $fullPath
        
        if (-not (Test-Path $dirPath)) {
            New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        }
    }
    
    Write-Host "   [2/3] Criando arquivos de configuração..." -ForegroundColor White
    
    # 2. Copiar templates de arquivos de configuração
    foreach ($file in $filesToCopy) {
        $sourceFile = Join-Path $templatePath $file
        $destFile = Join-Path $modulePath $file
        
        if (Test-Path $sourceFile) {
            Copy-Item -Path $sourceFile -Destination $destFile -Force
            
            # Customizar conteúdo para o módulo
            $content = Get-Content -Path $destFile -Raw
            $content = $content -replace "donabedian", $moduleName
            $content = $content -replace "Donabedian", $moduleFriendlyName
            $content = $content -replace "DONABEDIAN", ($moduleFriendlyName.ToUpper())
            
            Set-Content -Path $destFile -Value $content -Force
        }
    }
    
    # 3. Criar __init__.py para cada subdiretório do módulo
    Write-Host "   [3/3] Inicializando módulo Python..." -ForegroundColor White
    
    $subdirs = @(
        "api", "database", "models", "schemas", "services", 
        "data_access", "consolidation", "events", "dashboard"
    )
    
    foreach ($subDir in $subDirs) {
        $initFile = Join-Path $modulePath "src\$moduleName\$subDir\__init__.py"
        if (-not (Test-Path $initFile)) {
            New-Item -ItemType File -Path $initFile -Force | Out-Null
            Add-Content -Path $initFile -Value "# $subDir module`n"
        }
    }
    
    # Criar __init__.py para o módulo principal
    $mainInit = Join-Path $modulePath "src\$moduleName\__init__.py"
    if (-not (Test-Path $mainInit)) {
        $initContent = @"
"""
$moduleFriendlyName - $moduleTitle
Módulo IntelliCare
"""

__version__ = "0.1.0"
__author__ = "IntelliCare Team"
__module__ = "$moduleName"
"@
        Set-Content -Path $mainInit -Value $initContent
    }
    
    Write-Host "   ✅ Módulo $moduleFriendlyName replicado com sucesso!" -ForegroundColor Green
    Write-Host ""
}

# Executar replicação para cada módulo
$totalModules = $modules.Count
$currentModule = 0

foreach ($module in $modules.GetEnumerator()) {
    $currentModule++
    $progressPercent = [math]::Round(($currentModule / $totalModules) * 100)
    
    Write-Host "[$currentModule/$totalModules] ($progressPercent%) " -ForegroundColor Yellow -NoNewline
    
    Replicate-Module -ModuleDir $module.Key -ModuleInfo $module.Value
}

Write-Host "================================" -ForegroundColor Green
Write-Host "✅ REPLICAÇÃO CONCLUÍDA!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor Yellow
Write-Host "1. Validar integridade de cada módulo"
Write-Host "2. Customizar modelos de dados específicos"
Write-Host "3. Configurar rotas da API"
Write-Host "4. Executar testes de integração"
Write-Host ""
Write-Host "Tempo estimado restante: 3.5h por módulo" -ForegroundColor Cyan
