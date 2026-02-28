# FASE 1.2 - GERALDA v2.0 Fase 1: Persistência PostgreSQL

**Data de início:** 2026-02-24 10:15
**Responsável:** DEV0
**Prioridade:** 🔴 BLOQUEADOR
**Status:** 🔄 EM ANDAMENTO (BLOQUEIO 1.2.C REMOVIDO)

## Contexto

Geralda v1.0 usa dicionários em memória (`_plans`, `_tasks`, `_reminders`). Todo restart perde dados. Esta fase migra para PostgreSQL.

## Especificação

**Spec:** `intellicare-geralda/docs/specs/fase-01-fundacao-persistencia/EF-001_PERSISTENCIA_POSTGRESQL.md`

## Objetivo

Criar modelos SQLAlchemy + Alembic para persistir:
- CarePlan (planos de cuidado)
- CareTask (tarefas dos planos)
- Reminder (lembretes)
- EducationalMaterial (materiais educacionais)

## Tarefas

### 1.2.A - Modelos SQLAlchemy + Alembic

- [ ] ⚙️ Criar `geralda/models/care_plan.py` - modelo `CarePlan`
- [ ] ⚙️ Criar `geralda/models/care_task.py` - modelo `CareTask`
- [ ] ⚙️ Criar `geralda/models/reminder.py` - modelo `Reminder`
- [ ] ⚙️ Criar `geralda/models/educational_material.py` - modelo `EducationalMaterial`
- [ ] ⚙️ Criar `geralda/models/__init__.py` - exportar todos os modelos
- [ ] ⚙️ Gerar migração Alembic: `alembic revision --autogenerate -m "initial_geralda_tables"`
- [ ] ⚙️ Aplicar migração: `alembic upgrade head`
- [ ] ⚙️ Atualizar `geralda/api/app.py` - lifespan cria engine PostgreSQL

### 1.2.B - Refatorar Serviços

- [ ] ⚙️ Criar `geralda/services/care_plan_service.py`
- [ ] ⚙️ Criar `geralda/services/care_task_service.py`
- [ ] ⚙️ Criar `geralda/services/reminder_service.py`
- [ ] ⚙️ Criar `geralda/database/deps.py` - `get_db()` dependency
- [ ] ⚙️ Atualizar rotas em `geralda/api/routes/` - injetar `db: AsyncSession`

### 1.2.C - Testes PostgreSQL

- [ ] ⚙️ Criar `tests/conftest.py` com fixture de sessão (SQLite in-memory)
- [ ] 🧪 Criar `tests/test_care_plan_service.py` - mínimo 10 testes
- [ ] 🧪 Criar `tests/test_care_task_service.py` - mínimo 10 testes
- [ ] 🧪 Atualizar `tests/test_routes.py` - usar fixture de DB real
- [ ] 🧪 Meta: `pytest -q` → **≥ 80% cobertura, 0 falhas**

## Critérios de Aceite EF-001

- [ ] Todos os dados persistem após restart do container
- [ ] Queries por `patient_id` usam índice (verificar com EXPLAIN)
- [ ] Testes passando com SQLite in-memory no CI

## Log de Progresso

### 2026-02-24 10:15 - Início da FASE 1.2
- Criada estrutura de pastas para documentação
- Próximo passo: Verificar estrutura atual do Geralda

### 2026-02-24 20:38 - Revalidação crítica 1.2.C
- Corrigido bloqueio de testes por ausência de `aiosqlite` com fallback SQLite/PostgreSQL em `tests/conftest_db.py`
- Corrigido bug timezone-aware vs timezone-naive nos modelos SQLAlchemy
- Resultado validado: `test_care_plan_service.py` + `test_care_task_service.py` = **22/22 passando**
- Evidência: `1.2.C_TESTES_POSTGRESQL/20260224-2038_CORRECAO_BLOQUEIO_SQLITE_POSTGRES.md`
### 2026-02-24 21:45 - Validacao final de regressao
- Revalidacao ampla apos correcoes de persistencia/timezone.
- Resultado consolidado do modulo Geralda: **381 passed, 0 failed** (sem cobertura).
- Referencia: `..\..\NIVEL_3_ALTO_VALOR_CLINICO\FASE_3.2_GERALDA_MOTOR_IA_EVENTOS\20260224-2145_FECHAMENTO_ESTABILIZACAO_TESTES.md`
