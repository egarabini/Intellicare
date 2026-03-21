---
tipo: plano-execucao
demanda: DEM-065
titulo: Multi-tenant Avançado
status: em-execucao
dev: DEV-1
criado: 2026-03-21
---

# DEM-065 — Plano de Execução

## Estimativa

Tempo estimado: ~4h | Complexidade: alta

O núcleo crítico é o `tenant_provisioner.py` (Alembic programático + Keycloak API). O restante (middleware, endpoints, frontend) segue padrões já estabelecidos no projeto.

---

## Ordem de execução

### Bloco 1 — Fundação (1h)
1. Criar `migrations/015_tenant_config.sql` e aplicar
2. Criar `packages/intellicare-core/intellicare_core/tenant_provisioner.py`
   - Testar `CREATE SCHEMA` isolado primeiro
   - Depois Alembic upgrade programático
   - Por último integração Keycloak (pode mockar em teste)

### Bloco 2 — Backend (1.5h)
3. Criar `middleware/tenant_guard.py` e registrar no `main.py`
4. Atualizar `modules/admin/schemas.py` com novos tipos
5. Atualizar `modules/admin/services.py` — suspend/reactivate/provision
6. Atualizar `modules/admin/routes.py` — 7 novos endpoints

### Bloco 3 — Testes (45min)
7. Criar `tests/test_multitenant.py`:
   - `test_provision_tenant_creates_schema()`
   - `test_provision_tenant_runs_migrations()`
   - `test_suspend_tenant_blocks_requests()`
   - `test_reactivate_tenant_restores_access()`
   - `test_cross_tenant_isolation()`
8. Rodar todos os testes — garantir 0 regressões

### Bloco 4 — Frontend (45min)
9. Criar `frontend/AdminUI/src/pages/TenantsManager.tsx`
10. Adicionar rota no AdminUI router
11. Rebuild AdminUI no container

---

## Gotcha crítico — Alembic programático

Rodar migrations num schema específico requer setar `search_path` antes:

```python
async with engine.begin() as conn:
    await conn.execute(text(f"SET search_path TO {slug}, public"))
    await conn.run_sync(lambda c: alembic_upgrade(c, "head"))
```

Testar isso isoladamente antes de integrar no provisioner.

---

## Gotcha — Keycloak Admin API

Se `KEYCLOAK_ADMIN_URL` não estiver no `.env` do dev local, a criação de realm falhará silenciosamente. Validar no startup ou logar `WARNING` claro se ausente.

---

## Entrega

Commit com mensagem:
```
feat(multitenant): tenant_provisioner, migration 015, suspend/reactivate, TenantsManager
```
Hash → enviar para o ARQUITETO fechar DEM-065.
