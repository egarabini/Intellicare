# 2026-02-24 20:38 - Correcao do Bloqueio 1.2.C (SQLite/SQLAlchemy)

## Contexto

Os testes de servico da FASE 1.2.C estavam bloqueados por:

1. `ModuleNotFoundError: No module named "aiosqlite"`
2. Erro de timezone no fallback PostgreSQL (`can't subtract offset-naive and offset-aware datetimes`)

## Acoes executadas

1. Atualizado `pyproject.toml` para declarar `aiosqlite` em `tool.poetry.group.dev.dependencies`.
2. Implementado fallback no fixture `tests/conftest_db.py`:
   - Usa `sqlite+aiosqlite` quando o pacote existe.
   - Usa PostgreSQL com schema temporario isolado quando `aiosqlite` nao esta disponivel.
3. Corrigidos modelos para timezone-aware:
   - `geralda/models/care_plan.py`
   - `geralda/models/care_task.py`
   - `geralda/models/reminder.py`
   - `geralda/models/educational_material.py`

## Validacao

Comando:

```bash
pytest tests/test_care_plan_service.py tests/test_care_task_service.py -q --no-cov -p no:cacheprovider
```

Resultado:

- **22/22 testes passando**
- Bloqueio Pydantic/SQLAlchemy removido para o escopo da FASE 1.2.C

## Estado atual da FASE 1.2

- Persistencia via app DB ativa no container (`Dockerfile` -> `geralda.api.app_db:app`).
- Testes de servico do nucleo de persistencia validados localmente.
- Revalidacao completa com cobertura ainda depende de ajuste de permissao do arquivo `.coverage` no ambiente.
