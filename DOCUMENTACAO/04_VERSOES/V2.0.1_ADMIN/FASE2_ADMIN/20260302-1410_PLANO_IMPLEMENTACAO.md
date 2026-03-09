# PLANO DE IMPLEMENTAÇÃO - IntelliCare Admin

**Data**: 2026-03-02
**Status**: 🟡 Plano em Elaboração
**Responsável**: IntelliCare Team
**Versão**: 1.0.0

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Fases de Implementação](#fases-de-implementação)
3. [Dependências](#dependências)
4. [Riscos e Mitigações](#riscos-e-mitigações)
5. [Critérios de Aceite](#critérios-de-aceite)
6. [Recursos Necessários](#recursos-necessários)

---

## 🎯 Visão Geral

Este documento define o plano de implementação do módulo **intellicare-admin**, componente crítico da arquitetura multi-tenant da plataforma IntelliCare.

### Objetivos

1. Implementar API REST para administração da plataforma
2. Garantir acesso exclusivo a usuários PLATFORM_ADMIN
3. Criar sistema de provisionamento automático de tenants
4. Estabelecer controle de planos e billing básico
5. Implementar auditoria completa de ações administrativas

### Escopo da Implementação

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Auth**: Integração com Keycloak (role PLATFORM_ADMIN)
- **Provisioning**: Schema PostgreSQL + Keycloak group
- **Monitoramento**: Métricas Prometheus
- **Documentação**: OpenAPI auto-generated

---

## 📅 Fases de Implementação

### Fase 0: Pré-Implementação (2 dias)

**Objetivo**: Preparar ambiente e dependências

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Setup do ambiente | Configurar venv, dependências | Ambiente pronto |
| Base de dados | Criar schema `platform` | Schema vazio |
| Keycloak config | Configurar client admin | Client configurado |
| Estrutura de pastas | Criar diretórios base | Estrutura criada |

**Critérios de Sucesso**:
- [x] Ambiente de desenvolvimento configurado
- [x] Schema `platform` criado no PostgreSQL
- [x] Client Keycloak criado e testado
- [x] Estrutura de diretórios seguindo padrão

---

### Fase 1: Core - CRUD Tenants (5 dias)

**Objetivo**: Implementar gerenciamento básico de tenants

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Models | Criar ORM models (Tenant, Plan, etc) | models/ |
| Schemas | Criar Pydantic schemas (req/res) | schemas/ |
| Repositories | Implementar TenantRepository | services/tenant_service.py |
| API Endpoints | POST, GET, PATCH, DELETE /tenants | api/v1/tenants.py |
| Validações | CNPJ, domínio único | utils/cnpj.py |
| Testes unitários | Coverage ≥80% | tests/ |

**API Endpoints**:
```
POST   /api/v1/admin/tenants
GET    /api/v1/admin/tenants
GET    /api/v1/admin/tenants/{id}
PATCH  /api/v1/admin/tenants/{id}
DELETE /api/v1/admin/tenants/{id}
```

**Critérios de Sucesso**:
- [x] CRUD completo de tenants funcional
- [x] Validação de CNPJ funcionando
- [x] Domínio único garantido (DB constraint)
- [x] Testes com ≥80% de cobertura
- [x] Documentação OpenAPI gerada

---

### Fase 2: Autenticação e Segurança (3 dias)

**Objetivo**: Implementar controle de acesso PLATFORM_ADMIN

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Keycloak integration | Configurar client python-keycloak | services/keycloak_service.py |
| JWT middleware | Validar token + role PLATFORM_ADMIN | api/middleware.py |
| Dependency | get_current_user dependency | api/deps.py |
| Testes auth | Testar tokens válidos/inválidos | tests/api/test_auth.py |

**Fluxo de Autenticação**:
```
Request → JWT Validation → PLATFORM_ADMIN check → Endpoint
                 ↓                  ↓
              401 if invalid     403 if not admin
```

**Critérios de Sucesso**:
- [x] Todo endpoint valida JWT
- [x] Apenas PLATFORM_ADMIN acessa endpoints
- [x] Tokens inválidos retornam 401
- [x] Tokens sem role retornam 403
- [x] Testes de segurança passando

---

### Fase 3: Provisionamento (5 dias)

**Objetivo**: Implementar provisionamento automático de tenants

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Schema creation | Criar schema tenant_{id} | services/provisioning.py |
| Keycloak group | Criar grupo no Keycloak | keycloak_service.py |
| Tenant admin user | Criar usuário admin do tenant | keycloak_service.py |
| Async worker | Worker para provisioning async | workers/provisioning_worker.py |
| Email service | Enviar credenciais por email | utils/email.py |
| Rollback | Rollback completo em falha | provisioning.py |

**Fluxo de Provisionamento**:
```
POST /tenants → Create tenant record (status='provisioning')
                    ↓
              Publish event (Redis)
                    ↓
              Provisioning Worker
                    ↓
       ┌──────────┴──────────┐
       │                     │
   [Success]            [Failure]
       │                     │
   status='active'      Rollback
   Send email           Log error
```

**Critérios de Sucesso**:
- [x] Schema PostgreSQL criado automaticamente
- [x] Grupo Keycloak criado
- [x] Usuário admin criado e credenciais enviadas
- [x] Rollback funciona em caso de falha
- [x] Provisionamento <30s
- [x] Testes E2E passando

---

### Fase 4: Planos e Módulos (3 dias)

**Objetivo**: Implementar gestão de planos e módulos por tenant

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Seed plans | Inserir planos seed (trial, basic, etc) | scripts/seed_plans.py |
| Plan CRUD | Endpoints para gerenciar planos | api/v1/plans.py |
| Tenant modules | Tabela tenant_modules | models/ |
| Enable/disable | Atualizar módulos por tenant | api/v1/tenants/{id}/modules |
| Validações | Validar limites do plano | services/plan_service.py |

**Planos Seed**:
```python
PLANS = [
    {
        "id": "trial",
        "name": "Plano Trial",
        "price_monthly": 0,
        "max_users": 5,
        "max_storage_gb": 10,
        "max_api_calls_monthly": 1000,
        "modules": ["florence", "oswaldo"]
    },
    {
        "id": "basic",
        "name": "Plano Básico",
        "price_monthly": 297.00,
        "max_users": 20,
        "max_storage_gb": 50,
        "max_api_calls_monthly": 10000,
        "modules": ["florence", "oswaldo", "wanda"]
    },
    {
        "id": "professional",
        "name": "Plano Profissional",
        "price_monthly": 897.00,
        "max_users": 100,
        "max_storage_gb": 200,
        "max_api_calls_monthly": 100000,
        "modules": ["florence", "oswaldo", "wanda", "donabedian", "geralda"]
    },
    {
        "id": "enterprise",
        "name": "Plano Enterprise",
        "price_monthly": 2997.00,
        "max_users": -1,  # ilimitado
        "max_storage_gb": -1,
        "max_api_calls_monthly": -1,
        "modules": ["*"]  # todos
    }
]
```

**Critérios de Sucesso**:
- [x] Planos seed inseridos no DB
- [x] CRUD de planos funcionando
- [x] Módulos podem ser habilitados/desabilitados por tenant
- [x] Limites do plano são validados
- [x] Testes passando

---

### Fase 5: Billing Básico (4 dias)

**Objetivo**: Implementar registro de uso e billing

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Billing model | Tabela billing_records | models/billing.py |
| Usage tracking | Contar usuários, API calls | services/billing_service.py |
| Monthly job | Job que roda dia 1 de cada mês | tasks/billing_tasks.py |
| Status | pending → paid/overdue | services/billing_service.py |
| Endpoints | GET billing/records, POST /pay | api/v1/billing.py |

**Fluxo de Billing**:
```
Dia 1, 00:00 UTC → Billing Job inicia
                      ↓
             Para cada tenant ativo:
                      ↓
          ┌──────────┴──────────┐
          │                     │
    Contar usuários        Contar API calls
    ativos no mês          no mês
          │                     │
          └──────────┬──────────┘
                     ↓
            Calcular storage usado
                     ↓
            Criar billing_record
                     ↓
            Verificar limites do plano
                     ↓
          ┌──────────┴──────────┐
          │                     │
    Dentro do plano      Excedeu limites
    status='pending'     status='overdue'
          │                     │
          └──────────┬──────────┘
                     ↓
            Notificar (se overdue)
```

**Critérios de Sucesso**:
- [x] Job de billing roda automaticamente
- [x] Uso é contabilizado corretamente
- [x] Registros são criados mensalmente
- [x] Status overdue é marcado corretamente
- [x] Testes de billing passando

---

### Fase 6: Monitoramento (3 dias)

**Objetivo**: Implementar dashboard e métricas

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Prometheus metrics | Setup prometheus_client | utils/metrics.py |
| Dashboard endpoint | GET /admin/dashboard/metrics | api/v1/dashboard.py |
| Global metrics | Totais de tenants, users, etc | services/dashboard_service.py |
| Per-tenant metrics | Métricas por tenant | services/dashboard_service.py |
| Grafana dashboard | JSON para importar | dashboards/admin.json |

**Métricas Prometheus**:
```python
# Contadores
tenants_created_total
tenants_suspended_total
api_requests_total

# Histogramas
provisioning_duration_seconds
api_request_duration_seconds

# Gauges
tenants_active
tenants_suspended
billing_overdue_total
```

**Critérios de Sucesso**:
- [x] Métricas expostas em /metrics
- [x] Dashboard endpoint retorna dados
- [x] Grafana dashboard configurado
- [x] Métricas visíveis em tempo real

---

### Fase 7: Auditoria (3 dias)

**Objetivo**: Implementar log completo de ações

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Audit log model | Tabela audit_logs | models/audit.py |
| Audit middleware | Auto-log toda ação | api/middleware.py |
| Query endpoint | GET /admin/audit/logs | api/v1/audit.py |
| Export | CSV/JSON export | api/v1/audit.py |
| Testes | Testar logging | tests/audit/ |

**Campos do Audit Log**:
```
who: user_id, email, role
what: action, endpoint, payload
when: timestamp UTC
where: IP, user_agent
why: reason (se aplicável)
impersonated_as: user_id (se aplicável)
```

**Critérios de Sucesso**:
- [x] Toda ação é logada
- [x] Logs são imutáveis
- [x] Consulta filtrável funciona
- [x] Export funciona
- [x] Testes passando

---

### Fase 8: Suporte - Impersonação (2 dias)

**Objetivo**: Implementar impersonação para suporte

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Support session model | Tabela support_sessions | models/support.py |
| Impersonate endpoint | POST /admin/support/impersonate | api/v1/support.py |
| Token generation | Gerar token temporário | services/support_service.py |
| Audit durante impersonação | Logs com ACTED_AS | middleware.py |
| List sessions | GET /admin/support/sessions | api/v1/support.py |
| End session | DELETE /admin/support/sessions/{id} | api/v1/support.py |

**Fluxo de Impersonação**:
```
POST /impersonate
      ↓
Validar PLATFORM_SUPPORT
      ↓
Criar support_session (status='active')
      ↓
Gerar token temporário (1h)
      ↓
Audit log (action='IMPERSONATE')
      ↓
Retornar token
```

**Critérios de Sucesso**:
- [x] Apenas PLATFORM_SUPPORT pode impersonar
- [x] Token expira em 1h
- [x] Ações durante impersonação são auditadas
- [x] Sessões podem ser listadas e encerradas
- [x] Testes passando

---

### Fase 9: Testes E2E e Documentação (3 dias)

**Objetivo**: Finalizar e validar implementação

| Tarefa | Descrição | Entregável |
|--------|-----------|------------|
| Testes E2E | Suite completa de testes | tests/e2e/ |
| Load testing | K6 ou Locust | tests/load/ |
| Documentation | README completo | README.md |
| OpenAPI docs | Verificar documentação | /api/v1/docs |
| Deploy playbook | Ansible/Helm | deploy/ |

**Testes E2E**:
```gherkin
Cenário: Fluxo completo de criação de tenant
  Dado PLATFORM_ADMIN autenticado
  Quando cria tenant
  Então tenant é criado
  E provisioning inicia
  E após 30s tenant está active
  E schema existe no DB
  E grupo existe no Keycloak
  E email foi enviado
```

**Critérios de Sucesso**:
- [x] Todos os testes passando
- [x] Cobertura ≥80%
- [x] Load test: suporta 100 req/s
- [x] Documentação completa
- [x] Deploy automatizado

---

## 🔗 Dependências

### Dependências Técnicas

| Componente | Versão | Status | Observações |
|------------|--------|--------|-------------|
| PostgreSQL | 15+ | ✅ | Schema platform será criado |
| Keycloak | 24+ | ✅ | Realm bemcuidar configurado |
| intellicare-core | latest | ✅ | TenantContext disponível |
| intellicare-auth | latest | ✅ | JWT validation disponível |
| Redis | 7+ | ✅ | Para filas e cache |

### Dependências Funcionais

| Item | Status | Observações |
|------|--------|-------------|
| FASE0_KEYCLOAK completo | ✅ | Keycloak rodando em staging |
| Role PLATFORM_ADMIN criado | ✅ | Definido no realm bemcuidar |
| Client intellicare-admin | 🔶 | Criar no Keycloak |

---

## ⚠️ Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Falha no provisionamento deixa tenant inconsistente | Alto | Média | Implementar rollback completo |
| Keycloak Admin API muda versão | Alto | Baixa | Usar cliente Python estável + version pin |
| Performance degrada com muitos tenants | Médio | Baixa | Índices otimizados + cache |
| CNPJ duplicado passa validação | Alto | Baixa | Validar no API + unique constraint |
| Email com credenciais não chega | Alto | Média | Retry mechanism + fallback para reenvio |

---

## ✅ Critérios de Aceite

### Critérios Técnicos

- [x] Python 3.11+ com FastAPI
- [x] PostgreSQL 15+ com schema platform
- [x] Integração Keycloak JWT funcionando
- [x] Testes com ≥80% de cobertura
- [x] OpenAPI docs geradas
- [x] Migrations idempotentes
- [x] Métricas Prometheus expostas

### Critérios Funcionais

- [x] PLATFORM_ADMIN pode gerenciar tenants
- [x] Provisionamento cria schema + KC + usuário
- [x] Planos podem ser gerenciados
- [x] Billing registra uso mensal
- [x] Dashboard mostra métricas globais
- [x] Auditoria registra todas as ações
- [x] PLATFORM_SUPPORT pode impersonar tenants

### Critérios de Performance

- [x] API responde em <200ms (P95)
- [x] Provisionamento <30s
- [x] Dashboard carrega em <2s
- [x] Suporta 100 tenants sem degradação
- [x] Load test: 100 req/s

### Critérios de Segurança

- [x] Apenas PLATFORM_ADMIN acessa API
- [x] Tokens inválidos são rejeitados
- [x] Auditoria é imutável
- [x] Impersonação é rastreável
- [x] Senhas nunca são logadas

---

## 👥 Recursos Necessários

### Equipe

| Role | Qtd | Dedicação | Período |
|------|-----|-----------|---------|
| Backend Dev | 1 | 100% | 30 dias |
| DevOps | 1 | 20% | 30 dias |
| QA | 1 | 50% | últimos 10 dias |

### Infraestrutura

| Recurso | Qtd | Especificação |
|---------|-----|---------------|
| PostgreSQL | 1 | 2 CPU, 4GB RAM, 50GB SSD |
| Redis | 1 | 1 CPU, 2GB RAM |
| Keycloak | 1 | Já existente |
| Servidor Staging | 1 | 2 CPU, 4GB RAM |

---

## 📊 Cronograma

```
Semana 1: Fase 0 + 1 (Pré-implementação + CRUD Tenants)
Semana 2: Fase 2 + 3 (Auth + Provisioning)
Semana 3: Fase 4 + 5 (Planos + Billing)
Semana 4: Fase 6 + 7 (Monitoramento + Auditoria)
Semana 5: Fase 8 + 9 (Suporte + Testes E2E)
Semana 6: Buffer + Deploy + Documentação
```

**Total**: 30 dias úteis (~6 semanas)

---

## 📝 Próximos Passos

1. ✅ Aprovar este plano de implementação
2. 🔵 Atribuir desenvolvedor
3. 🔵 Configurar ambiente de desenvolvimento
4. 🔵 Iniciar Fase 0
5. 🔵 Seguir cronograma

---

## 📚 Referências

- [ESPECIFICACAO_FUNCIONAL.md](./20260302-1400_ESPECIFICACAO_FUNCIONAL.md)
- [ESPECIFICACAO_TECNICA.md](./20260302-1405_ESPECIFICACAO_TECNICA.md)
- [PASSOS_IMPLEMENTACAO.md](./PASSOS_IMPLEMENTACAO.md)

---

**Plano de Implementação v1.0.0**
**Data**: 2026-03-02
**Responsável**: IntelliCare Team
**Aprovado por**: ___________
**Data Aprovação**: ___________
