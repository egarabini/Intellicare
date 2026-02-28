# RESUMO - FASE 1.2.A - Modelos SQLAlchemy + Alembic

**Data:** 2026-02-24 10:35
**Status:** ✅ CONCLUÍDA

## Estrutura Criada

```
intellicare-geralda/
└── geralda/
    ├── models/              ← NOVO
    │   ├── __init__.py
    │   ├── care_plan.py     ✅ Criado
    │   ├── care_task.py     ✅ Criado
    │   ├── reminder.py       ✅ Criado
    │   └── educational_material.py ✅ Criado
    └── database/            ← NOVO
        ├── __init__.py
        ├── base.py          ✅ Criado
        └── deps.py          ✅ Criado
```

## Modelos Criados (4)

### 1. CarePlan (care_plans)
- **Tabela:** PostgreSQL
- **Colunas:**
  - `id` (UUID PK)
  - `patient_id` (String, indexado)
  - `patient_name` (String)
  - `conditions` (JSONB)
  - `goals` (JSONB)
  - `active` (Boolean, indexado)
  - `created_at`, `updated_at` (DateTime)
  - `deactivated_at`, `deactivation_reason` (nullable)

- **Índices:**
  - `idx_care_plans_patient_id`
  - `idx_care_plans_active`

### 2. CareTask (care_tasks)
- **Colunas:**
  - `id` (UUID PK)
  - `plan_id` (UUID FK, indexado)
  - `patient_id` (String, indexado)
  - `title`, `description`
  - `category` (Enum: MEDICATION, EXERCISE, DIET, etc.)
  - `status` (Enum: PENDING, COMPLETED, SKIPPED, OVERDUE)
  - `due_date` (Date, indexado)
  - `due_time` (String HH:MM)
  - `completed_at`, `completed_by`
  - `notes`, `recurrence_rule`

- **Índices:**
  - `idx_care_tasks_plan_id`
  - `idx_care_tasks_patient_id`
  - `idx_care_tasks_status`
  - `idx_care_tasks_due_date`

### 3. Reminder (reminders)
- **Colunas:**
  - `id` (UUID PK)
  - `plan_id` (UUID FK, indexado)
  - `patient_id` (String, indexado)
  - `task_id` (UUID FK nullable, indexado)
  - `message` (Text)
  - `scheduled_at` (DateTime, indexado)
  - `sent_at` (DateTime nullable)
  - `channel` (String: email, sms, whatsapp, push)
  - `status` (Enum: PENDING, SENT, FAILED, CANCELLED)

- **Índices:**
  - `idx_reminders_patient_id`
  - `idx_reminders_scheduled_at`

### 4. EducationalMaterial (educational_materials)
- **Colunas:**
  - `id` (UUID PK)
  - `plan_id` (UUID FK, indexado)
  - `patient_id` (String, indexado)
  - `title`, `content`, `category`
  - `condition_codes` (JSONB)
  - `language` (String, default "pt-BR")
  - `created_at` (DateTime)

- **Índices:**
  - `idx_educational_materials_plan_id`
  - `idx_educational_materials_patient_id`

## Database Infrastructure Criada

### Base.py
- `Base` class (AsyncAttrs + DeclarativeBase)
- `get_engine()` - Cria AsyncEngine
- `get_session_factory()` - Cra sessionmaker assíncrono

### Deps.py
- `get_db()` - FastAPI dependency para injeção de sessão

## Próximos Passos (1.2.A Continuação)

- [ ] Configurar Alembic para detectar novos modelos
- [ ] Gerar migração: `alembic revision --autogenerate -m "initial_geralda_tables"`
- [ ] Aplicar migração: `alembic upgrade head`
- [ ] Atualizar `geralda/api/app.py` para criar engine no lifespan

## Critérios de Aceite (Parcial)

- [x] 4 modelos SQLAlchemy criados ✅
- [x] Database infrastructure criada ✅
- [ ] Migração Alembic gerada ⏳
- [ ] Migração aplicada ⏳
- [ ] Engine configurado no app ⏳
