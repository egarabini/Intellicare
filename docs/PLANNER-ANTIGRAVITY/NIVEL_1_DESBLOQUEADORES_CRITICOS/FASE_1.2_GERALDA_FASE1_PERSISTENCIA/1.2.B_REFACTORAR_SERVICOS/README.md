# FASE 1.2.B - Refatorar Serviços para Usar PostgreSQL

**Data de início:** 2026-02-24 10:50
**Responsável:** DEV0
**Prioridade:** 🔴 BLOQUEADOR
**Status:** 🔄 EM ANDAMENTO

## Contexto

Agora que os modelos SQLAlchemy foram criados (FASE 1.2.A), precisamos refatorar os services que atualmente usam dicionários in-memory para usar o banco de dados PostgreSQL.

## Objetivo

Criar services que usam `AsyncSession` do SQLAlchemy para:
- Criar, ler, atualizar e deletar CarePlans
- Criar, ler, atualizar e deletar CareTasks
- Criar, ler, atualizar e deletar Reminders

## Tarefas

### Services a Criar

- [ ] ⚙️ Criar `geralda/services/care_plan_service.py`
  - `create_plan()`
  - `get_plan()`
  - `list_plans_by_patient()`
  - `update_plan()`
  - `deactivate_plan()`

- [ ] ⚙️ Criar `geralda/services/care_task_service.py`
  - `create_task()`
  - `get_task()`
  - `list_tasks_by_plan()`
  - `complete_task()`
  - `skip_task()`
  - `list_overdue_tasks()`

- [ ] ⚙️ Criar `geralda/services/reminder_service.py`
  - `schedule_reminder()`
  - `list_pending_reminders()`
  - `mark_sent()`
  - `cancel_reminder()`

- [ ] ⚙️ Criar `geralda/database/deps.py` - `get_db()` dependency
- [ ] ⚙️ Atualizar rotas em `geralda/api/routes/` para injetar `db: AsyncSession`

## Log de Progresso

### 2026-02-24 10:50 - Início da FASE 1.2.B
- Criada estrutura de pastas para documentação
- Próximo passo: Verificar services atuais do Geralda
