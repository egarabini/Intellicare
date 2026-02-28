# F1 — Plano de Implementação: intellicare-admin

> **DEV Atribuído:** DEV 2  
> **Depende de:** F0 (TenantContext + Infra)  
> **Bloqueia:** F2, F3, F5  
> **Pode rodar em paralelo com:** F4 (após F0)

---

## Ordem de Execução

| # | Task | Estimativa | Depende de |
|---|---|---|---|
| 1 | Scaffold do módulo (pyproject.toml, config, app.py) | 0.5 dia | F0 completo |
| 2 | Modelos ORM + Migrations (schema `platform`) | 1 dia | Task 1 |
| 3 | Pydantic Schemas (request/response) | 0.5 dia | Task 2 |
| 4 | TenantService (CRUD tenants) | 1.5 dias | Tasks 2, 3 |
| 5 | ProvisioningService (schema + KC + seed) | 2 dias | Task 4, F0.Task10 |
| 6 | PlanService + ModuleService | 1 dia | Task 2 |
| 7 | API Routes (tenants, plans, modules) | 1 dia | Tasks 4, 5, 6 |
| 8 | BillingService + billing_routes | 1 dia | Task 2 |
| 9 | Dashboard + Audit routes | 0.5 dia | Task 7 |
| 10 | Testes unitários + integração | 1.5 dias | Todas |
| 11 | Seed data (planos padrão) | 0.5 dia | Task 2 |

**Total: 10 dias**

---

## Detalhamento

### Task 1: Scaffold

```
Criar:
  intellicare-admin/
  ├── admin/__init__.py
  ├── admin/config.py          (AdminConfig)
  ├── admin/api/app.py         (create_app com lifespan)
  ├── pyproject.toml
  ├── requirements.txt
  └── README.md

Dependências:
  - intellicare-core
  - intellicare-auth
  - fastapi, uvicorn, sqlalchemy, alembic
  - python-keycloak (para Admin API)
```

### Task 2: Modelos ORM

```
Criar:
  admin/models/tenant.py      → Tenant, TenantModule
  admin/models/plan.py        → Plan
  admin/models/billing.py     → BillingRecord
  admin/models/audit.py       → GlobalAuditLog

Executar:
  alembic init migrations
  alembic revision --autogenerate -m "create platform schema"
  alembic upgrade head

Verificar:
  - Schema "platform" criado
  - Tabelas tenants, plans, tenant_modules, billing_records, audit_global existem
```

### Task 5: ProvisioningService (Mais Complexa)

```
Implementar:
  admin/services/provisioning_service.py

O fluxo é:
  1. CREATE SCHEMA tenant_{id};
  2. Rodar Alembic migrations nesse schema (subprocess ou API)
  3. POST /admin/realms/bemcuidar/groups → {name: "tenant_{id}"}
  4. Criar protocol mapper no grupo
  5. POST /admin/realms/bemcuidar/users → {email: admin_email, ...}
  6. PUT /admin/realms/bemcuidar/users/{uid}/groups/{gid}
  7. INSERT seed data (roles DEFAULT, configs default)
  8. UPDATE tenants SET provisioned=true WHERE tenant_id=...
```

> [!CAUTION]
> **Rollback:** Se o passo 3 falha, deletar o schema criado no passo 1. Se o passo 5 falha, deletar o grupo do passo 3 E o schema. Manter estado `provisioning_failed` para retry.

### Task 11: Seed Data

```sql
-- admin/seeds/default_plans.sql
INSERT INTO platform.plans (name, display_name, max_users, max_sms_month, price_monthly, modules_included)
VALUES
  ('trial',         'Trial (30 dias)', 5,    100,   0,      '["zilda","florence"]'),
  ('basico',        'Básico',          20,   500,   497.00, '["zilda","florence","oswaldo","geralda"]'),
  ('profissional',  'Profissional',    100,  2000,  1497.00,'["zilda","florence","oswaldo","geralda","donabedian","comunicacao","grahame"]'),
  ('enterprise',    'Enterprise',      9999, 10000, 2997.00,'["zilda","florence","oswaldo","geralda","donabedian","comunicacao","grahame","wanda"]');
```

---

## Checklist de Entrega

- [ ] Módulo scaffolded e importável
- [ ] Schema `platform` criado com todas as tabelas
- [ ] CRUD Tenants funcionando (POST, GET, PATCH, suspend, activate)
- [ ] Provisioning cria schema + grupo KC + usuário admin
- [ ] Provisioning tem rollback em caso de falha
- [ ] Planos seed inseridos
- [ ] Ativação/desativação de módulos por tenant
- [ ] Billing records CRUD
- [ ] Dashboard com métricas básicas
- [ ] Auditoria global registrando ações
- [ ] Testes passando (min 80% cobertura no service layer)
- [ ] README com instruções de execução
