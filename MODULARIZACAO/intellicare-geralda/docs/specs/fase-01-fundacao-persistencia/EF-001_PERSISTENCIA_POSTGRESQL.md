# EF-001 — Persistencia PostgreSQL

> Migrar o armazenamento em memoria da Geralda v1.0 para PostgreSQL com Alembic.

## 1. Objetivo

Substituir os dicionarios em memoria (`_plans`, `_tasks`, `_reminders`) por tabelas PostgreSQL, garantindo que os dados de planos de cuidado, tarefas, lembretes e materiais educativos sobrevivam a reinicializacoes e sejam consistentes em ambientes multi-instancia.

## 2. Justificativa

- **v1.0 e efemera**: Toda reinicializacao do container perde todos os dados
- **Escalabilidade**: Multiplas instancias da Geralda nao compartilham estado
- **Auditoria**: Sem banco, nao ha historico de alteracoes
- **Integracao**: Outros modulos e dashboards precisam consultar dados persistidos

## 3. Escopo

### 3.1 Tabelas a Criar

#### `care_plans`
| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | UUID (PK) | Identificador unico |
| patient_id | VARCHAR(64) NOT NULL | ID do paciente (FHIR Patient.id) |
| patient_name | VARCHAR(255) | Nome do paciente |
| conditions | JSONB NOT NULL | Lista de codigos ICD-10 (ex: ["N18.3", "E11"]) |
| goals | JSONB | Lista de metas terapeuticas |
| active | BOOLEAN DEFAULT TRUE | Plano ativo ou encerrado |
| created_at | TIMESTAMPTZ NOT NULL | Data de criacao |
| updated_at | TIMESTAMPTZ NOT NULL | Ultima atualizacao |
| created_by | VARCHAR(64) | ID do profissional que criou |
| deactivated_at | TIMESTAMPTZ | Data de encerramento |
| deactivation_reason | TEXT | Motivo do encerramento |

**Indices**: `idx_care_plans_patient_id`, `idx_care_plans_active`

#### `care_tasks`
| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | UUID (PK) | Identificador unico |
| plan_id | UUID (FK -> care_plans.id) | Plano pai |
| patient_id | VARCHAR(64) NOT NULL | ID do paciente (desnormalizado para queries) |
| title | VARCHAR(255) NOT NULL | Titulo curto da tarefa |
| description | TEXT | Descricao detalhada |
| category | VARCHAR(20) NOT NULL | Enum: medication, exercise, diet, exam, appointment, monitoring, education, other |
| status | VARCHAR(20) NOT NULL DEFAULT 'pending' | Enum: pending, completed, skipped, overdue |
| due_date | DATE | Data prevista |
| due_time | VARCHAR(5) | Horario HH:MM |
| completed_at | TIMESTAMPTZ | Quando foi concluida |
| completed_by | VARCHAR(64) | Quem completou (paciente ou profissional) |
| notes | TEXT | Observacoes |
| created_at | TIMESTAMPTZ NOT NULL | Data de criacao |
| recurrence_rule | VARCHAR(50) | Regra de recorrencia (ex: "daily", "weekly:1,3,5") |

**Indices**: `idx_care_tasks_plan_id`, `idx_care_tasks_patient_id`, `idx_care_tasks_status`, `idx_care_tasks_due_date`

#### `reminders`
| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | UUID (PK) | Identificador unico |
| patient_id | VARCHAR(64) NOT NULL | ID do paciente |
| title | VARCHAR(255) NOT NULL | Titulo do lembrete |
| message | TEXT NOT NULL | Mensagem completa |
| frequency | VARCHAR(20) NOT NULL | Enum: once, daily, weekly, monthly |
| time | VARCHAR(5) NOT NULL | Horario HH:MM |
| status | VARCHAR(20) NOT NULL DEFAULT 'active' | Enum: active, paused, completed, cancelled |
| start_date | DATE | Data de inicio |
| end_date | DATE | Data de fim |
| days_of_week | JSONB | Lista de dias (0=seg, 6=dom) para weekly |
| last_sent | TIMESTAMPTZ | Ultima vez que foi enviado |
| send_count | INTEGER DEFAULT 0 | Contagem de envios |
| category | VARCHAR(50) DEFAULT 'general' | Categoria (medication, appointment, exam, general) |
| created_at | TIMESTAMPTZ NOT NULL | Data de criacao |
| created_by | VARCHAR(64) | Quem criou |

**Indices**: `idx_reminders_patient_id`, `idx_reminders_status`, `idx_reminders_frequency`

#### `education_materials`
| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | VARCHAR(20) (PK) | ID legivel (ex: "ckd-001") |
| condition_code | VARCHAR(10) NOT NULL | Codigo ICD-10 (N18, E11, I10) |
| condition_name | VARCHAR(100) NOT NULL | Nome da condicao em portugues |
| title | VARCHAR(255) NOT NULL | Titulo do material |
| content | TEXT NOT NULL | Conteudo em markdown |
| language | VARCHAR(10) DEFAULT 'pt-BR' | Idioma |
| reading_level | VARCHAR(20) DEFAULT 'basic' | Nivel: basic, intermediate, advanced |
| tags | JSONB | Lista de tags para busca |
| source | VARCHAR(50) DEFAULT 'yaml' | Origem: yaml, ai_generated, professional |
| active | BOOLEAN DEFAULT TRUE | Se o material esta ativo |
| created_at | TIMESTAMPTZ NOT NULL | Data de criacao |
| updated_at | TIMESTAMPTZ NOT NULL | Ultima atualizacao |

**Indices**: `idx_education_condition_code`, `idx_education_tags` (GIN)

