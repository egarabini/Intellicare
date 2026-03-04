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
- [ ] Criar `geralda/models/care_plan.py` (ver spec tecnica)
- [ ] Criar `geralda/models/care_task.py`
- [ ] Criar `geralda/models/reminder.py`
- [ ] Criar `geralda/models/__init__.py`

### Tarefa 1.2 — Migracao Alembic
```bash
alembic revision --autogenerate -m "initial_geralda_tables"
alembic upgrade head
```
- [ ] Migracoes geradas e aplicadas
- [ ] Indices criados (verificar com \d+ no psql)

### Tarefa 1.3 — Refatorar servicos para PostgreSQL
- [ ] Criar `geralda/services/care_plan_service.py` (substituir _plans dict)
- [ ] Criar `geralda/services/care_task_service.py` (substituir _tasks dict)
- [ ] Criar `geralda/services/reminder_service.py`
- [ ] Criar `geralda/database/deps.py` (get_db dependency)

### Tarefa 1.4 — Atualizar rotas para usar DB
- [ ] `routes/care_plans.py` — injetar AsyncSession
- [ ] `routes/care_tasks.py` — injetar AsyncSession
- [ ] `routes/reminders.py` — injetar AsyncSession

---

## Fase 2 — Testes PostgreSQL (Dia 2-3) — ~4h

### Tarefa 2.1 — conftest.py com SQLite in-memory
- [ ] Criar `tests/conftest.py` com fixture de sessao (ver spec tecnica)
- [ ] Garantir que todos os modelos sao criados no setup

### Tarefa 2.2 — Testes de servicos
```bash
pytest tests/test_care_plan_service.py -v
pytest tests/test_care_task_service.py -v
```
- [ ] `test_care_plan_service.py` — 10 testes passando
- [ ] `test_care_task_service.py` — 10 testes passando
- [ ] Meta: dados persistem entre operacoes na mesma sessao

---

## Fase 3 — Integracao FHIR (Dia 3-4) — ~4h

### Tarefa 3.1 — Mapper FHIR CarePlan
- [ ] Criar `geralda/fhir/careplan_mapper.py` (ver spec tecnica)
- [ ] `test_fhir_mapper.py` — 8 testes sem dependencia de rede

### Tarefa 3.2 — Cliente Grahame
- [ ] Criar `geralda/fhir/client.py`
- [ ] Sincronizacao fire-and-forget (nao bloqueia se Grahame offline)

---

## Fase 4 — Motor de Eventos (Dia 5) — ~4h

### Tarefa 4.1 — Event Engine
- [ ] Criar `geralda/services/event_engine.py`
- [ ] Implementar OverdueTaskRule e LowAdherenceRule
- [ ] Endpoint `POST /api/v1/internal/run-event-check`

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
| Dados persistem apos restart | [ ] |
| CRUD CarePlan/CareTask/Reminder | [ ] |
| Mapper FHIR CarePlan testado | [ ] |
| Motor eventos gera alertas | [ ] |
| pytest >= 80% cobertura | [ ] |
| docker compose up -> healthy | [ ] |
| smoke_tests.py inclui GERALDA | [ ] |

---

*GERALDA v2.0 — Plano de Implementacao — 2026-03-04*
