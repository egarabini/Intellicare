# GERALDA — Especificacoes Tecnicas
**Data:** 2026-03-04
**Versao:** 2.0.0
**Modulo:** intellicare-geralda (porta 8006)

---

## 1. Stack Tecnologica

| Componente | Tecnologia |
|-----------|-----------|
| Runtime | Python 3.11 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x async |
| Banco | PostgreSQL 15 |
| LLM | Ollama (qwen2.5:7b) para linguagem acessivel |
| Cache/Fila | Redis (intellicare-core) |
| Workflow | Kestra (motor de eventos periodicos) |
| Testes | pytest + pytest-asyncio + aiosqlite |

---

## 2. Modelos SQLAlchemy (a criar)

### CarePlan
```python
# geralda/models/care_plan.py
class CarePlan(Base):
    __tablename__ = "care_plans"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[str] = mapped_column(index=True)
    patient_name: Mapped[str]
    conditions: Mapped[list] = mapped_column(JSONB)   # lista de CID-10
    goals: Mapped[list] = mapped_column(JSONB)         # metas clinicas
    active: Mapped[bool] = mapped_column(default=True, index=True)
    fhir_id: Mapped[Optional[str]]                     # ID no GRAHAME
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime]
    created_by: Mapped[Optional[str]]
    deactivated_at: Mapped[Optional[datetime]]
    deactivation_reason: Mapped[Optional[str]]
    tenant_id: Mapped[str] = mapped_column(index=True)
```

### CareTask
```python
class CareTask(Base):
    __tablename__ = "care_tasks"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("care_plans.id"), index=True)
    patient_id: Mapped[str] = mapped_column(index=True)
    title: Mapped[str]
    description: Mapped[Optional[str]]
    category: Mapped[str]   # medication, exercise, diet, exam, monitoring
    status: Mapped[str]     # pending, completed, skipped, overdue
    due_date: Mapped[Optional[date]] = mapped_column(index=True)
    due_time: Mapped[Optional[time]]
    completed_at: Mapped[Optional[datetime]]
    completed_by: Mapped[Optional[str]]
    recurrence_rule: Mapped[Optional[str]]  # RRULE format
    tenant_id: Mapped[str]
```

### Reminder
```python
class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("care_plans.id"))
    patient_id: Mapped[str]
    task_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("care_tasks.id"))
    message: Mapped[str]
    scheduled_at: Mapped[datetime] = mapped_column(index=True)
    sent_at: Mapped[Optional[datetime]]
    channel: Mapped[str]    # whatsapp, sms, email
    status: Mapped[str]     # pending, sent, failed
    tenant_id: Mapped[str]
```

---

## 3. Endpoints da API

```
# BaseAgent
GET  /api/v1/health
GET  /api/v1/info
POST /api/v1/analyze

# Planos de Cuidado
GET    /api/v1/care-plans              → List[CarePlan] (query: patient_id)
POST   /api/v1/care-plans              → CarePlan
GET    /api/v1/care-plans/{id}         → CarePlan
PATCH  /api/v1/care-plans/{id}         → CarePlan
DELETE /api/v1/care-plans/{id}         → 204 (soft deactivate)
GET    /api/v1/care-plans/{id}/adherence → AdherenceReport

# Tarefas
GET    /api/v1/care-tasks              → List[CareTask] (query: plan_id, status)
POST   /api/v1/care-tasks              → CareTask
PATCH  /api/v1/care-tasks/{id}/complete → CareTask
PATCH  /api/v1/care-tasks/{id}/skip    → CareTask

# Lembretes
GET    /api/v1/reminders               → List[Reminder] (query: patient_id, status)
POST   /api/v1/reminders               → Reminder
DELETE /api/v1/reminders/{id}          → 204

# Educacao
GET    /api/v1/educational-materials   → List[EducationalMaterial] (query: condition)
GET    /api/v1/educational-materials/{id} → EducationalMaterial

# Interno (para motor de eventos / Kestra)
POST   /api/v1/internal/run-event-check → EventCheckResult
```

---

## 4. FHIR CarePlan Mapper

```python
# geralda/fhir/careplan_mapper.py

def to_fhir_careplan(plan: CarePlan, tasks: list[CareTask]) -> dict:
    return {
        "resourceType": "CarePlan",
        "id": plan.fhir_id or str(plan.id),
        "status": "active" if plan.active else "completed",
        "intent": "plan",
        "title": f"Plano de cuidado — {plan.patient_name}",
        "subject": {"reference": f"Patient/{plan.patient_id}"},
        "period": {"start": plan.created_at.isoformat()},
        "category": [
            {
                "coding": [{
                    "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
                    "code": "assess-plan"
                }]
            }
        ],
        "activity": [
            {
                "detail": {
                    "status": task.status,
                    "description": task.title,
                    "scheduledPeriod": {
                        "start": task.due_date.isoformat() if task.due_date else None
                    }
                }
            }
            for task in tasks
        ]
    }
```

---

## 5. Motor de Eventos (Kestra Flow)

```yaml
# kestra/flows/geralda_event_check.yml
id: geralda_event_check
namespace: intellicare
description: "Verificacao periodica de eventos Geralda"

triggers:
  - type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 * * * *"  # de hora em hora

tasks:
  - id: check_events
    type: io.kestra.plugin.core.http.Request
    uri: "http://geralda:8006/api/v1/internal/run-event-check"
    method: POST
    headers:
      Content-Type: application/json
    body: '{"dry_run": false}'
```

**Regras implementadas no event check:**
```python
# geralda/services/event_engine.py
RULES = [
    OverdueTaskRule(threshold_days=3),      # tarefa vencida -> alerta WANDA
    LowAdherenceRule(threshold_pct=50, window_days=7), # adesao baixa -> alerta
    NewConditionRule(),                       # nova condicao -> sugerir tarefas
]
```

---

## 6. Configuracao

```env
DATABASE_URL=postgresql+asyncpg://intellicare:password@postgres:5432/intellicare
REDIS_URL=redis://redis:6379/0
GRAHAME_URL=http://grahame:8012/api/v1
COMUNICACAO_URL=http://comunicacao:8005/api/v1
WANDA_URL=http://wanda:8004/api/v1
OLLAMA_URL=http://ollama:11434
ENABLE_LLM_SIMPLIFICATION=true
KESTRA_API_URL=http://kestra:8080
PORT=8000
```

---

## 7. Testes (conftest.py padrao)

```python
@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:",
                                  connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as s:
        yield s
```

Meta de testes:
- `test_care_plan_service.py` — 10 testes
- `test_care_task_service.py` — 10 testes
- `test_fhir_mapper.py` — 8 testes
- `test_event_engine.py` — 5 testes
- `test_routes.py` — 8 testes

---

*GERALDA v2.0 — Especificacoes Tecnicas — 2026-03-04*
