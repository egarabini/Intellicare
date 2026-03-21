---
tipo: especificacao-tecnica
demanda: DEM-065
titulo: Multi-tenant Avançado
---

# DEM-065 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `packages/intellicare-core/intellicare_core/tenant_provisioner.py` | **Novo** | Orquestra schema + migrations + Keycloak |
| `packages/intellicare-core/intellicare_core/middleware/tenant_guard.py` | **Novo** | Middleware 403 para tenants suspensos |
| `migrations/015_tenant_config.sql` | **Novo** | Tabela `platform.tenant_config` |
| `modules/admin/routes.py` | Modificar | Endpoints cross-tenant (suspend, reactivate, delete) |
| `modules/admin/schemas.py` | Modificar | `TenantConfig`, `TenantProvisionRequest`, `TenantProvisionResult` |
| `modules/admin/services.py` | Modificar | Lógica suspend/reactivate; chamar tenant_provisioner |
| `frontend/AdminUI/src/pages/TenantsManager.tsx` | **Novo** | Tabela + modal Novo Tenant + ações Suspender/Reativar |
| `tests/test_multitenant.py` | **Novo** | 5 testes unitários/integração |

---

## Migration 015 — `platform.tenant_config`

```sql
CREATE SCHEMA IF NOT EXISTS platform;

CREATE TABLE IF NOT EXISTS platform.tenant_config (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_slug   VARCHAR(64) UNIQUE NOT NULL,
    display_name  VARCHAR(255) NOT NULL,
    plan          VARCHAR(32)  DEFAULT 'standard',
    max_users     INT          DEFAULT 50,
    modules_enabled TEXT[]     DEFAULT ARRAY['florence','oswaldo','careplanner'],
    created_at    TIMESTAMPTZ  DEFAULT now(),
    suspended_at  TIMESTAMPTZ
);
```

> Schema `platform` é compartilhado — não pertence a nenhum tenant específico.

---

## `tenant_provisioner.py` — contrato

```python
@dataclass
class TenantProvisionResult:
    slug: str
    schema_created: bool
    migrations_applied: bool
    keycloak_realm_created: bool
    seed_applied: bool
    error: str | None = None

async def provision_tenant(
    slug: str,
    display_name: str,
    plan: str,
    db: AsyncSession
) -> TenantProvisionResult:
    # 1. CREATE SCHEMA IF NOT EXISTS {slug}
    # 2. Alembic upgrade head no schema novo
    # 3. Seed: módulos padrão, roles, usuário gestor inicial
    # 4. POST /admin/realms (Keycloak Admin API via httpx)
    # 5. INSERT platform.tenant_config
```

**Variáveis de ambiente necessárias:**
```
KEYCLOAK_ADMIN_URL=http://keycloak:8080
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=<senha>
```

---

## Middleware `tenant_guard.py`

```python
class TenantGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant_slug = request.state.tenant_slug  # já populado pelo TenantContext
        if tenant_slug:
            config = await get_tenant_config(tenant_slug)
            if config and config.suspended_at is not None:
                return JSONResponse(
                    {"detail": "tenant_suspended"}, status_code=403
                )
        return await call_next(request)
```

Registrar no `main.py` após o `TenantContextMiddleware`.

---

## Endpoints novos em `/admin/tenants`

| Método | Path | Auth | Descrição |
|--------|------|------|-----------|
| `GET` | `/admin/tenants` | PLATFORM_ADMIN | Lista paginada de todos os tenants |
| `GET` | `/admin/tenants/{slug}` | PLATFORM_ADMIN | Detalhes + config + stats |
| `POST` | `/admin/tenants` | PLATFORM_ADMIN | Provisiona novo tenant |
| `PUT` | `/admin/tenants/{slug}/config` | PLATFORM_ADMIN | Altera plan, max_users, modules |
| `POST` | `/admin/tenants/{slug}/suspend` | PLATFORM_ADMIN | Seta `suspended_at = now()` |
| `POST` | `/admin/tenants/{slug}/reactivate` | PLATFORM_ADMIN | Limpa `suspended_at` |
| `DELETE` | `/admin/tenants/{slug}` | PLATFORM_ADMIN | Soft delete (não apaga schema) |

**Diferença de roles:**
- `TENANT_ADMIN` — admin de uma clínica específica (já existe)
- `PLATFORM_ADMIN` — acesso cross-tenant (novo claim Keycloak)

---

## `TenantsManager.tsx` — estrutura

```tsx
// Colunas da tabela
columns: slug | display_name | plan | active_users | modules | status (badge) | created_at | ações

// Badge de status
"active"       → verde   (suspended_at IS NULL)
"suspended"    → vermelho (suspended_at IS NOT NULL)
"provisioning" → amarelo  (durante POST em andamento)

// Modal "Novo Tenant"
campos: slug (validação: lowercase, sem espaços), display_name, plan (select: standard | premium | enterprise)
```

---

## Dependências

- `httpx` — já presente (chamadas Keycloak Admin API)
- `alembic` — já presente (migrations automáticas no novo schema)
- Keycloak Admin API acessível via `KEYCLOAK_ADMIN_URL` interno Docker
