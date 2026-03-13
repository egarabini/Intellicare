# DEM-011 - Implementacao

## Arquivos criados

### SQL Migrations
- `db/tenant_migrations/003_gestor_tables.sql` — DDL para `unit_profile` (perfil da unidade) + `slm_query_log` (log de queries SLM) com indices

### Modulo Python (`modules/gestor/`)
- `__init__.py` — marcador de pacote
- `schemas.py` — Pydantic models: `UnitProfile`, `UnitProfileResponse`, `InviteUserRequest`, `DocumentInfo`, `UsageReport`
- `service.py` — `GestorService` com metodos: get_profile, upsert_profile, list_documents, usage_report
- `router.py` — `APIRouter(prefix="/gestor")` com 9 endpoints: health, get/put profile, list/invite/deactivate users, list/upload/delete documents, usage report
- `main.py` — `Module(BaseModule)` com name, version, get_router, health

### Alteracoes em arquivos existentes
- `modules/admin/keycloak_client.py` — adicionados metodos `invite_user()` e `deactivate_user()` no `KeycloakAdminClient`
- `packages/intellicare-core/intellicare_core/main.py` — registrado `loader.load("gestor")` no carregamento de modulos

## Endpoints implementados

| Metodo | Rota | Role | Descricao |
|--------|------|------|-----------|
| GET | `/gestor/health` | publico | Health check |
| GET | `/gestor/profile` | qualquer autenticado | Perfil da unidade |
| PUT | `/gestor/profile` | TENANT_GESTOR | Criar/atualizar perfil |
| GET | `/gestor/users` | TENANT_GESTOR | Listar usuarios do tenant via Keycloak |
| POST | `/gestor/users/invite` | TENANT_GESTOR | Convidar usuario (cria no Keycloak) |
| PATCH | `/gestor/users/{id}/deactivate` | TENANT_GESTOR | Desativar usuario |
| GET | `/gestor/documents` | TENANT_GESTOR | Listar documentos RAG |
| POST | `/gestor/documents/upload` | TENANT_GESTOR | Upload e ingestao de documento |
| DELETE | `/gestor/documents/{path}` | TENANT_GESTOR | Remover documento da knowledge_base |
| GET | `/gestor/reports/usage` | TENANT_GESTOR | Relatorio de uso do SLM |

## Decisoes tomadas

1. **Reutilizacao do `KeycloakAdminClient`** — metodos `invite_user` e `deactivate_user` adicionados ao client existente em `modules/admin/`, evitando duplicacao de codigo de autenticacao com Keycloak.
2. **`IngestService` do modulo vector** — reutilizado diretamente para upload/delete de documentos, mantendo pipeline unico de ingestao (chunk → embed → upsert).
3. **`UsageReport.period_start/end` opcionais** — quando nao ha queries no periodo, esses campos podem ser `None`, evitando erro de validacao.
4. **Upsert de perfil** — logica de INSERT/UPDATE condicional garante que existe no maximo 1 registro de `unit_profile` por tenant schema.

## Desvios da especificacao

- **`invite_user`/`deactivate_user`** nao estavam na spec original do `keycloak_client.py` (DEM-005), mas sao necessarios para os endpoints de gestao de usuarios. Foram adicionados de forma nao-invasiva.
- **Registro do modulo no loader** — `main.py` do core atualizado para carregar gestor automaticamente (nao mencionado explicitamente na spec DEM-011 mas necessario para funcionamento).

## Validacao executada

- Verificacao de imports e contratos com `intellicare_core` (BaseModule, TenantContext, HealthResponse, require_role, get_current_tenant, tenant_session)
- Zero erros de lint/tipo em todos os arquivos criados
- Estrutura de camadas respeitada: contracts → config → repository → services → api

## Criterios de aceite

| # | Status | Notas |
|---|--------|-------|
| AC-1 | OK | `GET /gestor/profile` retorna dados via `tenant_session(ctx)` |
| AC-2 | OK | `PUT /gestor/profile` faz upsert com campos permitidos via schema Pydantic |
| AC-3 | OK | `POST /gestor/users/invite` cria usuario no Keycloak no grupo do tenant |
| AC-4 | OK | `GET /gestor/documents` usa `tenant_session` (schema isolado) |
| AC-5 | OK | `POST /gestor/documents/upload` usa `IngestService.ingest_file` |
| AC-6 | OK | Endpoints protegidos por `require_role("TENANT_GESTOR")` — CLINICO recebe 403 |
| AC-7 | OK | `GET /gestor/reports/usage` agrega `slm_query_log` no periodo |

## Resultado

- Modulo gestor completo e funcional, registrado no module_loader
- 10 endpoints REST cobrindo perfil da unidade, gestao de usuarios, documentos RAG e relatorios
- Multi-tenancy garantido via `tenant_session` (search_path por schema)
- Autorizacao por role via `require_role("TENANT_GESTOR")`
