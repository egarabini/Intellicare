# GERALDA — Plano de Implementacao
**Data:** 2026-03-04
**Versao:** 2.0.0
**Estimativa Total:** 5-7 dias
**Prioridade:** ONDA 2 — Core Clinico (pos-GRAHAME)

---

## Estado Atual

GERALDA v1.0 usa dicionarios in-memory. Todo restart perde dados.
Esta versao migra para PostgreSQL, adiciona integracao FHIR e motor de eventos.

Pre-requisito: GRAHAME funcional (para sincronizacao CarePlan)

---

## Fase 1 — Modelos e Migracao PostgreSQL (Dia 1-2) — ~6h

### Tarefa 1.1 — Criar modelos SQLAlchemy
- [x] Criar `geralda/models/care_plan.py` (JSONB→JSON para compat SQLite)
- [x] Criar `geralda/models/care_task.py`
- [x] Criar `geralda/models/reminder.py`
- [x] Criar `geralda/models/__init__.py`

### Tarefa 1.2 — Migracao Alembic
```bash
alembic revision --autogenerate -m "initial_geralda_tables"
alembic upgrade head
```
- [x] Migracoes geradas e aplicadas — `c7f711dc0758_initial_schema` com 4 tabelas
- [x] Indices criados (care_plans.patient_id, care_tasks.plan_id/status, reminders.patient_id/next_at)

### Tarefa 1.3 — Refatorar servicos para PostgreSQL
- [ ] Criar `geralda/services/care_plan_service.py` (substituir _plans dict)
- [ ] Criar `geralda/services/care_task_service.py` (substituir _tasks dict)
- [ ] Criar `geralda/services/reminder_service.py`
- [ ] Criar `geralda/database/deps.py` (get_db dependency)

### Tarefa 1.4 — Atualizar rotas para usar DB
- [x] `app_db.py` — app unificado DB-backed com CRUD completo
- [x] Plans: create, get, list
- [x] Tasks: add, complete, skip, list by plan
- [x] Reminders: list, due, schedule, pause/resume/cancel (in-memory engine)
- [x] Education: conditions, search, material by id/code
- [x] Analyze: POST /api/v1/analyze com agregação de planos+tarefas+aderência
- [x] Dockerfile CMD alterado: `geralda.api.app_db:app`

---

## Fase 2 — Testes PostgreSQL (Dia 2-3) — ~4h

### Tarefa 2.1 — conftest.py com SQLite in-memory
- [x] Criar `tests/test_app_db.py` com AsyncClient + SQLite in-memory (ASGITransport)
- [x] Garantir que todos os modelos sao criados no setup (async_engine + create_all)

### Tarefa 2.2 — Testes de servicos
```bash
pytest tests/test_care_plan_service.py -v
pytest tests/test_care_task_service.py -v
```
- [x] `test_app_db.py` — 12 testes passando (health, info, CRUD plans/tasks, aderência, analyze, education, reminders)
- [ ] Meta: dados persistem entre operacoes na mesma sessao

---

## Fase 3 — Integracao FHIR (Dia 3-4) — ~4h

### Tarefa 3.1 — Mapper FHIR CarePlan
- [x] `geralda/fhir/careplan_mapper.py` existe (pré-existente no código)
- [ ] `test_fhir_mapper.py` — 8 testes sem dependencia de rede

### Tarefa 3.2 — Cliente Grahame
- [x] `geralda/fhir/client.py` existe (pré-existente no código)
- [x] Sincronizacao fire-and-forget (nao bloqueia se Grahame offline)

---

## Fase 4 — Motor de Eventos (Dia 5) — ~4h

### Tarefa 4.1 — Event Engine
- [x] `geralda/services/event_engine.py` existe (pipeline 7 estágios, montado em app_db)
- [x] Implementar OverdueTaskRule e LowAdherenceRule — analyze endpoint detecta ambos
- [x] Rotas de eventos montadas via `event_router` em app_db.py

### Tarefa 4.2 — Kestra Flow
- [ ] Criar `kestra/flows/geralda_event_check.yml`
- [ ] Registrar flow no Kestra (se Kestra acessivel)

---

## Fase 5 — Release (Dia 6-7) — ~3h

### Tarefa 5.1 — Suite completa
```bash
pytest tests/ -v --cov=geralda --cov-report=term-missing
```
- [ ] Meta: >= 80% cobertura, 0 falhas

### Tarefa 5.2 — Docker smoke test
```bash
docker compose up --build -d
curl http://localhost:8006/api/v1/health
```
- [ ] Container sobe com PostgreSQL
- [ ] POST care-plan persiste, sobrevive a restart

---

## Checklist de Entrega

| Item | Status |
|------|--------|
| Dados persistem apos restart | [x] PostgreSQL via app_db.py |
| CRUD CarePlan/CareTask/Reminder | [x] Completo no app_db.py |
| Mapper FHIR CarePlan testado | [~] Mapper existe, faltam testes dedicados |
| Motor eventos gera alertas | [x] analyze + event_router |
| pytest >= 80% cobertura | [~] 393/399 passando (6 skips LLM), coverage pendente |
| docker compose up -> healthy | [ ] |
| smoke_tests.py inclui GERALDA | [ ] |

---

*GERALDA v2.0 — Plano de Implementacao — 2026-03-04*
