param(
    [switch]$Recreate
)

$modules = @(
    "intellicare-oswaldo",
    "intellicare-florence",
    "intellicare-geralda",
    "intellicare-nise",
    "intellicare-zilda",
    "intellicare-grahame"
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== IntelliCare Demo - Setup Python Virtual Environments ==="
Write-Host ""

foreach ($module in $modules) {
    $modulePath = Join-Path $root $module
    $dotVenv = Join-Path $modulePath ".venv"
    $venv = Join-Path $modulePath "venv"
    $dotVenvPython = Join-Path $dotVenv "Scripts\\python.exe"
    $venvPython = Join-Path $venv "Scripts\\python.exe"

    if (!(Test-Path $modulePath)) {
        Write-Host "[WARN] $module not found. Skipping."
        continue
    }

    if ($Recreate -and (Test-Path $dotVenv)) {
        Remove-Item -Recurse -Force $dotVenv
    }

    if (Test-Path $dotVenvPython) {
        Write-Host "[OK]   $module -> .venv already exists"
        continue
    }

    if (Test-Path $venvPython) {
        Write-Host "[OK]   $module -> venv already exists"
        continue
    }

    Write-Host "[INFO] $module -> creating .venv"
    Push-Location $modulePath
    try {
        python -m venv .venv
        if (Test-Path $dotVenvPython) {
            Write-Host "[OK]   $module -> .venv created"
        } else {
            Write-Host "[FAIL] $module -> .venv not created"
        }
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Done."
