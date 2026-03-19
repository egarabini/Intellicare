#!/usr/bin/env bash
# deploy/staging_update.sh
# Atualiza ambiente de staging com impacto minimo.
# Uso:
#   STAGING_ENV_FILE=infra/.env.staging bash deploy/staging_update.sh

set -euo pipefail

ENV_FILE="${STAGING_ENV_FILE:-infra/.env.staging}"
COMPOSE_FILE="infra/docker-compose.yml"
COMPOSE_CMD=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

seed_kestra_flows() {
  local flow_path

  for flow_path in infra/kestra/flows/*.yml; do
    [[ -f "$flow_path" ]] || continue

    echo "   -> $(basename "$flow_path")"
    cat "$flow_path" | "${COMPOSE_CMD[@]}" exec -T intellicare-service python -c '
import os
import sys

import httpx

flow_yaml = sys.stdin.read()
kestra_url = os.getenv("KESTRA_URL", "http://kestra:8080").rstrip("/")
response = httpx.post(
    f"{kestra_url}/api/v1/flows",
    content=flow_yaml,
    headers={"Content-Type": "application/x-yaml"},
    timeout=30,
)
print(f"HTTP {response.status_code}")
raise SystemExit(0 if response.status_code in (200, 201) else 1)
'
  done
}

echo "======================================"
echo " IntelliCare Staging Update"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================"

echo ""
echo "==> [1/7] Validando pre-requisitos..."
[[ -f "$ENV_FILE" ]] || { echo "ERRO: arquivo $ENV_FILE nao encontrado"; exit 1; }
[[ -f "$COMPOSE_FILE" ]] || { echo "ERRO: arquivo $COMPOSE_FILE nao encontrado"; exit 1; }
command -v git >/dev/null || { echo "ERRO: git nao encontrado"; exit 1; }
command -v docker >/dev/null || { echo "ERRO: docker nao encontrado"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERRO: docker compose nao encontrado"; exit 1; }

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERRO: repositorio com alteracoes locais. Limpe o working tree antes do deploy."
  git status --short
  exit 1
fi
echo "OK: pre-requisitos validados."

echo ""
echo "==> [2/7] Atualizando codigo..."
git pull --ff-only origin main
echo "OK: HEAD $(git rev-parse --short HEAD)"

echo ""
echo "==> [3/7] Build do servico principal..."
"${COMPOSE_CMD[@]}" build --no-cache intellicare-service
echo "OK: build concluido."

echo ""
echo "==> [4/7] Restart seletivo (sem down global)..."
"${COMPOSE_CMD[@]}" up -d --no-deps intellicare-service

echo ""
echo "==> [5/7] Aguardando inicializacao (30s)..."
sleep 30

echo ""
echo "==> [6/7] Seed dos flows Kestra..."
seed_kestra_flows || echo "AVISO: seed dos flows Kestra falhou (Kestra pode estar inicializando)."

echo ""
echo "==> [7/7] Status final dos servicos..."
"${COMPOSE_CMD[@]}" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "======================================"
echo " Deploy concluido!"
echo " Verificar:"
echo "   https://api.intellicare.ia.br/health"
echo "   https://gestor.intellicare.ia.br/gestor-ui/"
echo "   https://kestra.intellicare.ia.br"
echo "======================================"
