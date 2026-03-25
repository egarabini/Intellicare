# DEM-089 — Plano de Execução

## Responsável: CODEX

## Passos

1. **Ler ADR-004** — `docs/adr/ADR-004-identity-centralization.md` para contexto
2. **Ler DEM-083/DEM-084** — entender o padrão `find_or_create_by_cpf()` e `get_platform_db`
3. **Adicionar endpoints ao `modules/identity/router.py`**:
   - `POST /identity/admin/reconcile`
   - `GET /identity/admin/stats`
4. **Implementar `reconcile_tenant_patients()`** em `modules/identity/services.py`
5. **Implementar `get_identity_stats()`** em `modules/identity/services.py`
6. **Criar `IdentityPage.tsx`** no AdminUI com stats + botão reconciliar
7. **Adicionar NavLink** "Identidade" no AdminUI nav
8. **Escrever 6 testes**
9. **Rodar suite** — confirmar sem regressões
10. **Commitar e push**

## Restrições arquiteturais

- SQL direto em `repository.py` — sem ORM novo (padrão do projeto)
- `platform.` qualificado explicitamente em todas as queries ao platform schema
- `get_platform_db` como bare async generator (não `@asynccontextmanager`)
- `ctx.tenant_id` (nunca `ctx.tenant_slug`)
- Endpoint protegido com `require_role("PLATFORM_ADMIN")` — não TENANT_GESTOR

## Adaptações pré-aprovadas pelo ARQUITETO

- O endpoint de reconcile pode operar em um tenant por vez (scope=patients) sem precisar iterar todos os tenants em uma única chamada — simplifica autorização e não exige acesso cross-tenant no mesmo request
- Stats podem mostrar apenas platform.pessoa_fisica total + vínculos em `pessoa_estabelecimento` (sem query por tenant individual se complexo)

## Commit esperado

```
feat(identity): reconciliation endpoint + admin view (DEM-089)

- POST /identity/admin/reconcile: backfill pessoa_id em pacientes existentes com CPF
- GET /identity/admin/stats: cobertura de identidade por tenant
- IdentityPage.tsx no AdminUI com stats e botão reconciliar
- 6 testes: reconcile, idempotência, skip CPF nulo, isolamento erro, stats, RBAC
```
