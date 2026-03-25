# DEM-090 — Especificação Técnica

## Sequência de execução em staging

```bash
# 1. Pull
cd /opt/intellicare
git pull origin main

# 2. Aplicar migration 024 (professionals.pessoa_id)
# (via startup automático do intellicare-service OU execução manual)
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  exec intellicare-service python -c "
from db.migrator import run_migrations
run_migrations('tenant')
"

# 3. Rebuild apenas intellicare-service (--no-deps obrigatório)
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  build --no-cache --no-deps intellicare-service

docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d --no-deps intellicare-service

# 4. Aguardar healthy
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  ps intellicare-service

# 5. Smoke identity (delta DEM-087)
TOKEN=$(curl -s -X POST http://localhost:9000/auth/token \
  -d "client_id=intellicare-service&username=platform-admin&password=Admin@2025!&grant_type=password" \
  | jq -r '.access_token')

curl -s -X POST http://localhost:9000/identity/pessoas \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"cpf": "11122233344"}' | jq .

# Esperado: 200 {"pessoa_id": "...", "cpf": "11122233344"} ou 409 (idempotência)
```

## Smoke tests

```python
# test_staging_sync_2026_05_23.py

def test_migration_024_applied():
    """professionals tabela tem coluna pessoa_id UUID"""

def test_identity_jwt_fix():
    """Token válido → GET /identity/pessoas → 200 (não mais 401)"""

def test_identity_traefik_route():
    """POST https://intellicare.ia.br/api/identity/pessoas → 200 ou 409"""

def test_professional_pessoa_id_on_create():
    """Criar profissional com CPF → pessoa_id preenchido"""

def test_reconcile_endpoint():
    """POST /identity/admin/reconcile → { processed: N, errors: [] }"""

def test_admin_identity_page_200():
    """GET /admin-ui/identity → 200 (não 404)"""
```

Total esperado: 6 testes

## Deltas infra a confirmar fechados

| Delta | Fix em | Confirmação |
|-------|--------|-------------|
| JWT issuer 401 | DEM-087 | `curl localhost:9000/identity/pessoas` → 200 |
| Traefik 405 `/api/identity/*` | DEM-087 | `curl https://intellicare.ia.br/api/identity/pessoas` → 200/409 |
| Keycloak `intellicare_staging` postgres auth | DEM-087 (colateral) | Keycloak container stays healthy após 5min |
