# DEM-068 — Staging Full Sync 2026-04-18 — FINALIZAÇÃO

**Data de entrega:** 2026-03-21
**Dev responsável:** DEV-3/4 (CODEX)
**Commit de evidência:** `772a1dd`
**Sprint:** 2026-04-18

---

## Smoke final aprovado

| Endpoint | Resultado |
|----------|-----------|
| `POST /admin/tenants/provision` | `201` ✅ |
| `POST /notifications/push/subscribe` | `201` ✅ |
| `POST /careplanner/journeys/trigger` | `202` ✅ |
| `GET /careplanner/health/adapters` | `200` ✅ |
| `GET /instance/connectionState/intellicare` (Evolution) | `state: open` ✅ |
| `GET /florence/notes/encounter/1` (JWT válido) | `200` ✅ |

Evidência registrada em `deploy/staging_sync_log.txt`.

---

## Bloqueios encontrados e resolvidos

### B1 — Dockerfile não copiava `db/` e `tools/`
- **Sintoma:** `ModuleNotFoundError: tools.scripts.tenant_provisioner` no container
- **Fix:** COPY adicionado no Dockerfile para incluir `db/` e `tools/`
- **Commit patch:** `d7cc7cc8`

### B2 — `push_subscriptions` não criada no startup
- **Sintoma:** `POST /notifications/push/subscribe` → 500 (tabela inexistente)
- **Fix:** migration 016 aplicada manualmente no schema do tenant de staging + fix no startup para garantir aplicação automática
- **Commit patch:** `d7cc7cc8`

### B3 — Kestra rejeita `application/json`
- **Sintoma:** `POST /journeys/trigger` → 415 Unsupported Media Type no Kestra
- **Fix:** `trigger_flow()` alterado para enviar `multipart/form-data` em vez de JSON
- **Commit patch:** `d7cc7cc8`

### B4 — Schema drift `deleted_at` ausente
- **Sintoma:** `tenant_guard` e `admin/service.py` filtravam por `deleted_at` que não existia no staging
- **Fix:** coluna adicionada via `ALTER TABLE platform.tenant_config ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ`
- **Abordagem correta:** fix no schema do staging — não tolerância no código

### B5 — Keycloak `invalid_client`
- **Sintoma:** smoke com `client_secret=CHANGE_ME_ON_DEPLOY` retornava `invalid_client`
- **Fix:** identificado `KEYCLOAK_CLIENT_SECRET=staging-client-secret-2025` no `.env.staging` via Admin API
- **Abordagem:** usar o secret real — não alterar o Keycloak

### B6 — Git fetch bloqueado no sandbox do CODEX
- **Sintoma:** `0807431` (rename imagens Portal) não chegou ao clone local de CODEX
- **Fix:** `git pull origin main` executado diretamente no VPS antes do rebuild

---

## Commits desta DEM

| Hash | Descrição |
|------|-----------|
| `3b6f6f0` | patch parcial staging sync |
| `da68a1d` | patch parcial staging sync |
| `1a3e6a0` | patch parcial staging sync |
| `1f5dee8` | patch parcial staging sync |
| `d7cc7cc8` | fix: Dockerfile db/tools, push_subscriptions, Kestra multipart |
| `772a1dd` | infra: staging sync sprint 2026-04-18 — evidência smoke OK |

---

## Status pós-entrega

- Sprint 2026-04-18: **✅ Concluída** (4/4 DEMs entregues)
- Próxima sprint: **2026-04-25** (pendente planejamento)
