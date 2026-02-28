# Análise da Estrutura Geralda - 2026-02-24 10:15

## Estrutura Atual

### Diretórios
```
intellicare-geralda/
├── geralda/
│   ├── api/           # FastAPI routes
│   ├── engine/        # Lógica de negócio (in-memory)
│   │   ├── care_manager.py
│   │   ├── reminder_engine.py
│   │   └── models.py  # ← Dataclasses atuais (in-memory)
│   └── config.py
├── migrations/        # Alembic (já configurado!)
├── tests/
└── alembic.ini
```

### Modelos Atuais (Dataclasses)

**Localização:** `geralda/engine/models.py`

**Estrutura:**
1. `CareTask` - Tarefa de cuidado (dataclass)
2. `CarePlan` - Plano de cuidado (dataclass)
3. Enums: `TaskStatus`, `TaskCategory`, `ReminderFrequency`, `ReminderStatus`

**Problema:** Tudo fica em memória! Perde dados no restart.

## Objetivo da Migração

Converter dataclasses → SQLAlchemy ORM:

### 1. CarePlan (Tabela: care_plans)
```python
Colunas:
  - id (UUID PK)
  - patient_id (String, indexado)
  - patient_name (String)
  - conditions (JSONB)
  - goals (JSONB)
  - active (Boolean)
  - created_at (DateTime)
  - updated_at (DateTime)
  - deactivated_at (DateTime, nullable)
  - deactivation_reason (String, nullable)
```

### 2. CareTask (Tabela: care_tasks)
```python
Colunas:
  - id (UUID PK)
  - plan_id (UUID FK → care_plans)
  - patient_id (String, indexado)
  - title (String)
  - description (Text)
  - category (Enum)
  - status (Enum)
  - due_date (Date)
  - due_time (String)
  - completed_at (DateTime)
  - completed_by (String, nullable)
  - notes (Text)
  - recurrence_rule (String, nullable)
```

### 3. Reminder (Tabela: reminders)
```python
Colunas:
  - id (UUID PK)
  - plan_id (UUID FK → care_plans)
  - patient_id (String, indexado)
  - task_id (UUID FK → care_tasks, nullable)
  - message (Text)
  - scheduled_at (DateTime)
  - sent_at (DateTime, nullable)
  - channel (String)
  - status (Enum)
```

### 4. EducationalMaterial (Tabela: educational_materials)
```python
Colunas:
  - id (UUID PK)
  - plan_id (UUID FK → care_plans)
  - patient_id (String, indexado)
  - title (String)
  - content (Text)
  - category (String)
  - condition_codes (JSONB)
  - language (String)
  - created_at (DateTime)
```

## Índices Necessários

```sql
CREATE INDEX idx_care_plans_patient_id ON care_plans(patient_id);
CREATE INDEX idx_care_plans_active ON care_plans(active);
CREATE INDEX idx_care_tasks_plan_id ON care_tasks(plan_id);
CREATE INDEX idx_care_tasks_patient_id ON care_tasks(patient_id);
CREATE INDEX idx_care_tasks_status ON care_tasks(status);
CREATE INDEX idx_care_tasks_due_date ON care_tasks(due_date);
CREATE INDEX idx_reminders_patient_id ON reminders(patient_id);
CREATE INDEX idx_reminders_scheduled_at ON reminders(scheduled_at);
```

## Próximos Passos

1. Criar estrutura `geralda/models/` com modelos SQLAlchemy
2. Criar `geralda/database/` com session factory
3. Configurar Alembic para detectar novos modelos
4. Gerar migração inicial
5. Atualizar services para usar ORM

