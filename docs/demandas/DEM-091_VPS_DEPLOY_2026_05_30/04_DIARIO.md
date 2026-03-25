# DEM-091 — Diário de Execução

> Dev: DEV-1 | Data: 2026-03-25

## Execução

### Passo 1 — Estado inicial do VPS

VPS estava com rebase em andamento e branch divergida (1 commit local vs 9 remotos). Situação detectada antes do pull.

**Decisão:** Cancelar rebase e fazer reset hard para `origin/main` — correto para deploy target puro conforme alinhado com ARQUITETO.

```bash
git rebase --abort
git fetch origin
git reset --hard origin/main
```

### Passos 2–5 — Deploy normal

Rebuild e up do `intellicare-service` com `--env-file infra/.env.staging` e `--no-deps` conforme plano. Serviço subiu healthy.

Pytest executado: **6/6 passed** (sem skips).

### Passo 6 — Cleanup worktrees

| Worktree | Resultado |
|----------|-----------|
| `.tmp_dem082` | ✅ Removido |
| `.tmp_push083` | ✅ Removido |
| `.tmp_staging_fix` | ✅ Referência git removida (`worktree prune`). Diretório físico persiste com ~28 junction points de pytest-cache que requerem elevação de admin para deletar. |

`git worktree list` está limpo: `main`, `develop`, `DEM-007_KEYCLOAK_AUTH_FIX`, `dem023-staging` (locked).

## Adaptações ao plano

Nenhuma adaptação de código — deploy puro. A única variação foi a necessidade de `git rebase --abort` + `reset --hard` em vez de `git pull` direto, por causa do estado divergido do VPS.

## Pendência residual

`.tmp_staging_fix` — diretório físico em `C:\Users\egara\INTELLICARE\.tmp_staging_fix`. Requer PowerShell elevado (admin):
```powershell
Remove-Item -Path "C:\Users\egara\INTELLICARE\.tmp_staging_fix" -Recurse -Force
```
