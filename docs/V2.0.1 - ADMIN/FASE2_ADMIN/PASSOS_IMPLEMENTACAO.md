# PASSOS DE IMPLEMENTAÇÃO - IntelliCare Admin

**Data**: 2026-03-02
**Status**: 🟢 Pronto para Implementação
**Versão**: 1.0.0

---

## 📋 Checklist de Implementação

Este documento contém o checklist passo a passo para implementação do módulo **intellicare-admin**.

---

## FASE 0: Pré-Implementação

### Setup do Ambiente

- [ ] Criar ambiente virtual
  ```bash
  cd intellicare-admin
  python -m venv .venv
  source .venv/bin/activate  # Linux/Mac
  .venv\Scripts\activate     # Windows
  ```

- [ ] Instalar dependências
  ```bash
  pip install -e ".[dev]"
  ```

- [ ] Configurar pre-commit hooks
  ```bash
  pre-commit install
  ```

### Schema Database

- [ ] Conectar no PostgreSQL
  ```bash
  psql -h localhost -U postgres -d intellicare
  ```

- [ ] Criar schema platform
  ```sql
  CREATE SCHEMA IF NOT EXISTS platform;
  GRANT ALL ON SCHEMA platform TO admin_module_role;
  ```

- [ ] Verificar schema criado
  ```sql
  \dn platform
  ```

### Keycloak Configuration

- [ ] Acessar Admin Console: https://auth.intellicare.ia.br/admin

- [ ] Criar client intellicare-admin
  - Client ID: `intellicare-admin`
  - Client Authentication: ON
  - Authorization: OFF
  - Standard Flow: OFF
  - Service Accounts Roles: ON
  - Valid Redirect URIs: `http://localhost:8010/*`

- [ ] Obter client secret
  ```bash
  kcadm.sh get clients/intellicare-admin/secrets -r bemcuidar
  ```

- [ ] Configurar client credentials no .env
  ```bash
  KEYCLOAK_CLIENT_ID=intellicare-admin
  KEYCLOAK_CLIENT_SECRET=<secret>
  ```

- [ ] Criar role PLATFORM_ADMIN (se não existe)
  ```bash
  kcadm.sh create roles -r bemcuidar -s name=PLATFORM_ADMIN
  ```

- [ ] Criar role PLATFORM_SUPPORT
  ```bash
  kcadm.sh create roles -r bemcuidar -s name=PLATFORM_SUPPORT
  ```

- [ ] Testar autenticação
  ```bash
  python -c "from admin.core.security import test_keycloak; test_keycloak()"
  ```

---

## FASE 1: Core - CRUD Tenants

### Estrutura de Diretórios

- [ ] Criar estrutura base
  ```bash
  mkdir -p admin/{api,core,models,schemas,services,utils,workers,tasks}
  touch admin/__init__.py admin/api/__init__.py admin/core/__init__.py
  touch admin/models/__init__.py admin/schemas/__init__.py
  touch admin/services/__init__.py admin/utils/__init__.py
  touch admin/workers/__init__.py admin/tasks/__init__.py
  ```

### Models

- [ ] Criar `admin/models/tenant.py`
  ```python
  class Tenant(Base):
      # Ver especificação técnica
  ```

- [ ] Criar `admin/models/plan.py`
  ```python
  class Plan(Base):
      # Ver especificação técnica
  ```

- [ ] Criar `admin/models/billing.py`
  ```python
  class BillingRecord(Base):
      # Ver especificação técnica
  ```

- [ ] Criar `admin/models/audit.py`
  ```python
  class AuditLog(Base):
      # Ver especificação técnica
  ```

### Schemas

- [ ] Criar `admin/schemas/tenant.py`
  - TenantCreate
  - TenantResponse
  - TenantUpdate
  - TenantListResponse

- [ ] Criar `admin/schemas/plan.py`
  - PlanCreate
  - PlanResponse
  - PlanUpdate

- [ ] Criar `admin/schemas/billing.py`
  - BillingRecordResponse
  - BillingRecordCreate

### Services

- [ ] Criar `admin/services/tenant_service.py`
  - TenantRepository
  - create_tenant()
  - get_tenant()
  - list_tenants()
  - update_tenant()
  - delete_tenant()

### API Endpoints

- [ ] Criar `admin/api/v1/tenants.py`
  - POST /api/v1/admin/tenants
  - GET /api/v1/admin/tenants
  - GET /api/v1/admin/tenants/{id}
  - PATCH /api/v1/admin/tenants/{id}
  - DELETE /api/v1/admin/tenants/{id}

### Validações

- [ ] Criar `admin/utils/cnpj.py`
  - validate_cnpj()
  - format_cnpj()

- [ ] Criar `admin/utils/domain.py`
  - validate_domain()
  - is_domain_available()

### Testes

