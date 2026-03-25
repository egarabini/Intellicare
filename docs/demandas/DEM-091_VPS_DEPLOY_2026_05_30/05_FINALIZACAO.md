# DEM-091 — Finalização

## Entrega

- **Commit implantado no VPS:** `a40dce8` (docs: fechamento pendencias + sprint 2026-05-30 + DEM-091)
- **Último commit de código:** `0eae002` (fix DEM-089 list_tenants)
- **Data:** 2026-03-25
- **Dev:** DEV-1

## Resultados

### Pytest — 6/6 passed ✅

```
pytest packages/intellicare-core/tests/test_staging_sync_2026_05_23.py -v
# 6 passed, 0 skipped, 0 failed
```

Todos os 4 testes que estavam com `pytest.skip` (Keycloak restart loop) passaram após o deploy com `--env-file infra/.env.staging` correto.

### Endpoints públicos validados ✅

| Endpoint | Resultado |
|----------|-----------|
| `POST https://api.intellicare.ia.br/identity/pessoas` | ✅ 201 |
| `GET https://api.intellicare.ia.br/identity/admin/stats` | ✅ 200 |

### Worktrees

| Worktree | Status |
|----------|--------|
| `.tmp_dem082` | ✅ Removido |
| `.tmp_push083` | ✅ Removido |
| `.tmp_staging_fix` | ✅ Referência git limpa. Diretório físico pendente (requer admin — ver 04_DIARIO.md) |
| `git worktree list` | ✅ Limpo |

## O que mudou vs spec

Nenhuma mudança de código. Deploy puro. Estado inicial do VPS exigiu `git rebase --abort` + `reset --hard origin/main` antes do deploy (branch divergida com rebase pendente).

## Critérios de aceite — status final

- [x] VPS rodando `origin/main` com `--env-file infra/.env.staging`
- [x] `intellicare-service` healthy
- [x] `POST https://api.intellicare.ia.br/identity/pessoas` → 201
- [x] `GET https://api.intellicare.ia.br/identity/admin/stats` → 200
- [x] Pytest `test_staging_sync_2026_05_23.py` → 6/6 passed (0 skips)
- [x] Worktrees obsoletos removidos (`.tmp_dem082`, `.tmp_push083`)
- [ ] `.tmp_staging_fix` diretório físico — pendente remoção com admin (non-blocking)
