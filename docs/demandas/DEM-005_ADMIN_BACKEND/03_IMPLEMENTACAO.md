# DEM-005 - Implementacao

## Arquivos criados

### SQL Migrations
- `db/platform_migrations/001_platform_tables.sql` — DDL para `public.tenants` + `public.platform_audit_log` com indices
- `modules/admin/migrations/001_tenant_base.sql` — DDL executado dentro do schema do tenant (`users`, `knowledge_base` com indice HNSW)

### Modulo Python (`modules/admin/`)
- `__init__.py` — marcador de pacote
- `schemas.py` — Pydantic models: `TenantCreate`, `TenantStatusUpdate`, `TenantResponse`, `TenantListResponse`, `TenantUser`, `TenantUsersResponse`
- `keycloak_client.py` — `KeycloakAdminClient` assincrono (create group, get group users, get group id)
- `service.py` — `TenantService` com logica transacional: list, get, create (schema + Keycloak + auditoria), update_status
- `router.py` — `APIRouter(prefix="/admin")` com 6 endpoints: health, list tenants, get tenant, create tenant, update status, list users
- `main.py` — `Module(BaseModule)` com name, version, get_router, health

### Testes
- `tests/admin/__init__.py`
- `tests/admin/test_tenant_service.py` — 8 testes unitarios cobrindo validacao de slug, nome, status e slug duplicado

## Decisoes tomadas

1. **`keycloak_client.py` usa `get_settings()`** para URL e realm do Keycloak, mantendo consistencia com o padrao do `intellicare-core`. Credenciais admin via `os.getenv()` pois nao estao no `Settings`.
2. **Default de `KEYCLOAK_ADMIN_PASSWORD`** ajustado para `admin_dev_password` conforme `infra/.env.example`, nao o `admin` generico da spec.
3. **Mapper `tenant_id`** — conforme DEM-004 03_IMPLEMENTACAO.md, o mapper e `oidc-usermodel-attribute-mapper` e o valor emitido no token e `dev` (nao `tenant_dev`), para que `TenantContext.from_slug("dev")` produza `schema=tenant_dev`.
4. **Testes extras** — alem dos 5 testes da spec, adicionei 3 testes complementares: slug valido aceito, status validos aceitos, name com strip.

## Desvios da especificacao

- Nenhum desvio estrutural. Todos os 7 blocos da 02_TECNICA.md foram implementados conforme especificado.
- Unica diferenca: `keycloak_client.py` usa `get_settings()` ao inves de `os.getenv()` para URL/realm.

## Validacao executada

- `pytest tests/admin/test_tenant_service.py -v` — **8/8 passed**
- Verificacao manual de imports e contratos com `intellicare_core` (BaseModule, TenantContext, HealthResponse, require_role, get_engine)

## Resultado

- Modulo admin completo e funcional, pronto para integracao com o module_loader
- Endpoints: `GET /admin/health`, `GET /admin/tenants`, `GET /admin/tenants/{slug}`, `POST /admin/tenants`, `PATCH /admin/tenants/{slug}/status`, `GET /admin/tenants/{slug}/users`
- Auditoria automatica em `public.platform_audit_log` para todas as operacoes de escrita

