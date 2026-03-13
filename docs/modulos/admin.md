---
tipo: nota-modulo
modulo: admin
porto: 8010
fase: 1
sprint: "1.3"
status: pendente
dem_principal: DEM-005
tags: [fase-1, admin, p0]
---

# Módulo: admin

**Responsabilidade:** Administração da plataforma — gestão de tenants, provisionamento de schemas, integração Keycloak e módulo financeiro (planos, contratos, faturas).

---

## Propósito

Módulo exclusivo do `PLATFORM_ADMIN`. Controla o ciclo de vida de tenants (criação, ativação, suspensão) e o módulo financeiro (planos, contratos, faturas, job de inadimplência). Toda ação é registrada em `platform_audit_log`.

---

## Endpoints Principais

### Tenant Management (DEM-005)

| Método | Rota | Descrição | Role |
|--------|------|-----------|------|
| GET | `/admin/health` | Health check | any |
| GET | `/admin/tenants` | Lista tenants (paginado) | `PLATFORM_ADMIN` |
| GET | `/admin/tenants/{slug}` | Detalhe de um tenant | `PLATFORM_ADMIN` |
| POST | `/admin/tenants` | Cria tenant + schema + grupo Keycloak | `PLATFORM_ADMIN` |
| PATCH | `/admin/tenants/{slug}/status` | Ativa/suspende tenant | `PLATFORM_ADMIN` |
| GET | `/admin/tenants/{slug}/users` | Lista usuários do tenant (via Keycloak) | `PLATFORM_ADMIN` |

### Financeiro (DEM-007)

| Método | Rota | Descrição | Role |
|--------|------|-----------|------|
| GET | `/financeiro/health` | Health check | any |
| GET | `/financeiro/plans` | Lista planos ativos | `PLATFORM_ADMIN` |
| POST | `/financeiro/plans` | Cria plano | `PLATFORM_ADMIN` |
| POST | `/financeiro/contracts` | Cria contrato + 1ª fatura | `PLATFORM_ADMIN` |
| GET | `/financeiro/contracts/{id}/invoices` | Faturas de um contrato | `PLATFORM_ADMIN` |
| PATCH | `/financeiro/invoices/{id}/pay` | Marca fatura como paga | `PLATFORM_ADMIN` |
| GET | `/financeiro/reports/billing` | Relatório mensal | `PLATFORM_ADMIN` |

---

## Tabelas

### Schema `public` (globais)

| Tabela | Descrição |
|--------|-----------|
| `tenants` | Registro de tenants (`id`, `slug`, `name`, `status`, timestamps) |
| `platform_audit_log` | Auditoria (`actor_id`, `action`, `target_type`, `payload` JSONB) |
| `plans` | Planos disponíveis (`price_brl` em centavos, `max_users`, `cycle`) |
| `contracts` | Contratos tenant↔plano (`start_date`, `end_date`, `status`) |
| `invoices` | Faturas (`amount_brl`, `due_date`, `paid_at`, `status`: pending/paid/overdue) |

### Schema `tenant_{slug}` (por tenant, criado no provisionamento)

| Tabela | Descrição |
|--------|-----------|
| `users` | Espelho leve do Keycloak (`keycloak_id`, `email`, `role`) |
| `knowledge_base` | Base RAG (`content`, `embedding vector(768)`, `source_path`) |

---

## Roles Autorizados

- **`PLATFORM_ADMIN`** — acesso total a todos os endpoints admin e financeiro
- Sem token → 401; token com role diferente → 403

---

## Stack e Dependências

- FastAPI (APIRouter com prefix `/admin` e `/financeiro`)
- SQLAlchemy async (`get_engine()` para queries diretas)
- Keycloak Admin API via `KeycloakAdminClient` (criação de grupos, listagem de usuários)
- APScheduler: job diário às 03:00 para marcar faturas overdue e suspender tenants inadimplentes
- [[decisoes/ADR-001-schema-autonomo]]
- [[decisoes/ADR-002-modulo-vs-servico]]
- DEM-003: intellicare-core (`TenantContext`, auth, db)
- DEM-004: Keycloak configurado (realm, clients, roles)

---

## DEMs relacionadas

- **DEM-005**: Admin backend (CRUD tenants + provisionamento)
- **DEM-006**: Admin frontend (HTMX/Jinja2 dashboard)
- **DEM-007**: Módulo Financeiro (planos, contratos, faturas, job inadimplência)
