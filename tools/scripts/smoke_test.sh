#!/usr/bin/env bash
# IntelliCare V3 - Smoke test do ambiente de desenvolvimento
# Uso: bash tools/scripts/smoke_test.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}OK${NC} $1"; }
fail() { echo -e "${RED}FAIL${NC} $1"; exit 1; }

echo "IntelliCare V3 - Smoke Test"
echo "================================"

docker exec intellicare-postgres pg_isready -h localhost -p 5432 -U intellicare -d intellicare >/dev/null 2>&1 \
    && pass "PostgreSQL: respondendo" \
    || fail "PostgreSQL: nao responde"

docker exec -e PGPASSWORD=intellicare_dev_password intellicare-postgres \
psql -h localhost -U intellicare -d intellicare -tAc \
    "SELECT extname FROM pg_extension WHERE extname='vector'" 2>/dev/null \
    | grep -q vector \
    && pass "pgvector: extensao ativa" \
    || fail "pgvector: extensao NAO encontrada"

docker exec intellicare-redis redis-cli -h localhost -p 6379 -a redis_dev_password ping 2>/dev/null \
    | grep -q PONG \
    && pass "Redis: respondendo" \
    || fail "Redis: nao responde"

curl -sf http://localhost:11434/api/tags >/dev/null \
    && pass "OLLAMA: API respondendo" \
    || fail "OLLAMA: nao responde"

curl -sf http://localhost:8080 >/dev/null \
    && pass "Keycloak: respondendo" \
    || fail "Keycloak: nao responde"

curl -sf http://localhost:8090/api/version >/dev/null \
    && pass "Traefik: dashboard respondendo" \
    || fail "Traefik: nao responde"

echo ""
echo "================================"
echo "Todos os servicos OK."
