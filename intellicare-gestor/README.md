# intellicare-gestor

Módulo de gestão **por tenant** do IntelliCare. Permite que o administrador local de cada organização gerencie usuários, permissões RBAC, setores e configurações.

## Diferença Admin vs Gestor

| | intellicare-admin | intellicare-gestor |
|---|---|---|
| **Quem usa** | Super-admin da plataforma | Admin local da organização |
| **Schema** | `platform` | `tenant_{id}` |
| **Gerencia** | Tenants, planos, billing | Usuários, roles, setores |
| **Porta** | 8010 | **8011** |

## Endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/info` | Info do módulo |
| `GET` | `/gestor/users` | Listar usuários do tenant |
| `POST` | `/gestor/users` | Criar/convidar usuário |
| `PATCH` | `/gestor/users/{id}` | Atualizar usuário |
| `DELETE` | `/gestor/users/{id}` | Desativar usuário (soft delete) |
| `GET` | `/gestor/roles` | Listar roles |
| `POST` | `/gestor/roles` | Criar role customizada |
| `PATCH` | `/gestor/roles/{id}` | Atualizar permissões |
| `GET` | `/gestor/sectors` | Listar setores |
| `POST` | `/gestor/sectors` | Criar setor |
| `PATCH` | `/gestor/sectors/{id}` | Atualizar setor |
| `GET` | `/gestor/settings` | Listar configurações |
| `PATCH` | `/gestor/settings` | Atualizar configurações |
| `GET` | `/gestor/audit` | Logs de auditoria |
| `GET` | `/gestor/dashboard` | Dashboard do gestor |

## Desenvolvimento Local

```bash
docker compose up
# http://localhost:8011/docs
```

## Variáveis de Ambiente

| Variável | Default | Descrição |
|---|---|---|
| `INTELLICARE_DATABASE_URL` | — | URL PostgreSQL |
| `INTELLICARE_REDIS_URL` | `redis://localhost:6379` | URL Redis |
| `INTELLICARE_MULTI_TENANT_ENABLED` | `false` | Habilitar multi-tenancy |
| `INTELLICARE_ENVIRONMENT` | `development` | Ambiente |
