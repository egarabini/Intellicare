#!/usr/bin/env bash
set -euo pipefail

UI_DIR="$(git rev-parse --show-toplevel)/frontend/Portal"
OUT_DIR="$(git rev-parse --show-toplevel)/packages/intellicare-core/intellicare_core/static/portal"

echo "==> Instalando dependências..."
cd "$UI_DIR"
npm ci

echo "==> Gerando build de produção..."
npm run build

echo "==> Bundle size:"
du -sh "$OUT_DIR"