- [ ] Criar `tests/api/test_tenants.py`
  - test_create_tenant_success
  - test_create_tenant_duplicate_cnpj
  - test_list_tenants
  - test_get_tenant
  - test_update_tenant
  - test_delete_tenant

---

## FASE 2: Autenticação e Segurança

### Keycloak Integration

- [ ] Instalar python-keycloak
  ```bash
  pip install python-keycloak
  ```

- [ ] Criar `admin/services/keycloak_service.py`
  - KeycloakService class
  - create_tenant_group()
  - create_tenant_admin_user()
  - revoke_tenant_tokens()

### JWT Middleware

- [ ] Criar `admin/api/middleware.py`
  - require_platform_admin()
  - require_platform_support()

- [ ] Criar `admin/api/deps.py`
  - get_current_user()
  - get_current_tenant()

- [ ] Integrar middleware no FastAPI app
  ```python
  app.middleware("http") require_platform_admin
  ```

### Testes de Autenticação

- [ ] Criar `tests/api/test_auth.py`
  - test_valid_token_accepted
  - test_invalid_token_rejected
  - test_platform_admin_required
  - test_platform_support_required

---

## FASE 3: Provisionamento

### Schema Management

- [ ] Criar `admin/services/provisioning.py`
  - ProvisioningService
  - create_tenant_schema()
  - drop_tenant_schema()
  - create_base_tables()

### Async Worker

- [ ] Criar `admin/workers/provisioning_worker.py`
  - ProvisioningWorker
  - process_provisioning_queue()
  - rollback_provisioning()

- [ ] Configurar Redis queue
  ```python
  import redis.asyncio as redis
  ```

### Email Service

- [ ] Criar `admin/utils/email.py`
  - send_welcome_email()
  - send_credentials_email()
  - Email templates (HTML)

### Endpoints de Provisionamento

- [ ] Adicionar endpoint POST /api/v1/admin/tenants/{id}/provision
- [ ] Adicionar endpoint GET /api/v1/admin/tenants/{id}/provisioning-status

### Testes de Provisionamento

- [ ] Criar `tests/services/test_provisioning.py`
  - test_provisioning_success
  - test_provisioning_rollback
  - test_schema_creation
  - test_keycloak_integration

---

## FASE 4: Planos e Módulos

### Seed Plans

- [ ] Criar `admin/scripts/seed_plans.py`
  ```python
  PLANS = [...]
  ```

- [ ] Executar seed
  ```bash
  python -m admin.scripts.seed_plans
  ```

- [ ] Verificar planos no DB
  ```sql
  SELECT * FROM platform.plans;
  ```

### Tenant Modules

- [ ] Criar `admin/models/tenant_module.py`
  ```python
  class TenantModule(Base):
      ...
  ```

- [ ] Criar endpoints
  - GET /api/v1/admin/tenants/{id}/modules
  - PATCH /api/v1/admin/tenants/{id}/modules

- [ ] Criar `admin/schemas/module.py`
  - ModuleEnableRequest
  - ModuleResponse

### Testes de Planos

- [ ] Criar `tests/api/test_plans.py`
  - test_list_plans
  - test_get_plan
  - test_enable_module
  - test_disable_module

---

## FASE 5: Billing Básico

### Billing Service

- [ ] Criar `admin/services/billing_service.py`
  - BillingService
  - calculate_usage()
  - create_billing_record()
  - check_plan_limits()

### Billing Job

- [ ] Criar `admin/tasks/billing_tasks.py`
  - monthly_billing_job()
  - schedule_job()

- [ ] Configurar scheduler (Celery ou APScheduler)

### Billing Endpoints

- [ ] Criar `admin/api/v1/billing.py`
  - GET /api/v1/admin/billing/records
  - GET /api/v1/admin/billing/tenants/{id}
  - POST /api/v1/admin/billing/tenants/{id}/pay

### Testes de Billing

- [ ] Criar `tests/tasks/test_billing.py`
  - test_monthly_job
  - test_usage_calculation
  - test_overdue_detection

---

## FASE 6: Monitoramento

### Prometheus Metrics

- [ ] Instalar prometheus_client
  ```bash
  pip install prometheus-client
  ```

- [ ] Criar `admin/utils/metrics.py`
  - tenants_created_total
  - tenants_suspended_total
  - provisioning_duration_seconds
  - api_request_duration_seconds

- [ ] Expor endpoint /metrics
  ```python
  from prometheus_client import make_asgi_app
  app.add_route("/metrics", make_asgi_app())
  ```

### Dashboard Service

- [ ] Criar `admin/services/dashboard_service.py`
  - DashboardService
  - get_global_metrics()
  - get_tenant_metrics()

### Dashboard Endpoints

