#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
UI_DIR="$ROOT_DIR/frontend/GestorUI"
OUT_DIR="$ROOT_DIR/packages/intellicare-core/intellicare_core/static/gestor-ui"

echo "==> Instalando dependencias..."
cd "$UI_DIR"
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

echo "==> Gerando build de producao..."
npm run build

echo "==> Artefato em: $OUT_DIR"
ls -lh "$OUT_DIR"
