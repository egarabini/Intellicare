---
tipo: plano-execucao
demanda: DEM-083
titulo: ADR-004 + Identity Foundation
status: planejada
dev: CODEX
sprint: 2026-05-16
criado: 2026-03-23
---

# DEM-083 — Plano de Execução

## Estimativa

Tempo estimado: ~4h | Complexidade: média-alta

Complexidade está na definição correta das tabelas e na sessão de banco (platform vs tenant). A implementação em si é direta. O ADR precisa de cuidado — vai ser referenciado por muitos sprints futuros.

---

## Ordem de execução

### Bloco 1 — ADR-004 (30min)
1. Criar `docs/adr/ADR-004-identity-centralization.md`
2. Revisar ADR-001 e ADR-002 para manter consistência de formato
3. Incluir diagrama ASCII do modelo: `Keycloak → platform.pessoa → {schema}.paciente`

### Bloco 2 — Migration 021 (30min)
4. Criar `db/platform_migrations/021_pessoa_identity.sql` conforme `02_TECNICA.md §2`
5. Testar aplicação em banco limpo: `psql -f 021_pessoa_identity.sql`
6. Testar idempotência: rodar segunda vez — nenhum erro esperado (`IF NOT EXISTS`)

### Bloco 3 — Módulo identity (90min)
7. Criar `modules/identity/__init__.py`, `models.py`, `schemas.py`
8. Criar `repository.py` — `get_pessoa_by_cpf()`, `get_pessoa_by_id()`, `create_pessoa_fisica()`
9. Criar `services.py` — `find_or_create_by_cpf()` com normalização de CPF
10. Criar `router.py` — 3 endpoints (ver `02_TECNICA.md §3`)
11. Registrar router em `main.py`

### Bloco 4 — Testes (45min)
12. Criar `tests/test_identity_foundation.py` com 6 cenários obrigatórios
13. `pytest tests/test_identity_foundation.py -v` → 6/6 passed
14. `pytest -x` (suite completa) → zero regressões

---

## Gotcha — `get_platform_db` já existe?

Verificar se a dependência `get_platform_db` já está implementada no projeto. Se não:
```python
# packages/intellicare_core/database.py — adicionar:
async def get_platform_db() -> AsyncGenerator[AsyncSession, None]:
    async with platform_session_factory() as session:
        yield session
```
Onde `platform_session_factory` usa a mesma `DATABASE_URL` mas com `search_path=platform`.

Se já existir (usado em `prompt_templates`), apenas importar.

---

## Gotcha — Alinhamento com migration 017

A migration 017 (`prompt_templates`) já usa o schema `platform`. Confirmar que o banco de staging tem o schema `platform` criado antes de aplicar a 021. Verificar:
```sql
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'platform';
```

---

## Entrega

```
feat(identity): ADR-004 + platform.pessoa foundation — migration 021, identity service, find-or-create CPF
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
