# DEM-091 — Plano de Execução

> ⚠️ **Processo obrigatório**: criar `04_DIARIO.md` durante a execução e `05_FINALIZACAO.md` ao entregar. O ARQUITETO só registra o hash no dashboard quando ambos existirem com conteúdo real.

## Pré-requisitos

- [ ] Acesso SSH ao VPS (`/opt/intellicare`)
- [ ] `origin/main` já contém `0eae002` (hotfix DEM-089 — confirmar com `git log origin/main --oneline -3`)
- [ ] Migration 024 já aplicada em staging (validar antes de subir)

## Passos

### Passo 1 — Pull origin/main

```bash
cd /opt/intellicare
git status          # garantir working tree limpo
git pull origin main
git log --oneline -5  # confirmar que 0eae002 está no HEAD
```

### Passo 2 — Rebuild intellicare-service

```bash
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  build --no-cache --no-deps intellicare-service
```

Tempo esperado: 3–8 minutos (pip install + compilação).

### Passo 3 — Up do serviço

```bash
docker compose --env-file infra/.env.staging -f infra/docker-compose.yml \
  up -d --no-deps intellicare-service

# Aguardar healthy
docker ps | grep intellicare-service
# esperado: Up X seconds (healthy)
```

### Passo 4 — Validação rápida (sem auth)

```bash
# Deve retornar 401 ou 422 — NUNCA 405
curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.intellicare.ia.br/identity/pessoas \
  -H "Content-Type: application/json" -d '{}'
```

### Passo 5 — Suite completa

```bash
PYTHONPATH=. pytest packages/intellicare-core/tests/test_staging_sync_2026_05_23.py -v
```

Resultado esperado: **6 passed, 0 skipped, 0 failed**.

### Passo 6 — Cleanup worktrees (local Windows)

```bash
git worktree remove .tmp_dem082 --force
git worktree remove .tmp_staging_fix --force
git worktree prune
rmdir .tmp_push083
```

## Gotchas

- Se `git pull` der conflito: não resolver na main do VPS — verificar o estado do repositório com o ARQUITETO
- Se pytest ainda retornar skips: verificar `KEYCLOAK_ISSUER_URL` no `.env.staging` do VPS
- 405 persiste após deploy: checar `docker logs intellicare-service --tail 50` — pode indicar startup failure
- Não usar `docker compose up -d` sem `--no-deps`: pode reiniciar Keycloak e causar instabilidade
