#!/bin/bash
# IntelliCare . - Development Environment Installation
# This script installs all Python modules and frontend dependencies

set -e

echo "================================================"
echo "IntelliCare . - Installation Script"
echo "================================================"
echo ""

MODULES=(
    "intellicare-core"
    "intellicare-auth"
    "intellicare-admin"
    "intellicare-florence"
    "intellicare-oswaldo"
    "intellicare-donabedian"
    "intellicare-wanda"
    "intellicare-comunicacao"
    "intellicare-geralda"
    "intellicare-zilda"
    "intellicare-ocr"
    "intellicare-pierre"
    "intellicare-nise"
    "intellicare-grahame"
    "intellicare-gestor"
)

# Track installation status
INSTALLED=()
FAILED=()
SKIPPED=()

echo "[1/3] Installing Intellicare Core (shared SDK)..."
echo "----------------------------------------"

if [ -d "intellicare-core" ]; then
    cd intellicare-core
    echo "Creating virtual environment for intellicare-core..."
    python -m venv .venv && \
    source .venv/Scripts/activate && \
    echo "Installing intellicare-core with dev dependencies..." && \
    pip install -e ".[dev]" -q && \
    echo "✓ intellicare-core installed successfully" && \
    INSTALLED+=("intellicare-core") && \
    deactivate
    cd ..
else
    echo "✗ intellicare-core directory not found"
    FAILED+=("intellicare-core")
fi

echo ""
echo "[2/3] Installing agent modules..."
echo "----------------------------------------"

for MODULE in "${MODULES[@]}"; do
    if [ "$MODULE" = "intellicare-core" ] || [ "$MODULE" = "intellicare-auth" ]; then
        continue
    fi

    if [ ! -d "$MODULE" ]; then
        echo "⊘ $MODULE - directory not found, skipping"
        SKIPPED+=("$MODULE")
        continue
    fi

    echo ""
    echo "Installing $MODULE..."
    cd "$MODULE"

    if [ ! -f "pyproject.toml" ]; then
        echo "⊘ No pyproject.toml found, skipping"
        SKIPPED+=("$MODULE")
        cd ..
        continue
    fi

    echo "  Creating virtual environment..."
    if python -m venv .venv; then
        source .venv/Scripts/activate

        # Check if it uses poetry or setuptools
        if grep -q 'build-backend.*poetry' pyproject.toml; then
            echo "  Detected Poetry build system, installing with pip..."
        else
            echo "  Installing with pip..."
        fi

        if pip install -e ".[dev]" -q; then
            echo "  ✓ $MODULE installed successfully"
            INSTALLED+=("$MODULE")
        else
            echo "  ✗ Failed to install $MODULE"
            FAILED+=("$MODULE")
        fi

        deactivate
    else
        echo "  ✗ Failed to create virtual environment"
        FAILED+=("$MODULE")
    fi

    cd ..
done

echo ""
echo "[3/3] Installing frontend (intellicare-portal)..."
echo "----------------------------------------"

if [ -d "intellicare-portal/frontend" ]; then
    cd intellicare-portal/frontend
    echo "Installing Node.js dependencies..."
    if npm install --silent; then
        echo "✓ Frontend dependencies installed successfully"
        INSTALLED+=("intellicare-portal (frontend)")
    else
        echo "✗ Failed to install frontend dependencies"
        FAILED+=("intellicare-portal (frontend)")
    fi
    cd ../..
else
    echo "⊘ intellicare-portal/frontend directory not found"
    SKIPPED+=("intellicare-portal (frontend)")
fi

# Installation Summary
echo ""
echo "================================================"
echo "Installation Summary"
echo "================================================"
echo ""

if [ ${#INSTALLED[@]} -gt 0 ]; then
    echo "Successfully installed (${#INSTALLED[@]}):"
    for item in "${INSTALLED[@]}"; do
        echo "  ✓ $item"
    done
fi

if [ ${#SKIPPED[@]} -gt 0 ]; then
    echo ""
    echo "Skipped (${#SKIPPED[@]}):"
    for item in "${SKIPPED[@]}"; do
        echo "  ⊘ $item"
    done
fi

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "Failed (${#FAILED[@]}):"
    for item in "${FAILED[@]}"; do
        echo "  ✗ $item"
    done
fi

echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo ""
echo "1. Start infrastructure services:"
echo "   docker compose up -d"
echo ""
echo "2. Run a specific module (example):"
echo "   cd intellicare-wanda"
echo "   source .venv/bin/activate"
echo "   uvicorn wanda.api.app:app --reload --port 8004"
echo ""
echo "3. Run all services with Docker:"
echo "   docker compose -f docker-compose.full.yml up -d"
echo ""
echo "4. Run frontend:"
echo "   cd intellicare-portal/frontend"
echo "   npm run dev"
echo ""
echo "5. Run smoke tests:"
echo "   python scripts/smoke_tests.py"
echo ""
