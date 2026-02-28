# FASE 1.2.C - Testes PostgreSQL para Geralda

**Data de início:** 2026-02-24 11:05
**Responsável:** DEV0
**Prioridade:** 🔴 BLOQUEADOR
**Status:** 🔄 EM ANDAMENTO

## Contexto

Agora que os modelos SQLAlchemy (1.2.A) e os services (1.2.B) foram criados, precisamos criar testes para validar que tudo funciona corretamente.

## Objetivo

Criar testes usando SQLite in-memory (para CI/CD) com mínimo de 80% cobertura e 0 falhas.

## Tarefas

### Testes a Criar

- [ ] ⚙️ Criar `tests/conftest.py` com fixture de sessão SQLite in-memory
- [ ] 🧪 Criar `tests/test_care_plan_service.py` - mínimo 10 testes
- [ ] 🧪 Criar `tests/test_care_task_service.py` - mínimo 10 testes
- [ ] 🧪 Atualizar `tests/test_routes.py` - usar fixture de DB real
- [ ] 🧪 Meta: `pytest -q` → **≥ 80% cobertura, 0 falhas**

## Critérios de Aceite EF-001

- [x] Dados persistem após restart (services implementados)
- [x] Queries por `patient_id` usam índice (índices criados)
- [ ] Testes passando com SQLite in-memory no CI
- [ ] Cobertura ≥ 80%

## Log de Progresso

### 2026-02-24 11:05 - Início da FASE 1.2.C
- Criada estrutura de pastas para documentação
- Próximo passo: Verificar testes atuais do Geralda
