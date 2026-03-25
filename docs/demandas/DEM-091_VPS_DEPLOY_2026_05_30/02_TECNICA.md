# DEM-091 — Spec Técnica

## Serviço alvo

`intellicare-service` (FastAPI) — único serviço que precisa ser rebuilt.

## Comandos de deploy

```bash
# No VPS — /opt/intellicare
git pull origin main

docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  build --no-cache --no-deps intellicare-service

docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d --no-deps intellicare-service
```

> ⚠️ **CRÍTICO**: sempre usar `--env-file infra/.env.staging`. Usar `infra/.env` causa modo dev silencioso — Keycloak issuer URL não é configurado corretamente.

> ⚠️ **CRÍTICO**: sempre usar `--no-deps` para não subir/reiniciar outros serviços (keycloak, postgres, redis).

## Validação pós-deploy

```bash
# Health check básico
curl -s http://localhost:9000/health | jq .

# Identity endpoint (requer token — testar sem auth deve retornar 401, não 405)
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.intellicare.ia.br/identity/pessoas \
  -H "Content-Type: application/json" \
  -d '{"cpf":"000.000.000-00"}'
# esperado: 401 (não autenticado) ou 422 (payload inválido) — NUNCA 405

# Suite completa
cd /opt/intellicare
PYTHONPATH=. pytest packages/intellicare-core/tests/test_staging_sync_2026_05_23.py -v
# esperado: 6 passed, 0 skipped
```

## Cleanup de worktrees obsoletos

```bash
# Executar no repositório local (Windows)
git worktree remove .tmp_dem082 --force
git worktree remove .tmp_staging_fix --force
git worktree prune
rmdir .tmp_push083  # diretório vazio residual
```

## Módulos carregados

`AVAILABLE_MODULES` não precisa ser definido — o módulo `identity` é carregado por padrão quando não especificado.

## Migration 024

Já foi aplicada manualmente em staging durante a Sprint 2026-05-23. Não precisa reaplicar. Verificar:

```bash
docker exec intellicare-postgres psql -U intellicare_staging intellicare_staging \
  -c "\d professionals" | grep pessoa_id
# esperado: pessoa_id | uuid | YES
```

## Variáveis críticas em `.env.staging`

| Variável | Valor esperado | Observação |
|----------|---------------|------------|
| `KEYCLOAK_ISSUER_URL` | `https://auth.intellicare.ia.br/realms/intellicare` | Validação JWT — separado de `KEYCLOAK_URL` |
| `KEYCLOAK_URL` | `http://keycloak:8080` | Chamadas internas |
| `DATABASE_URL` | `postgresql://intellicare_staging:...@postgres:5432/intellicare_staging` | |
