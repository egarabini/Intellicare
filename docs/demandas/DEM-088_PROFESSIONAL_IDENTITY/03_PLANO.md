# DEM-088 — Plano de Execução

## Responsável: DEV-2

## Passos

1. **Ler DEM-084 como referência** — `docs/demandas/DEM-084_PATIENT_IDENTITY/` completo
2. **Criar migration 024** — `db/tenant_migrations/024_professionals_pessoa_id.sql`
3. **Localizar `professionals/repository.py`** — adicionar parâmetro `pessoa_id` em `create_professional()`
4. **Atualizar `professionals/services.py`** — chamar `find_or_create_by_cpf()` quando CPF presente
5. **Atualizar `professionals/router.py`** — injetar `platform_db` como segundo Depends (bare async generator)
6. **Atualizar `professionals/router.py`** — endpoint PUT para reconciliar `pessoa_id` em updates com CPF
7. **Escrever 5 testes** em `tests/test_professional_identity.py`
8. **Rodar suite completa** — confirmar sem regressões
9. **Commitar e push para origin/main**

## Gotchas a evitar (aprendizados DEM-084)

| Gotcha | Como evitar |
|--------|------------|
| `@asynccontextmanager` em `get_platform_db` | Usar bare async generator — já corrigido em `session.py:94` |
| `ctx.tenant_slug` | Sempre `ctx.tenant_id` |
| Normalização CPF | `re.sub(r'\D', '', cpf)` antes de qualquer operação |
| Dois AsyncSession no mesmo handler | Permitido — transactions separadas, sem 2PC |

## Commit esperado

```
feat(clinico): professional identity integration (DEM-088)

- migration 024: professionals.pessoa_id UUID nullable
- find_or_create_by_cpf() integrado no create/update professional
- 5 testes: criação com CPF, sem CPF, multi-tenant, update, FK lógica
- Padrão ADR-004: FK lógica, sem NOT NULL, tenant isolado
```
