# IntelliCare Admin

**Módulo de administração da plataforma IntelliCare SaaS.**

Gerencia tenants (organizações), planos, módulos contratados, billing e auditoria.

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run server
uvicorn admin.api.app:app --host 0.0.0.0 --port 8010

# Seed plans
python -m admin.scripts.seed_plans
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/admin/tenants` | Create tenant + provisioning |
| `GET` | `/admin/tenants` | List tenants (paginated) |
| `GET` | `/admin/tenants/{id}` | Tenant details |
| `PATCH` | `/admin/tenants/{id}` | Update tenant |
| `POST` | `/admin/tenants/{id}/suspend` | Suspend tenant |
| `POST` | `/admin/tenants/{id}/activate` | Reactivate tenant |
| `GET` | `/admin/tenants/{id}/modules` | Tenant modules |
| `PATCH` | `/admin/tenants/{id}/modules` | Enable/disable modules |
| `GET` | `/admin/plans` | List plans |
| `GET` | `/admin/dashboard` | Global metrics |

## Environment Variables

```env
ADMIN_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/intellicare
ADMIN_KEYCLOAK_ADMIN_URL=https://keycloak.example.com
ADMIN_KEYCLOAK_ADMIN_USERNAME=admin
ADMIN_KEYCLOAK_ADMIN_PASSWORD=secret
ADMIN_KEYCLOAK_TARGET_REALM=bemcuidar
```
