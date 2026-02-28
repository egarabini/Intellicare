# IntelliCare . - Development Environment Installation
# This script installs all Python modules and frontend dependencies

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "IntelliCare . - Installation Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$modules = @(
    "intellicare-core",
    "intellicare-auth",
    "intellicare-admin",
    "intellicare-florence",
    "intellicare-oswaldo",
    "intellicare-donabedian",
    "intellicare-wanda",
    "intellicare-comunicacao",
    "intellicare-geralda",
    "intellicare-zilda",
    "intellicare-ocr",
    "intellicare-pierre",
    "intellicare-nise",
    "intellicare-grahame",
    "intellicare-gestor"
)

# Track installation status
$installed = @()
$failed = @()
$skipped = @()

Write-Host "[1/3] Installing Intellicare Core (shared SDK)..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow

if (Test-Path "intellicare-core") {
    Push-Location intellicare-core
    Write-Host "Creating virtual environment for intellicare-core..." -ForegroundColor Cyan
    python -m venv .venv
    if ($? -eq $true) {
        Write-Host "Virtual environment created" -ForegroundColor Green
        Write-Host "Installing intellicare-core with dev dependencies..." -ForegroundColor Cyan
        & ".\.venv\Scripts\Activate.ps1"
        pip install -e ".[dev]" --quiet
        if ($? -eq $true) {
            Write-Host "Successfully installed intellicare-core" -ForegroundColor Green
            $installed += "intellicare-core"
        } else {
            Write-Host "Failed to install intellicare-core" -ForegroundColor Red
            $failed += "intellicare-core"
        }
        deactivate
    } else {
        Write-Host "Failed to create virtual environment" -ForegroundColor Red
        $failed += "intellicare-core"
    }
    Pop-Location
} else {
    Write-Host "intellicare-core directory not found" -ForegroundColor Red
    $failed += "intellicare-core"
}

Write-Host ""
Write-Host "[2/3] Installing agent modules..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow

foreach ($module in $modules) {
    if ($module -eq "intellicare-core" -or $module -eq "intellicare-auth") {
        continue
    }

    if (-not (Test-Path $module)) {
        Write-Host "$module - directory not found, skipping" -ForegroundColor DarkYellow
        $skipped += $module
        continue
    }

    Write-Host "`nInstalling $module..." -ForegroundColor Cyan
    Push-Location $module

    if (-not (Test-Path "pyproject.toml")) {
        Write-Host "No pyproject.toml found, skipping" -ForegroundColor DarkYellow
        $skipped += $module
        Pop-Location
        continue
    }

    Write-Host "  Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv

    if ($? -eq $true) {
        & ".\.venv\Scripts\Activate.ps1"
        Write-Host "  Installing with pip..." -ForegroundColor Cyan
        pip install -e ".[dev]" --quiet

        if ($? -eq $true) {
            Write-Host "  Successfully installed $module" -ForegroundColor Green
            $installed += $module
        } else {
            Write-Host "  Failed to install $module" -ForegroundColor Red
            $failed += $module
        }

        deactivate
    } else {
        Write-Host "  Failed to create virtual environment" -ForegroundColor Red
        $failed += $module
    }

    Pop-Location
}

Write-Host ""
Write-Host "[3/3] Installing frontend (intellicare-portal)..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow

if (Test-Path "intellicare-portal\frontend") {
    Push-Location intellicare-portal\frontend
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Cyan
    npm install --silent
    if ($? -eq $true) {
        Write-Host "Frontend dependencies installed successfully" -ForegroundColor Green
        $installed += "intellicare-portal (frontend)"
    } else {
        Write-Host "Failed to install frontend dependencies" -ForegroundColor Red
        $failed += "intellicare-portal (frontend)"
    }
    Pop-Location
} else {
    Write-Host "intellicare-portal/frontend directory not found" -ForegroundColor DarkYellow
    $skipped += "intellicare-portal (frontend)"
}

# Installation Summary
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
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Start infrastructure services:" -ForegroundColor White
Write-Host "   docker compose up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Run a specific module (example):" -ForegroundColor White
Write-Host "   cd intellicare-wanda" -ForegroundColor Cyan
Write-Host "   .\.venv\Scripts\activate" -ForegroundColor Cyan
Write-Host "   uvicorn wanda.api.app:app --reload --port 8004" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Run all services with Docker:" -ForegroundColor White
Write-Host "   docker compose -f docker-compose.full.yml up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Run frontend:" -ForegroundColor White
Write-Host "   cd intellicare-portal\frontend" -ForegroundColor Cyan
Write-Host "   npm run dev" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Run smoke tests:" -ForegroundColor White
Write-Host "   python scripts/smoke_tests.py" -ForegroundColor Cyan
Write-Host ""
