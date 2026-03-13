---
tipo: roadmap
atualizado: 2026-03-13
---

# IntelliCare V3 — Roadmap

## Visão

1 serviço Python (`intellicare-service`), módulos carregados dinamicamente,
tríade RAG/SLM/pgvector. De 10+ containers caóticos para 1 container inteligente.

---

## Fase 0 — Fundação ✅

| DEM | Sprint | Entrega | Status |
|-----|--------|---------|--------|
| DEM-000 | 0.0 | Migração V2→V3: tag v2-final, branch v2-archive, skeleton V3 no main | ✅ |
| DEM-001 | 0.1 | Vault Obsidian, ADRs, templates, notas de módulos, design-docs | ✅ |

---

## Fase 1 — Admin (Semanas 1-3)

**Resultado ao final:** Tenant pode ser criado, configurado e faturado.

| DEM | Sprint | Entrega |
|-----|--------|---------|
| DEM-002 | 1.0 | Infra Docker: PostgreSQL+pgvector, Redis, Keycloak, OLLAMA, Traefik + `ingest_docs.py` |
| DEM-003 | 1.1 | `intellicare-core`: TenantContext, auth, db, vector helpers, module_loader |
| DEM-004 | 1.2 | Keycloak: realm, clients, roles (PLATFORM_ADMIN, TENANT_GESTOR, CLINICO, PACIENTE), mappers |
| DEM-005 | 1.3 | Admin backend: CRUD tenants+planos, provisionamento automático de schema |
| DEM-006 | 1.4 | Admin frontend: Jinja2+HTMX, dashboard de tenants e planos |
| DEM-007 | 1.5 | Finance básico: registro de uso mensal, billing status, controle de plano |

---

## Fase 2 — Gestor (Semanas 4-6)

**Resultado ao final:** Gestor do tenant organiza equipe e estrutura física.

| DEM | Sprint | Entrega |
|-----|--------|---------|
| DEM-008 | 2.1 | Gestor backend: CRUD unidades, setores, profissionais, alocações |
| DEM-009 | 2.2 | Gestor frontend: Jinja2+HTMX, dashboard do tenant |
| DEM-010 | 2.3 | Integração admin↔gestor E2E: flow completo de onboarding testado |

---

## Fase 3 — Cuidado + RAG (Semanas 7-12)

**Resultado ao final:** Profissional consulta protocolo clínico em <300ms.

| DEM | Sprint | Entrega |
|-----|--------|---------|
| DEM-011 | 3.1 | pgvector ativo: tabela `protocols`, índice HNSW, script de ingestão |
| DEM-012 | 3.2 | SLM OLLAMA: modelo configurado, endpoint de embedding e geração |
| DEM-013 | 3.3 | Cuidado backend: busca semântica + síntese SLM, latência <300ms |
| DEM-014 | 3.4 | Programas de saúde: DRC, Diabetes, HAS, Câncer indexados no pgvector |
| DEM-015 | 3.5 | Frontend clínico MVP: React ou HTMX, consulta de protocolo end-to-end |

---

## O que NÃO fazer agora

- Não criar 10 containers separados por módulo (ver [[decisoes/ADR-002-modulo-vs-servico]])
- Não usar LangGraph/Flowise/LangChain nas Fases 1-2 — orquestração prematura
- Não construir WANDA até ter 2+ módulos clínicos funcionais — ela é a cola, não o produto
- Não criar schema global — cada tenant é autônomo (ver [[decisoes/ADR-001-schema-autonomo]])
- Não criar frontend React separado para admin/gestor — FastAPI+HTMX é suficiente e mais rápido
