---
dem: DEM-008
titulo: Teste E2E de Integração — Implementação
tipo: IMPLEMENTACAO
status: concluído
criado: 2026-03-14
---

# DEM-008 · 03 — Implementação

## Arquivos Criados

| Arquivo | Papel |
|---------|-------|
| `tests/e2e/__init__.py` | Pacote de testes |
| `tests/e2e/conftest.py` | Fixtures de sessão: API client, tokens, tenant lifecycle |
| `tests/e2e/test_health.py` | AC-1: health checks (API, Admin, Keycloak) |
| `tests/e2e/test_auth.py` | AC-3/4/5: JWT claims, autorização, 401/403 |
| `tests/e2e/test_tenant_flow.py` | AC-2/10: schema criado, tenant suspenso |
| `tests/e2e/test_isolation.py` | AC-6: isolamento multi-tenant |
| `tests/e2e/test_rag.py` | AC-7: ingest + busca semântica pgvector |
| `tools/scripts/run_e2e.sh` | AC-9: script CI executável |
| `pytest.ini` | Marcadores `e2e` e `unit`, asyncio_mode=auto |

## Testes (11 coletados)

| Arquivo | Teste | AC |
|---------|-------|----|
| `test_health.py` | `test_api_health` | AC-1 |
| `test_health.py` | `test_admin_module_health` | AC-1 |
| `test_health.py` | `test_keycloak_health` | AC-1 |
| `test_auth.py` | `test_token_contem_tenant_id` | AC-3 |
| `test_auth.py` | `test_gestor_acessa_gestor_endpoint` | AC-4 |
| `test_auth.py` | `test_gestor_negado_em_admin` | AC-5 |
| `test_auth.py` | `test_sem_token_retorna_401` | AC-5 |
| `test_tenant_flow.py` | `test_schema_criado_no_postgres` | AC-2 |
| `test_tenant_flow.py` | `test_tenant_suspenso_bloqueia_acesso` | AC-10 |
| `test_isolation.py` | `test_dados_isolados_entre_tenants` | AC-6 |
| `test_rag.py` | `test_ingest_e_busca_semantica` | AC-7 |

## Execução

```bash
# Testes E2E (requer ambiente rodando)
pytest tests/e2e/ -m e2e -v

# Via script CI
./tools/scripts/run_e2e.sh

# Apenas testes unitários (sem ambiente)
pytest tests/ -m "not e2e" -v
```

## Pré-requisitos

- `docker compose up -d` (infra rodando)
- Keycloak configurado (`setup_keycloak.py`)
- OLLAMA com `nomic-embed-text` (para test_rag)
- Dependências: `httpx`, `asyncpg`, `python-jose`, `pytest-asyncio`

## Dependências

- `intellicare-core` (DEM-003): auth, contracts
- `modules/admin` (DEM-005): tenant CRUD
- `modules/gestor` (DEM-011): endpoint de teste
- Keycloak (DEM-004): tokens e autorização
- pgvector (DEM-009): busca semântica

