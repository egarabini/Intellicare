# DEM-065 — Multi-tenant Avançado — FINALIZAÇÃO

**Data de entrega:** 2026-03-21
**Dev responsável:** DEV-1
**Commit final:** `683c0f9`
**Sprint:** 2026-04-18
**Arquivos alterados:** 12 | **Inserções:** 1.180 linhas

---

## Resumo da entrega

Ciclo completo de provisionamento de tenant automatizado — schema PostgreSQL, migrations Alembic, Keycloak realm/client e seed básico criados por um único `POST /admin/tenants`. Controles de ciclo de vida (suspend/reactivate/soft-delete) gerenciáveis pelo `platform-admin` via AdminUI.

---

## O que foi entregue

| Camada | Arquivo | Descrição |
|--------|---------|-----------|
| DB | `015_tenant_config.sql` | Tabela `platform.tenant_config` com plano, módulos, timestamps |
| Backend | `tenant_provisioner.py` | Schema + Alembic programático + Keycloak API seed |
| Middleware | `tenant_guard.py` | ASGI 403 para tenants suspensos |
| Service | `service.py` | suspend / reactivate / soft-delete / config CRUD |
| Router | `router.py` | 6 endpoints cross-tenant (`/admin/tenants/*`) |
| Schemas | `schemas.py` | `TenantProvisionRequest`, `TenantConfigItem`, `TenantConfigResponse` |
| Frontend | `TenantsManager.tsx` | Tabela paginada, badge status, ações Suspender/Reativar |
| Frontend | `TenantConfigPage.tsx` | Edição de plano, max_users, módulos ativos *(bônus)* |
| Testes | `test_multitenant_advanced.py` | **16 testes passando** |

---

## Além do escopo original

- `TenantConfigPage.tsx` — página dedicada para editar configurações de tenant (plano, módulos ativos, max_users) não estava no BRIEFING, entregue como bônus
- 16 testes vs mínimo de 4 especificado

---

## Endpoints entregues

```
GET    /admin/tenants                    → lista paginada todos os tenants
GET    /admin/tenants/{slug}             → detalhes + config
POST   /admin/tenants                    → provisiona novo tenant
PUT    /admin/tenants/{slug}/config      → altera plan / max_users / modules
POST   /admin/tenants/{slug}/suspend     → seta suspended_at
POST   /admin/tenants/{slug}/reactivate  → limpa suspended_at
```

---

## Impacto em DEM-068

DEV-3/4 deve validar no staging:
- `POST /admin/tenants` provisiona `clinica-smoke` com schema criado
- `POST /admin/tenants/clinica-smoke/suspend` → requisições do tenant retornam 403
- Variáveis `KEYCLOAK_ADMIN_URL`, `KEYCLOAK_ADMIN_USER`, `KEYCLOAK_ADMIN_PASSWORD` devem estar no `.env.staging`
