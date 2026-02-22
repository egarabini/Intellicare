# Fase 1 — Plano de Implementacao

> **EFs:** W001 (Persistencia + Module Registry) | W002 (IPS-First Aprimorado) | W011 (MCP Client)
> **Data:** 2026-02-17
> **DEV:** DEV1
> **Base:** Wanda v1.0.0 (69 testes, 93% cobertura, 8 endpoints)

---

## 1. Visao Geral

A Fase 1 evolui a WANDA de um orquestrador stateless em-memoria para um orquestrador persistente com PostgreSQL, cache Redis de IPS e capacidade de consumir MCP Servers (MINERVA e PIERRE).

### Principios
1. **Compatibilidade v1.0** — Todos 69 testes existentes devem continuar passando
2. **Graceful degradation** — Sem DB/Redis, WANDA opera no modo v1.0 (in-memory)
3. **Incremental** — Cada EF pode ser ativada independentemente via config

---

## 2. Arquivos Novos

```
wanda/
├── database/
│   ├── __init__.py
│   ├── engine.py              # AsyncEngine factory (asyncpg)
│   ├── models.py              # SQLAlchemy ORM models (registered_modules, health_events, etc.)
│   └── repository.py          # ModuleRepository (CRUD PostgreSQL)
│
├── registry/
│   ├── __init__.py
│   ├── persistent_registry.py # ModuleRegistryV2 (extends v1.0 interface + PostgreSQL)
│   └── discovery_service.py   # DiscoveryService (probes + persists)
│
├── ips/
│   ├── __init__.py
│   ├── manager.py             # IPSManager (Redis cache + Florence fetch)
│   ├── enricher.py            # IPSEnricher (Oswaldo + Geralda)
│   ├── fallback.py            # IPSFallbackStrategy
│   └── models.py              # IPSBundle, EnrichedIPS, ValidationResult
│
├── mcp/
│   ├── __init__.py
│   ├── client.py              # WandaMCPClient (SSE sessions)
│   ├── config.py              # MCPClientConfig
│   ├── models.py              # MCPModuleRecord, MCPToolInfo, MCPCallRecord
│   ├── exceptions.py          # MCP-specific errors
│   └── tool_registry.py       # WandaToolRegistry (HTTP + MCP unificado)
│
├── api/
│   ├── registry_routes.py     # /api/v1/registry/* (EF-W001)
│   ├── ips_routes.py          # /api/v1/ips/* (EF-W002)
│   └── mcp_routes.py          # /api/v1/mcp/* (EF-W011)

tests/
├── test_database.py           # SQLAlchemy models + repository
├── test_persistent_registry.py # ModuleRegistryV2
├── test_discovery_service.py  # DiscoveryService
├── test_ips_manager.py        # IPSManager + cache
├── test_ips_enricher.py       # IPSEnricher
├── test_mcp_client.py         # WandaMCPClient
├── test_mcp_routes.py         # MCP API endpoints
├── test_registry_routes.py    # Registry API endpoints
└── test_ips_routes.py         # IPS API endpoints
```

## 3. Arquivos Modificados

| Arquivo | Mudanca |
|---------|---------|
| `wanda/config.py` | Adicionar config PostgreSQL, Redis, MCP |
| `wanda/api/app.py` | Incluir novos routers (registry, ips, mcp) |
| `wanda/orchestrator/orchestrator.py` | Integrar IPSManager e MCP Client |
| `tests/conftest.py` | Adicionar fixtures para DB, Redis, MCP |

---

## 4. Ordem de Implementacao

1. **Database layer** (engine, models, repository)
2. **PersistentRegistry + DiscoveryService** (EF-W001)
3. **Registry routes** (EF-W001 endpoints)
4. **IPS module** (manager, enricher, fallback, models) (EF-W002)
5. **IPS routes** (EF-W002 endpoints)
6. **MCP module** (client, config, models, exceptions) (EF-W011)
7. **MCP routes** (EF-W011 endpoints)
8. **Integration** (config, app, orchestrator updates)
9. **Tests** (all 9 test files)
10. **Validation** (run all tests, >=85% coverage)

---

## 5. Estimativa

| EF | Arquivos | Testes |
|----|----------|--------|
| W001 | 7 novos, 3 mod | ~25 |
| W002 | 5 novos, 2 mod | ~30 |
| W011 | 7 novos, 1 mod | ~15 |
| **Total** | **19 novos, 4 mod** | **~70 novos** |

Meta: 69 (existentes) + 70 (novos) = **~139 testes**, cobertura >= 85%.
