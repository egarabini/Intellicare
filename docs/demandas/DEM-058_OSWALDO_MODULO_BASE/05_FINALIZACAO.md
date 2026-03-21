# DEM-058 — Oswaldo Módulo Base — Finalização

## Status: ✅ CONCLUÍDA

- **Commit final:** `19799a2` (`19799a21476570be30e3356a2e7bc2716c1f525e`)
- **Commit base:** `5a3a17a` (código estrutural + frontend)
- **Entregador:** DEV-1
- **Data:** 2026-04-04

---

## O que foi entregue

| Camada | Mudança |
|---|---|
| **Migration 014** | Tabela `prescriptions` com `items JSONB`, `cid10_code/desc`, `status DRAFT\|SIGNED` — PKs UUID para compatibilidade com FKs existentes |
| **Contracts** | `PrescriptionItem`, `CreatePrescriptionRequest`, `Prescription`, `CID10Result` |
| **Repository** | `create_prescription()`, `get_prescriptions_by_encounter()`, `search_cid10()` — padrão `tenant_session(ctx)` V3 |
| **Routes** | `GET /oswaldo/cid10/search`, `POST /oswaldo/prescriptions`, `GET /oswaldo/prescriptions/encounter/{id}` |
| **Frontend** | `OswaldoCID10Search` (autocomplete debounce), `OswaldoPrescriptionEditor`, aba "Prescrição" em `EncounterView` |

## Histórico de debug

| Problema | Causa | Fix |
|---|---|---|
| `404` nos testes | Prefixo duplicado no router — `ModuleLoader` monta em `/oswaldo`, router também definia prefix | Remover prefix do `routes.py` |
| `500 AttributeError: 'TenantContext' has no attribute 'db'` | Briefing usou padrão V2 (`ctx.db.fetch()`); V3 usa `tenant_session(ctx)` | Replicar padrão de `modules/careplanner/repository.py` |

---

## Gotcha registrada

Entrada adicionada em `docs/gotchas/careplanner.md`:
**"`TenantContext` não tem `.db` na V3 — usar `tenant_session(ctx)`"**

---

## Critérios de aceite — verificação final

- [x] Migration 014 aplicada sem erro
- [x] `GET /oswaldo/cid10/search?q=` retorna lista CID-10
- [x] `POST /oswaldo/prescriptions` cria prescrição com items JSONB
- [x] `GET /oswaldo/prescriptions/encounter/{id}` lista prescrições
- [x] `OswaldoCID10Search` com autocomplete no ClinicoUI
- [x] `OswaldoPrescriptionEditor` com lista de itens e salvar
- [x] Aba "Prescrição" visível em `EncounterView`
- [x] 3 testes passando