#### `audit_log`
| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | BIGSERIAL (PK) | ID sequencial |
| entity_type | VARCHAR(30) NOT NULL | plan, task, reminder, education |
| entity_id | VARCHAR(64) NOT NULL | ID da entidade |
| action | VARCHAR(20) NOT NULL | created, updated, deleted, completed, skipped |
| actor_id | VARCHAR(64) | Quem fez a acao |
| actor_type | VARCHAR(20) | patient, professional, system, ai |
| details | JSONB | Detalhes da alteracao (campos antes/depois) |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT NOW() | Timestamp |

**Indices**: `idx_audit_entity`, `idx_audit_actor`, `idx_audit_created_at`

### 3.2 Camada de Acesso a Dados

Criar `geralda/database/` com:

```
geralda/database/
  __init__.py
  connection.py      # AsyncEngine, SessionLocal, get_db dependency
  models.py          # SQLAlchemy ORM models
  repositories/
    __init__.py
    care_plan_repo.py     # CarePlanRepository (CRUD + queries)
    care_task_repo.py     # CareTaskRepository
    reminder_repo.py      # ReminderRepository
    education_repo.py     # EducationRepository
    audit_repo.py         # AuditRepository
```

### 3.3 Padrao Repository

Cada repository deve implementar:

```python
class CarePlanRepository:
    async def create(self, plan: CarePlanCreate) -> CarePlan
    async def get_by_id(self, plan_id: UUID) -> Optional[CarePlan]
    async def list_by_patient(self, patient_id: str, active_only: bool = True) -> list[CarePlan]
    async def update(self, plan_id: UUID, data: CarePlanUpdate) -> Optional[CarePlan]
    async def deactivate(self, plan_id: UUID, reason: str) -> Optional[CarePlan]
    async def count_by_patient(self, patient_id: str) -> int
```

### 3.4 Migracoes Alembic

- `alembic/versions/001_initial_schema.py` — Cria todas as tabelas
- `alembic/versions/002_seed_education.py` — Insere os 11 materiais educativos YAML existentes
- `alembic/env.py` — Configurado para async (asyncpg)

### 3.5 Compatibilidade API

**CRITICO**: A API REST (24 endpoints) deve manter 100% de compatibilidade com v1.0.

Os engines (`CareManager`, `ReminderEngine`, `ContentLoader`) devem ser refatorados para usar os repositories como backend, mas mantendo a mesma interface publica.

Padrao sugerido:

```python
class CareManager:
    def __init__(self, repo: CarePlanRepository, task_repo: CareTaskRepository):
        self._repo = repo
        self._task_repo = task_repo

    async def create_plan(self, patient_id, conditions, ...) -> CarePlan:
        # Mesma assinatura, agora persiste no banco
        plan = await self._repo.create(...)
        await self._audit("plan", plan.id, "created", ...)
        return plan
```

## 4. Configuracao

Novas variaveis de ambiente:

```env
# PostgreSQL
INTELLICARE_DATABASE_URL=postgresql+asyncpg://geralda:senha@localhost:5432/intellicare
INTELLICARE_DATABASE_SCHEMA=intellicare_geralda
INTELLICARE_DATABASE_POOL_SIZE=5
INTELLICARE_DATABASE_MAX_OVERFLOW=10

# Migracao
INTELLICARE_AUTO_MIGRATE=false
```

## 5. Docker Compose

Atualizar `docker-compose.yml` para incluir PostgreSQL:

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: intellicare
      POSTGRES_USER: geralda
      POSTGRES_PASSWORD: ${DB_PASSWORD:-geralda_dev}
    volumes:
      - geralda_pgdata:/var/lib/postgresql/data
    ports:
      - "${DB_PORT:-5436}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U geralda"]

  api:
    depends_on:
      db:
        condition: service_healthy
    environment:
      - INTELLICARE_DATABASE_URL=postgresql+asyncpg://geralda:${DB_PASSWORD:-geralda_dev}@db:5432/intellicare

volumes:
  geralda_pgdata:
```

## 6. Testes

### 6.1 Testes Unitarios (Repositories)
- Usar `pytest-asyncio` + banco de teste em memoria (SQLite async) ou testcontainers
- Cada repository: CRUD completo, filtros, edge cases
- Minimo 30 testes novos

### 6.2 Testes de Integracao
- Migracoes Alembic: upgrade/downgrade
- Seed de dados educativos
- Concorrencia (2 requests simultaneas)

### 6.3 Testes de Regressao
- TODOS os 108 testes existentes devem continuar passando
- API retorna mesmos JSONs da v1.0

## 7. Criterios de Aceitacao

- [ ] Todas as tabelas criadas com migracoes Alembic
- [ ] 11 materiais educativos migrados dos YAML para o banco
- [ ] 24 endpoints mantendo mesmo contrato JSON
- [ ] 108 testes existentes passando (regressao)
- [ ] 30+ testes novos para repositories e migracoes
- [ ] Audit log registrando todas as operacoes de escrita
- [ ] Docker compose funcional com PostgreSQL
- [ ] Documentacao de configuracao atualizada
- [ ] Cobertura >= 90%

## 8. Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|-----------|
| Quebra de contrato API | Testes de regressao automatizados |
| Performance com banco | Indices otimizados + connection pool |
| Migracoes em producao | Alembic com versionamento |
| Dados YAML orfaos | Script de seed na migracao 002 |

## 9. Estimativa de Complexidade

- **Arquivos novos**: ~12
- **Arquivos modificados**: ~6 (engines + config + docker)
- **Linhas estimadas**: ~1.500
- **Testes novos**: ~30
