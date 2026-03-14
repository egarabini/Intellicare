#!/usr/bin/env bash
set -euo pipefail

UI_DIR="$(git rev-parse --show-toplevel)/frontend/ClinicoUI"
OUT_DIR="$(git rev-parse --show-toplevel)/packages/intellicare-core/intellicare_core/static/clinico-ui"

echo "==> Instalando dependências..."
cd "$UI_DIR"
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi

echo "==> Gerando build de produção..."
npm run build

echo "==> Artefato em: $OUT_DIR"
ls -lh "$OUT_DIR"
