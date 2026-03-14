#!/usr/bin/env bash
# run_e2e.sh — Executa suite E2E completa
# Uso: ./tools/scripts/run_e2e.sh
set -euo pipefail

echo "=== IntelliCare V3 — Teste E2E ==="

# 1. Verificar que docker-compose está rodando
echo "Verificando serviços..."
docker compose -f infra/docker-compose.yml ps --quiet || {
    echo "ERRO: docker-compose não está rodando. Execute: docker compose -f infra/docker-compose.yml up -d"
    exit 1
}

# 2. Aguardar health da API
echo "Aguardando API..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo "API pronta."
        break
    fi
    echo "  Aguardando... ($i/30)"
    sleep 2
done

# 3. Setup Keycloak (idempotente)
echo "Configurando Keycloak..."
python tools/scripts/setup_keycloak.py

# 4. Rodar testes E2E
echo "Executando testes E2E..."
pytest tests/e2e/ \
    -m e2e \
    -v \
    --tb=short \
    --cov=intellicare_core \
    --cov=modules \
    --cov-report=term-missing \
    --cov-fail-under=70

echo "=== Todos os testes E2E passaram ==="