- [ ] Criar `admin/api/v1/dashboard.py`
  - GET /api/v1/admin/dashboard/metrics
  - GET /api/v1/admin/dashboard/tenants

### Grafana Dashboard

- [ ] Criar `dashboards/admin.json`
- [ ] Importar no Grafana

---

## FASE 7: Auditoria

### Audit Service

- [ ] Criar `admin/services/audit_service.py`
  - AuditService
  - log_action()
  - query_logs()

### Audit Middleware

- [ ] Atualizar `admin/api/middleware.py`
  - Adicionar audit_log() após cada request

### Audit Endpoints

- [ ] Criar `admin/api/v1/audit.py`
  - GET /api/v1/admin/audit/logs
  - GET /api/v1/admin/audit/logs/{id}
  - GET /api/v1/admin/audit/logs/export

### Testes de Auditoria

- [ ] Criar `tests/api/test_audit.py`
  - test_action_logged
  - test_filter_logs
  - test_export_logs

---

## FASE 8: Suporte - Impersonação

### Support Session Model

- [ ] Criar `admin/models/support.py`
  ```python
  class SupportSession(Base):
      ...
  ```

### Support Service

- [ ] Criar `admin/services/support_service.py`
  - SupportService
  - create_impersonation_session()
  - generate_impersonation_token()
  - end_session()

### Support Endpoints

- [ ] Criar `admin/api/v1/support.py`
  - POST /api/v1/admin/support/impersonate
  - GET /api/v1/admin/support/sessions
  - DELETE /api/v1/admin/support/sessions/{id}

### Testes de Suporte

- [ ] Criar `tests/api/test_support.py`
  - test_impersonate_success
  - test_impersonate_unauthorized
  - test_token_expiration
  - test_audit_during_impersonation

---

## FASE 9: Testes E2E e Documentação

### Testes E2E

- [ ] Criar `tests/e2e/test_tenant_lifecycle.py`
  ```gherkin
  Cenário: Fluxo completo de tenant
    - Criar tenant
    - Aguardar provisioning
    - Verificar schema criado
    - Verificar Keycloak group criado
    - Suspender tenant
    - Reativar tenant
    - Excluir tenant
  ```

### Load Testing

- [ ] Criar `tests/load/tenant_load_test.js` (K6)
  ```javascript
  // Test: 100 req/s por 5 minutos
  ```

- [ ] Executar load test
  ```bash
  k6 run tests/load/tenant_load_test.js
  ```

### Documentação

- [ ] Atualizar `intellicare-admin/README.md`
  - Quick Start
  - API Endpoints
  - Environment Variables
  - Deploy

- [ ] Verificar OpenAPI docs
  - Acessar http://localhost:8010/api/v1/docs
  - Verificar se todos endpoints estão documentados

### Deploy

- [ ] Criar Dockerfile
  ```dockerfile
  FROM python:3.11-slim
  ...
  ```

- [ ] Criar docker-compose.admin.yml
  ```yaml
  services:
    admin:
      ...
  ```

- [ ] Testar local
  ```bash
  docker-compose -f docker-compose.admin.yml up -d
  ```

- [ ] Deploy para staging
  ```bash
  ssh root@167.86.97.142
  cd /opt/intellicare
  git pull origin staging
  docker-compose -f docker-compose.admin.yml up -d
  ```

---

## VALIDAÇÃO FINAL

### Checklist de Validação

- [ ] Todos os testes unitários passando
- [ ] Todos os testes de integração passando
- [ ] Testes E2E passando
- [ ] Cobertura ≥80%
- [ ] Load test passando (100 req/s)
- [ ] Documentação completa
- [ ] OpenAPI docs geradas
- [ ] Deploy staging funcionando
- [ ] Métricas Prometheus visíveis
- [ ] Health check respondendo

### Smoke Test no Staging

- [ ] Criar tenant de teste
  ```bash
  curl -X POST https://admin.intellicare.ia.br/api/v1/admin/tenants \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name": "Teste", "cnpj": "...", ...}'
  ```

- [ ] Verificar se provisioning completou
  ```bash
  curl https://admin.intellicare.ia.br/api/v1/admin/tenants/{id}
  ```

- [ ] Verificar schema criado
  ```bash
  psql -c "\dt tenant_*"
  ```

- [ ] Verificar Keycloak group criado
  ```bash
  kcadm.sh get groups -r bemcuidar | grep tenant_
  ```

---

## CONCLUSÃO

Após completar todos os passos acima, o módulo **intellicare-admin** estará pronto para produção.

### Próximos Passos

1. Aprovação final do stakeholder
2. Deploy em produção
3. Configurar alertas (Prometheus/Grafana)
4. Documentar runbooks operacionais
5. Treinar equipe de suporte

---

**Passos de Implementação v1.0.0**
**Data**: 2026-03-02
**Responsável**: IntelliCare Team
