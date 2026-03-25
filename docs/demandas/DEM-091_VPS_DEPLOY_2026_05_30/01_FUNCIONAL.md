# DEM-091 — VPS Deploy 2026-05-30

## Objetivo

Sincronizar o VPS de staging (`api.intellicare.ia.br`) com o estado atual de `origin/main` e validar os 6 smoke tests da DEM-090 que foram ignorados por conta do Keycloak restart loop.

## Contexto

- Sprint 2026-05-23 encerrada com `0eae002` (hotfix DEM-089 list_tenants)
- Keycloak fix: causa raiz resolvida — `intellicare-service` estava usando `infra/.env` em vez de `infra/.env.staging`
- `localhost:9000/identity/pessoas → 201` funciona localmente
- VPS ainda retorna 405 em todos os endpoints `/identity/*` porque não recebeu o pull

## Critério de aceite

1. VPS executando `origin/main` com `--env-file infra/.env.staging`
2. `intellicare-service` healthy e respondendo na porta 8000
3. `POST https://api.intellicare.ia.br/identity/pessoas` → 201 (com token válido)
4. `GET https://api.intellicare.ia.br/identity/admin/stats` → 200
5. Suite completa sem skips: `pytest packages/intellicare-core/tests/test_staging_sync_2026_05_23.py` → **6/6 passed**
6. Nenhum worktree obsoleto pendente no repositório

## Fora de escopo

- Novos endpoints ou features
- Alterações de código — deploy apenas
