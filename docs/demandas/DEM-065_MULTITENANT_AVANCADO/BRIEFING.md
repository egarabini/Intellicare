# DEM-065 — Multi-tenant Avançado

**Sprint:** 2026-04-18
**Dev:** DEV-1
**Estimativa:** ~4h
**Prioridade:** Alta — fundação para onboarding self-service de novas clínicas

---

## Objetivo

Hoje o IntelliCare V3 já usa schema-per-tenant no PostgreSQL, mas o ciclo de criação de um novo tenant exige intervenção manual (SQL direto, seed manual, configuração no Keycloak via Admin UI). Esta DEM automatiza esse ciclo e adiciona capacidades de administração cross-tenant pelo `platform-admin`.

---

## Escopo

### 1. API de provisionamento de tenant (`/admin/tenants`)

Endpoint existente `POST /admin/tenants` deve ser estendido para executar automaticamente:

```python
# packages/intellicare-core/intellicare_core/tenant_provisioner.py (novo)

async def provision_tenant(slug: str, display_name: str, db):
    """
    1. Cria schema PostgreSQL: CREATE SCHEMA IF NOT EXISTS {slug}
    2. Roda migrations Alembic no schema novo
    3. Executa seed básico (módulos padrão, roles, usuário gestor inicial)
    4. Cria realm + client no Keycloak via API Admin
    5. Retorna TenantProvisionResult com status de cada etapa
    """
```

**Variáveis necessárias no `.env`:**
```
KEYCLOAK_ADMIN_URL=http://keycloak:8080
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=<senha>
```

### 2. Migration 015 — tabela `tenant_config`

```sql
CREATE TABLE IF NOT EXISTS platform.tenant_config (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_slug VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    plan        VARCHAR(32) DEFAULT 'standard',   -- standard | premium | enterprise
    max_users   INT DEFAULT 50,
    modules_enabled TEXT[] DEFAULT ARRAY['florence','oswaldo','careplanner'],
    created_at  TIMESTAMPTZ DEFAULT now(),
    suspended_at TIMESTAMPTZ
);
```

> Schema `platform` — compartilhado entre todos os tenants, para metadados globais.

### 3. Cross-tenant admin — endpoints

```
GET  /admin/tenants                     → lista paginada (todos os tenants)
GET  /admin/tenants/{slug}              → detalhes + config + estatísticas
POST /admin/tenants                     → provisiona novo tenant (usa tenant_provisioner)
PUT  /admin/tenants/{slug}/config       → altera plan, max_users, modules_enabled
POST /admin/tenants/{slug}/suspend      → seta suspended_at, bloqueia logins
POST /admin/tenants/{slug}/reactivate   → limpa suspended_at
DELETE /admin/tenants/{slug}            → soft delete (não apaga schema)
```

Todos os endpoints exigem role `PLATFORM_ADMIN` (não `TENANT_ADMIN`).

### 4. AdminUI — página `TenantsManager`

Componente React `frontend/AdminUI/src/pages/TenantsManager.tsx`:

- Tabela de tenants com colunas: slug, nome, plano, usuários ativos, módulos, status, data criação
- Botão **Novo Tenant** → modal com campos `slug`, `display_name`, `plan`
- Ação **Suspender / Reativar** por linha
- Badge colorido: `active` (verde) / `suspended` (vermelho) / `provisioning` (amarelo)

### 5. Proteção de rotas por tenant suspenso

Middleware FastAPI: se `tenant_config.suspended_at IS NOT NULL`, retornar `403 {"detail": "tenant_suspended"}` para qualquer requisição autenticada desse tenant.

```python
# packages/intellicare-core/intellicare_core/middleware/tenant_guard.py
```

---

## Testes esperados (mínimo 4)

```python
# tests/test_multitenant.py

test_provision_tenant_creates_schema()       # POST /admin/tenants → schema criado
test_provision_tenant_runs_migrations()      # migrations executadas no novo schema
test_suspend_tenant_blocks_requests()        # 403 após suspensão
test_reactivate_tenant_restores_access()     # 200 após reativação
test_cross_tenant_isolation()               # tenant A não acessa dados do tenant B
```

---

## Arquivos a criar/modificar

```
packages/intellicare-core/intellicare_core/
├── tenant_provisioner.py          (novo)
├── middleware/
│   └── tenant_guard.py            (novo)
modules/admin/
├── routes.py                      (adicionar endpoints cross-tenant)
├── schemas.py                     (TenantConfig, TenantProvisionRequest)
└── services.py                    (lógica suspend/reactivate)
migrations/
└── 015_tenant_config.sql          (novo)
frontend/AdminUI/src/pages/
└── TenantsManager.tsx             (novo)
```

---

## Dependências

- Keycloak Admin API deve estar acessível via `KEYCLOAK_ADMIN_URL` (já no docker-compose)
- `httpx` (já presente) para chamadas à API Keycloak
- Schema `platform` pode não existir — `tenant_provisioner` deve criá-lo se necessário

---

## Critério de aceite

1. `POST /admin/tenants {"slug": "clinica-beta", "display_name": "Clínica Beta"}` cria schema `clinica_beta` no PostgreSQL com migrations aplicadas
2. Login como usuário do tenant `clinica-beta` funciona no ClinicoUI
3. `POST /admin/tenants/clinica-beta/suspend` → requisições subsequentes do tenant retornam `403`
4. 4/4 testes passando
5. Página `TenantsManager` lista tenants e permite provisionar novo via modal
