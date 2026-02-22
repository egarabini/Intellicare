# PLANO DE IMPLEMENTAÇÃO - Separação Operacional/Analítico

**Data**: 2026-02-11  
**Status**: 🟢 Plano Completo  
**Duração Estimada**: 6 semanas  
**Equipe**: 2-3 desenvolvedores  
**Sprint**: 2 semanas por fase  

---

## 📋 Índice

1. [Visão Geral do Plano](#visão-geral-do-plano)
2. [Fase 1: Fundação (Sprint 1-2)](#fase-1-fundação-sprint-1-2)
3. [Fase 2: Implementação Core (Sprint 3-4)](#fase-2-implementação-core-sprint-3-4)
4. [Fase 3: Consolidação (Sprint 5-6)](#fase-3-consolidação-sprint-5-6)
5. [Fase 4: Validação e Deploy (Sprint 7+)](#fase-4-validação-e-deploy-sprint-7)
6. [Checklist de Entrega](#checklist-de-entrega)
7. [Riscos e Mitigação](#riscos-e-mitigação)
8. [Métricas de Sucesso](#métricas-de-sucesso)

---

## 🎯 Visão Geral do Plano

### Objetivos

```
✅ Implementar separação operacional/analítico em todos os 8 módulos
✅ Garantir unidirecionalidade: operacional → analítico (nunca ao contrário)
✅ Implementar monitoramento de violações
✅ Treinar equipe no novo padrão
✅ Zero impacto em operações existentes
```

### Timeline

```
SEMANA 1-2   : Fundação (infrastructure, base libraries)
SEMANA 3-4   : Core implementation (schemas, DAOs, events)
SEMANA 5-6   : Consolidation service (batch jobs, metrics)
SEMANA 7+    : Validation, testing, deploy progressivo
```

### Deliverables por Fase

| Fase | Sprint | Entrega Principal | Critério de Sucesso |
|------|--------|-------------------|---------------------|
| 1    | 1-2    | Base Architecture | intellicare-core com DAO patterns |
| 2    | 3-4    | Module Integration | Todos os 8 módulos com schemas |
| 3    | 5-6    | Consolidation Job | Batch processing com métricas |
| 4    | 7+     | Production Ready  | 989 testes passando, zero violações |

---

## 🔧 FASE 1: Fundação (Sprint 1-2)

### Objetivo
Criar base de código compartilhada em `intellicare-core` com padrões reutilizáveis.

### 📝 Tarefas

#### Task 1.1: Setup inicial do repositório
**Duração**: 1 dia  
**Responsável**: Dev Lead  
**Deliverable**: Estrutura de pastas

```bash
# Estrutura
intellicare-core/
├── src/
│   └── intellicare_core/
│       ├── __init__.py
│       ├── data_access/
│       │   ├── __init__.py
│       │   ├── base.py                    # BaseDAO abstrato
│       │   ├── operational.py             # OperationalDataAccess[T]
│       │   ├── analytics.py               # AnalyticsDataAccess[T]
│       │   └── models.py                  # SQLAlchemy models comuns
│       ├── events/
│       │   ├── __init__.py
│       │   ├── publisher.py               # EventPublisher
│       │   ├── models.py                  # Event dataclasses
│       │   └── stream_manager.py          # RedisStreamManager
│       ├── security/
│       │   ├── __init__.py
│       │   ├── rls_enforcer.py            # RLS policies validation
│       │   ├── provenance.py              # FHIR Provenance tracking
│       │   └── audit.py                   # Audit logging
│       ├── monitoring/
│       │   ├── __init__.py
│       │   ├── metrics.py                 # Prometheus metrics
│       │   ├── health_check.py            # Health endpoints
│       │   └── logger.py                  # Structured logging
│       ├── config/
│       │   ├── __init__.py
│       │   ├── database.py                # DB configuration
│       │   ├── redis.py                   # Redis configuration
│       │   └── settings.py                # App settings
│       └── schemas/
│           ├── __init__.py
│           └── common.py                  # Pydantic schemas comuns
├── tests/
│   ├── test_dao.py
│   ├── test_events.py
│   └── test_security.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_core_schemas.py
├── pyproject.toml
├── setup.py
└── README.md
```

**Checklist**:
- [ ] Git repo criado e estrutura inicial
- [ ] pyproject.toml com dependências base
- [ ] CI/CD pipeline básico (.github/workflows)
- [ ] Docker build (Dockerfile)

#### Task 1.2: Implementar BaseDAO abstrato
**Duração**: 3 dias  
**Responsável**: Dev 1  
**Deliverable**: `intellicare_core/data_access/base.py` + testes

```python
# Requerimentos
- BaseDAO abstrato com CRUD genérico
- Type hints genéricos: BaseDAO[T]
- Suporte a filtros, paginação, ordenação
- Métodos para validação de schema
- 100% test coverage
```

**Testes**:
```bash
pytest tests/test_dao.py -v --cov
```

#### Task 1.3: Implementar OperationalDataAccess
**Duração**: 3 dias  
**Responsável**: Dev 1  
**Deliverable**: `intellicare_core/data_access/operational.py`

```python
# Requerimentos
- Estende BaseDAO
- Valida que schema é _operacional apenas
- Implementa create(), update(), read(), list(), delete()
- Rejeita acesso a _analitico
- Integração com ORM SQLAlchemy
- 100% test coverage
```

#### Task 1.4: Implementar AnalyticsDataAccess
**Duração**: 2 dias  
**Responsável**: Dev 2  
**Deliverable**: `intellicare_core/data_access/analytics.py`

```python
# Requerimentos
- Read-only para _analitico
- Métodos: read(), list(), aggregate()
- Rejeita write, update, delete
- Suporte a queries complexas (joins, window functions)
- 100% test coverage
```

#### Task 1.5: Implementar EventPublisher
**Duração**: 3 dias  
**Responsável**: Dev 2  
**Deliverable**: `intellicare_core/events/publisher.py`

```python
# Requerimentos
- Pub/Sub em Redis Streams
- Padrão de stream naming: {schema}:events:{entity_type}
- Serialização JSON com provenance
- Retry logic
- Dead Letter Queue
- 100% test coverage
```

#### Task 1.6: Configuração de Database
**Duração**: 2 dias  
**Responsável**: DevOps  
**Deliverable**: Alembic migrations para schemas base

```sql
-- Requerimentos
- CREATE SCHEMA intellicare_core
- CREATE TABLE usuarios, organizacoes, roles
- CREATE indices básicos
- CREATE PostgreSQL roles (app_role, analytics_role, consolidation_role)
- RLS policies base

-- Teste
psql -U intellicare -d intellicare_db -f migration.sql
```

#### Task 1.7: Configuração de Redis
**Duração**: 1 dia  
**Responsável**: DevOps  
**Deliverable**: Redis streams configuration

```bash
# Requerimentos
- Redis 7+ rodando
- Consumer groups criados manualmente (scripts)
- Persistence configurada (AOF)
- Backups automatizados

# Teste
redis-cli XINFO STREAM oswaldo_operacional:events:pacientes
```

#### Task 1.8: Testes de integração
**Duração**: 2 dias  
**Responsável**: Dev 1 + Dev 2  
**Deliverable**: Test suite completo

```python
# Requerimentos
- Testes E2E: create → event → read
- Testes de isolamento: operacional vs analítico
- Testes de segurança: rejeitando violações
- Testes de performance: 100+ eventos/s
- Mock Redis e DB para CI

# Teste
pytest tests/ -v --cov --cov-fail-under=85
```

#### Task 1.9: Documentação da Fundação
**Duração**: 1 dia  
**Responsável**: Dev Lead  
**Deliverable**: README, SETUP.md, API docs

```
📄 README.md - O que é intellicare-core
📄 SETUP.md - Como fazer setup local
📄 API.md - Referência de classes/funções
📄 CONTRIBUTING.md - Padrões de código
```

### 🎯 Critérios de Aceitação (Fase 1)

- [ ] intellicare-core publicado em PyPI ou private registry
- [ ] 85%+ test coverage
- [ ] Documentação completa (docstrings, README)
- [ ] Pipeline CI/CD rodando testes automaticamente
- [ ] Code review aprovado
- [ ] Demo para stakeholders

### 📊 Estimativa de Esforço

| Task | Dev 1 | Dev 2 | Dias |
|------|-------|-------|------|
| 1.1  | 1     | -     | 1    |
| 1.2  | 3     | -     | 3    |
| 1.3  | 3     | -     | 3    |
| 1.4  | -     | 2     | 2    |
| 1.5  | -     | 3     | 3    |
| 1.6  | -     | 2 (DevOps) | 2 |
| 1.7  | -     | 1 (DevOps) | 1 |
| 1.8  | 2     | 2     | 2    |
| 1.9  | 1     | -     | 1    |
| **TOTAL** | **11** | **8** | **18 dias** |

---

## 🔄 FASE 2: Implementação Core (Sprint 3-4)

### Objetivo
Integrar separation pattern em todos os 8 módulos LEGO.

### 📝 Tarefas

#### Task 2.1: Análise de cada módulo
**Duração**: 2 dias  
**Responsável**: Dev Lead + Dev 1  
**Deliverable**: Documento de mapeamento

```
Para cada módulo analise:
1. Tabelas existentes no schema atual
2. Quais são operacionais (write-heavy)?
3. Quais são analíticas (read-heavy)?
4. Quais relacionamentos existem?
5. Quais triggers/procedures existem?

Exemplo:
  oswaldo:
    - Operacional: pacientes, monitoramento, alertas
    - Analítico: historico_alertas, metricas_consolidadas
    - Relacionamentos: pacientes → monitoramento (FK)
```

#### Task 2.2-2.9: Migrar cada módulo (8 módulos = 8 tasks)
**Duração**: 2 dias por módulo = 16 dias total  
**Responsável**: Dev 1 + Dev 2 (parallelisar)  
**Deliverable**: Schemas operacional + analítico por módulo

```bash
# Task 2.2: intellicare-auth
# Task 2.3: intellicare-comunicacao
# Task 2.4: intellicare-donabedian
# Task 2.5: intellicare-florence
# Task 2.6: intellicare-geralda
# Task 2.7: intellicare-oswaldo
# Task 2.8: intellicare-portal
# Task 2.9: intellicare-wanda

# Para cada módulo:
1. Criar Alembic migration:
   - CREATE SCHEMA {modulo}_operacional
   - CREATE SCHEMA {modulo}_analitico
   - COPY existing tables → _operacional
   - CREATE new denormalized tables → _analitico

2. Implementar DAOs:
   - {modulo}/data_access/operational_dao.py
   - {modulo}/data_access/analytics_dao.py

3. Usar intellicare-core classes

4. Testes:
   - unit tests de DAO
   - integration tests de separação
   - performance tests

5. Atualizar endpoints FastAPI:
   - Usar OperationalDataAccess para writes
   - Usar AnalyticsDataAccess para reads (se aplicável)
```

**Exemplo Detalhado (oswaldo)**:

```sql
-- Migration SQL
CREATE SCHEMA oswaldo_operacional;
CREATE SCHEMA oswaldo_analitico;

-- Move tabelas existentes
ALTER TABLE oswaldo.pacientes SET SCHEMA oswaldo_operacional;
ALTER TABLE oswaldo.monitoramento SET SCHEMA oswaldo_operacional;

-- Create analytic tables (denormalized)
CREATE TABLE oswaldo_analitico.pacientes_hist (...)
CREATE TABLE oswaldo_analitico.monitoramento_diario (...)
```

```python
# oswaldo/routers/pacientes.py

@router.post("/pacientes", response_model=PacienteResponse)
async def create_paciente(
    data: PacienteCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Usa OperationalDataAccess de intellicare-core
    dao = OperationalDataAccess[Paciente](
        session=session,
        entity_class=Paciente,
        schema='oswaldo_operacional'
    )
    paciente = dao.create(data.dict(), actor_id=current_user.id)
    session.commit()
    return paciente
```

#### Task 2.10: Integração RLS no PostgreSQL
**Duração**: 2 dias  
**Responsável**: DevOps + Dev 1  
**Deliverable**: Row-Level Security policies

```sql
-- Criar roles
CREATE ROLE intellicare_app_role;
CREATE ROLE intellicare_analytics_role;
CREATE ROLE intellicare_consolidation_role;

-- Para cada schema (iterado):
ALTER DEFAULT PRIVILEGES IN SCHEMA {modulo}_operacional
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO intellicare_app_role;

ALTER DEFAULT PRIVILEGES IN SCHEMA {modulo}_analitico
  GRANT SELECT ON TABLES TO intellicare_analytics_role;

-- RLS Policies
ALTER TABLE {modulo}_operacional.{tabela} ENABLE ROW LEVEL SECURITY;
CREATE POLICY no_analytic_write ON {modulo}_analitico.{tabela}
  AS PERMISSIVE FOR UPDATE, DELETE USING (FALSE);
```

#### Task 2.11: Atualizar Alembic para múltiplos schemas
**Duração**: 1 dia  
**Responsável**: DevOps  
**Deliverable**: Script de migração unificado

```python
# alembic/env.py - configurado para todos os schemas
# Toda nova migration auto-detecta ambos schemas

# Comando
alembic upgrade head  # Aplica todas as migrations
```

### 🎯 Critérios de Aceitação (Fase 2)

- [ ] Todos os 8 módulos têm schemas separados
- [ ] RLS policies implementadas e testadas
- [ ] Nenhuma tabela de operacional em analítico
- [ ] Nenhuma escrita possível em analítico desde aplicação
- [ ] 85%+ test coverage em cada módulo
- [ ] Demo de segregação funcionando

### 📊 Estimativa de Esforço

| Task | Estimativa |
|------|-----------|
| 2.1  | 2 dias    |
| 2.2-2.9 (8 módulos) | 16 dias |
| 2.10 | 2 dias    |
| 2.11 | 1 dia     |
| **TOTAL** | **21 dias** |

---

## ⚙️ FASE 3: Consolidação (Sprint 5-6)

### Objetivo
Implementar consolidation service que replica operacional → analítico.

### 📝 Tarefas

#### Task 3.1: Consolidation Service scaffolding
**Duração**: 2 dias  
**Responsável**: Dev 2  
**Deliverable**: Serviço standalone

```bash
# Estrutura
consolidation-service/
├── src/
│   └── consolidation_service/
│       ├── __init__.py
│       ├── main.py
│       ├── consolidator.py         # DataConsolidator
│       ├── event_processor.py       # Event processing logic
│       ├── aggregation.py           # Aggregation functions
│       ├── models.py
│       └── config.py
├── tests/
├── Dockerfile
├── docker-compose.yml
└── README.md
```

#### Task 3.2: Implementar EventProcessor
**Duração**: 3 dias  
**Responsável**: Dev 2  
**Deliverable**: Processador de eventos idempotente

```python
# Requerimentos:
- Consome eventos de Redis Streams
- 1 evento = 1 transaction
- Upsertar em tabela analítica (denormalizado)
- Registrar em audit_trail
- Retry com exponential backoff
- DLQ para falhas permanentes
- 100% test coverage
```

#### Task 3.3: Implementar AggregationEngine
**Duração**: 3 dias  
**Responsável**: Dev 1  
**Deliverable**: Agregações por período

```python
# Requerimentos:
- Calcula agregações: COUNT, SUM, AVG, MAX, MIN
- Agrupa por período: dia, semana, mês
- Materializa em tabelas pré-agregadas
- Indexes para BI queries
- Idempotência (rodadas múltiplas = mesmo resultado)
- 100% test coverage
```

#### Task 3.4: Implementar ConsolidationOrchestrator
**Duração**: 2 dias  
**Responsável**: Dev 2  
**Deliverable**: Orquestração de consolidação

```python
# Requerimentos:
- Scheduled job (cron: 2 AM UTC)
- Processa múltiplos módulos em paralelo (thread pool)
- Healthcheck
- Graceful shutdown
- Restart on failure
```

#### Task 3.5: Monitoramento (Prometheus + Grafana)
**Duração**: 2 dias  
**Responsável**: Dev 2  
**Deliverable**: Métricas e alertas

```python
# Métricas:
- events_published_total
- events_consolidated_total
- replication_lag_seconds
- consolidation_duration_seconds
- security_violations_total

# Alertas:
- ReplicationLag > 1 hour
- ConsolidationFailed
- SecurityViolationDetected
```

#### Task 3.6: Testes E2E de Consolidação
**Duração**: 2 dias  
**Responsável**: Dev 1 + Dev 2  
**Deliverable**: Test suite completo

```python
# Testes:
1. Create event em operacional
2. Publicar em Redis
3. Consolidation consome
4. Valida que tabela analítica foi atualizada
5. Audit trail está correto
6. Responsável é registrado corretamente
```

#### Task 3.7: Documentação de Consolidação
**Duração**: 1 dia  
**Responsável**: Dev Lead  
**Deliverable**: Docs

```
📄 CONSOLIDATION_GUIDE.md - Como funciona consolidação
📄 MONITORING_GUIDE.md - Como monitorar saúde
📄 TROUBLESHOOTING.md - Como debugar problemas
```

### 🎯 Critérios de Aceitação (Fase 3)

- [ ] Consolidation Service roda sem erros por 24h
- [ ] Replication lag < 1 minuto (para eventos de ontem)
- [ ] Zero dados perdidos ou duplicados
- [ ] Audit trail completo
- [ ] Alerts disparam corretamente
- [ ] Failover automático testado

### 📊 Estimativa de Esforço

| Task | Estimativa |
|------|-----------|
| 3.1  | 2 dias    |
| 3.2  | 3 dias    |
| 3.3  | 3 dias    |
| 3.4  | 2 dias    |
| 3.5  | 2 dias    |
| 3.6  | 2 dias    |
| 3.7  | 1 dia     |
| **TOTAL** | **15 dias** |

---

## ✅ FASE 4: Validação e Deploy (Sprint 7+)

### Objetivo
Validar tudo, testar em staging, deploy progressivo em produção.

### 📝 Tarefas

#### Task 4.1: Validação de Separação
**Duração**: 1 dia  
**Responsável**: Dev Lead  
**Deliverable**: Script de auditoria

```python
# Script que valida:
1. Nenhuma FK entre _operacional e _analitico
2. Nenhuma trigger escrevendo em _analitico de aplicação
3. RLS policies ativas em todas as tabelas analíticas
4. Audit log completo
5. Zero violações de segurança registradas

# Executar:
python scripts/audit_separation.py --report report.html
```

#### Task 4.2: Performance Testing
**Duração**: 2 dias  
**Responsável**: Dev 1  
**Deliverable**: Relatório de performance

```
Teste de carga:
- 1000 eventos/seg → operacional
- Consolidation consome dentro de 5 min
- BI queries < 5 segundos
- Sem degradação em operacional durante consolidação
```

#### Task 4.3: Staging Deployment
**Duração**: 2 dias  
**Responsável**: DevOps  
**Deliverable**: Ambiente de staging com tudo

```bash
# Setup:
1. PostgreSQL 15+ com esquemas
2. Redis 7+ com streams
3. Aplicações (consumidores)
4. Consolidation Service
5. Prometheus + Grafana
6. Alertas

# Testes:
1. Criar dados
2. Rodar consolidação
3. Verificar dados em analítico
4. Validar auditoria
```

#### Task 4.4: Testes Funcionais Finais
**Duração**: 1 dia  
**Responsável**: QA + Dev Lead  
**Deliverable**: Report de testes

```
Casos de teste:
1. ✅ Criar paciente → evento publicado → consolidado
2. ✅ Atualizar paciente → evento publicado → consolidado
3. ✅ Deletar paciente → evento publicado → consolidado
4. ✅ BI query em analítico → sem delay operacional
5. ✅ Aplicação tenta escrever em analítico → REJEITADO
6. ✅ Consolidação falha → DLQ + alert
7. ✅ Auditoria completa para rastrear
```

#### Task 4.5: Treinamento da Equipe
**Duração**: 1 dia  
**Responsável**: Dev Lead  
**Deliverable**: Workshop + docs

```
Agenda:
- Hora 1: Visão geral da separação
- Hora 2: Padrões de código (como usar DAO)
- Hora 3: Como adicionar novo módulo
- Hora 4: Troubleshooting comum
```

#### Task 4.6: Runbook de Operação
**Duração**: 1 dia  
**Responsável**: DevOps  
**Deliverable**: Procedimentos

```
📄 OPERATIONAL_RUNBOOK.md
- Como iniciar serviços
- Como monitorar
- Como fazer failover
- Como fazer restore de backup
- Como escalar consolidação
```

#### Task 4.7: Plano de Rollback
**Duração**: 1 dia  
**Responsável**: DevOps + Dev Lead  
**Deliverable**: Procedimento de rollback

```sql
-- Se algo der errado:
1. Parar aplicações
2. Parar consolidation service
3. Verificar audit_log
4. Restore da backup anterior (se necessário)
5. Validate data integrity
6. Restart aplicações
```

#### Task 4.8: Production Deployment
**Duração**: 1 dia (pode ser iterativo)  
**Responsável**: DevOps  
**Deliverable**: Ambiente de produção

```bash
# Phases:
Phase 1 (Canary):  módulo 1 (oswaldo) com 10% traffic
Phase 2 (Ramp):    módulo 1 com 50% traffic
Phase 3 (Full):    módulo 1 com 100% traffic
Phase 4-10:        Repete para demais módulos
```

#### Task 4.9: Post-Deployment Validation
**Duração**: 1 dia  
**Responsável**: Dev Lead + Ops  
**Deliverable**: Checklist validado

```
✅ Aplicação rodando sem erros
✅ Consolidação rodando a cada período
✅ Alerts disparam corretamente
✅ Replication lag aceitável
✅ Zero violações de segurança
✅ Audit logs corretos
```

### 🎯 Critérios de Aceitação (Fase 4)

- [ ] Todos os testes passam (unit, integration, E2E)
- [ ] Performance dentro de SLA
- [ ] Zero downtime deployment
- [ ] Rollback automatizado testado
- [ ] Equipe treinada e confiante
- [ ] Documentação completa

### 📊 Estimativa de Esforço

| Task | Estimativa |
|------|-----------|
| 4.1-4.9 | 10 dias |
| **TOTAL** | **10 dias** |

---

## 📋 Checklist de Entrega

### Código

- [ ] intellicare-core publicado com 85%+ coverage
- [ ] Todos os 8 módulos migrados e testados
- [ ] Consolidation Service em produção
- [ ] Zero code warnings/alerts

### Documentação

- [ ] Especificação Funcional (✅ feito)
- [ ] Especificação Técnica (✅ feito)
- [ ] Guia de Implementação (esse documento)
- [ ] API Documentation
- [ ] Runbook de Operação
- [ ] Guia de Troubleshooting
- [ ] Workshop realizado

### Testes

- [ ] 85%+ unit test coverage
- [ ] 100% integration tests passando
- [ ] Performance tests dentro de SLA
- [ ] E2E tests validando separação
- [ ] Security tests (RLS, violações)

### Monitoramento

- [ ] Prometheus rodando com métricas
- [ ] Grafana dashboards criados
- [ ] Alertas configurados
- [ ] Logs agregados (ELK/Loki)

### Operação

- [ ] Backup/Restore testado
- [ ] Failover automático testado
- [ ] Scaling testado
- [ ] Rollback testado

---

## 🚨 Riscos e Mitigação

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|--------------|-----------|
| Migration de dados falha | CRÍTICO | BAIXA | Backup+restore automático, teste em staging |
| Performance degrada | ALTO | MÉDIA | Load tester antes, índices otimizados |
| RLS bloqueia operação legítima | ALTO | MÉDIA | Whitelist de queries, testes de RLS |
| Consolidação fica atrasada | MÉDIA | MÉDIA | Monitoramento proativo, alertas, scaling |
| Equipe usa DAOs errado | MÉDIA | MÉDIA | Code review, checklist, treinamento |
| Redis data loss | ALTO | BAIXA | AOF persistence, replicação, alertas |

---

## 📊 Métricas de Sucesso

### Técnicas

```
✅ Replication lag < 1 minuto (P99)
✅ Consolidation duration < 5 minutos
✅ Zero eventos perdidos ou duplicados
✅ Error rate < 0.1%
✅ 85%+ test coverage
✅ Query performance no BI < 5 segundos
```

### Operacionais

```
✅ Zero impacto em operações existentes
✅ Deploy sem downtime
✅ Equipe consegue fazer rollback em < 30 min
✅ Alerts são acionados < 1 min de problema
```

### Organizacionais

```
✅ Documentação aprovada por stakeholders
✅ Equipe confiante e treinada
✅ Conformidade LGPD validada
✅ Auditoria de segurança aprovada
```

---

## 📅 Calendar Timeline

```
INÍCIO: 2026-02-11 (Quarta)

FASE 1: Fundação
  Início: 2026-02-11 | Fim: 2026-02-28 | 18 dias

FASE 2: Core Implementation
  Início: 2026-03-03 | Fim: 2026-03-23 | 21 dias

FASE 3: Consolidation
  Início: 2026-03-24 | Fim: 2026-04-07 | 15 dias

FASE 4: Validation & Deploy
  Início: 2026-04-08 | Fim: 2026-04-18 | 10 dias

FIM: 2026-04-18 (Sexta) - ~66 dias totais

Próximas refinements + feedback: 2-4 semanas
```

---

**Próximo Passo**: Atualizar este plano com datas reais e iniciar Sprint 1.
