# DEM-089 — Finalização

## Commit

`3a9f386` — feat(identity): reconciliation endpoint + admin view (DEM-089)

## Entregues

### Backend — módulo identity

| Arquivo | Mudança |
|---------|---------|
| `modules/identity/router.py` | `POST /identity/admin/reconcile`, `GET /identity/admin/stats` |
| `modules/identity/services.py` | `reconcile_tenant_patients()`, `reconcile_tenant_professionals()`, `get_identity_stats()` |
| `modules/identity/repository.py` | queries batch por tenant, stats cross-tenant |
| `modules/identity/schemas.py` | `ReconcileResult`, `IdentityStats`, `TenantCoverage` |

### Frontend — AdminUI

| Arquivo | Mudança |
|---------|---------|
| `frontend/AdminUI/src/pages/IdentityPage.tsx` | Cards totais + tabela por tenant + botão reconciliar com confirmação modal |
| `frontend/AdminUI/src/hooks/useIdentity.ts` | Hook com `getStats()` e `runReconcile()` |
| `frontend/AdminUI/src/App.tsx` | Rota `/admin-ui/identity` + NavLink "Identidade" |
| `packages/intellicare-core/static/admin-ui/` | Bundle regenerado: `index.html` + `index-CEE6pvO7.js` |

## Testes

```
pytest packages/intellicare-core/tests/test_identity_foundation.py \
       packages/intellicare-core/tests/test_identity_reconciliation.py -q
14 passed
```

- 8 de `test_identity_foundation.py` (regressão DEM-083)
- 6 novos de `test_identity_reconciliation.py`:
  - reconciliação de pacientes legados
  - reconciliação de profissionais legados
  - idempotência (segunda execução → linked=0)
  - skip de CPF nulo/inválido
  - isolamento de erro por linha
  - stats retorna cobertura percentual
  - autorização PLATFORM_ADMIN

## Adaptações ao código real

| Item | Spec | Real |
|------|------|------|
| Acesso a professionals | assumia coluna `cpf` sempre presente | detecção defensiva: testa `cpf` e `document_cpf`; pula scope se nenhuma coluna existir |
| Stats por tenant | `asyncio.gather()` paralelo | serial por corretude — otimização fica para sprint futura |
| Escopo reconciliação | por tenant individual | mantido — simplifica RBAC e é suficiente para volume atual |

## Gotcha registrado em 04_DIARIO.md

> **Detecção defensiva de CPF em professionals:** a reconciliação inspeciona o schema do tenant antes de rodar o batch — se a tabela `professionals` não tiver coluna `cpf` nem `document_cpf`, o scope `professionals` é pulado sem erro. Esse padrão deve ser usado em qualquer futura DEM que toque colunas opcionais de módulos clínicos.
