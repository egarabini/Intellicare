# IntelliCare . - Simple Installation Script for Windows
# This script installs modules that don't require C++ build tools

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "IntelliCare . - Simple Installation" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

$simpleModules = @("intellicare-core", "intellicare-auth", "intellicare-donabedian", "intellicare-wanda", "intellicare-comunicacao", "intellicare-geralda", "intellicare-zilda", "intellicare-nise", "intellicare-grahame", "intellicare-gestor", "intellicare-pierre")

$installed = @()
$failed = @()
$skipped = @()

Write-Host "[Phase 1] Installing simple modules..." -ForegroundColor Yellow
Write-Host "-----------------------------------------------------------------------" -ForegroundColor Yellow

foreach ($module in $simpleModules) {
    if (-not (Test-Path $module)) {
        Write-Host "$module - directory not found, skipping"
        $skipped += $module
        continue
    }

    if (-not (Test-Path "$module\pyproject.toml")) {
        Write-Host "$module - no pyproject.toml found, skipping"
        $skipped += $module
        continue
    }

    Write-Host "`nInstalling $module..."
    Push-Location $module

    Write-Host "  Creating virtual environment..."
    python -m venv .venv

    if ($LASTEXITCODE -eq 0) {
        & ".\.venv\Scripts\Activate.ps1"
        Write-Host "  Installing dependencies..."
        pip install -e ".[dev]"

        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Successfully installed $module"
            $installed += $module
        } else {
            Write-Host "  Failed to install $module"
            $failed += $module
        }

        deactivate
    } else {
        Write-Host "  Failed to create virtual environment"
        $failed += $module
    }

    Pop-Location
}

Write-Host ""
Write-Host "[Phase 2] Installing frontend..." -ForegroundColor Yellow
Write-Host "-----------------------------------------------------------------------" -ForegroundColor Yellow

if (Test-Path "intellicare-portal\frontend") {
    Push-Location intellicare-portal\frontend
    Write-Host "Installing Node.js dependencies..."
    npm install
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Frontend dependencies installed successfully"
        $installed += "intellicare-portal (frontend)"
    } else {
        Write-Host "Failed to install frontend dependencies"
        $failed += "intellicare-portal (frontend)"
    }
    Pop-Location
} else {
    Write-Host "intellicare-portal/frontend directory not found"
    $skipped += "intellicare-portal (frontend)"
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Installation Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($installed.Count -gt 0) {
    Write-Host "Successfully installed ($($installed.Count)):" -ForegroundColor Green
    foreach ($item in $installed) {
        Write-Host "  - $item" -ForegroundColor Green
    }
}

if ($skipped.Count -gt 0) {
    Write-Host "`nSkipped ($($skipped.Count)):" -ForegroundColor DarkYellow
    foreach ($item in $skipped) {
        Write-Host "  - $item" -ForegroundColor DarkYellow
    }
}

if ($failed.Count -gt 0) {
    Write-Host "`nFailed ($($failed.Count)):" -ForegroundColor Red
    foreach ($item in $failed) {
        Write-Host "  - $item" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Modules requiring Visual Studio C++ build tools:" -ForegroundColor Yellow
Write-Host "  - intellicare-admin" -ForegroundColor DarkYellow
Write-Host "  - intellicare-florence" -ForegroundColor DarkYellow
Write-Host "  - intellicare-oswaldo" -ForegroundColor DarkYellow
Write-Host "  - intellicare-ocr" -ForegroundColor DarkYellow
Write-Host ""
Write-Host "To install these modules, install Visual Studio 2022 Community" -ForegroundColor White
Write-Host "with 'Desktop development with C++' workload, then re-run installation." -ForegroundColor White
Write-Host ""
