# IntelliCare V3 — Dashboard de Demandas

> Atualizado em: 2026-03-13
> Arquiteto: Eduardo (ARQUITETO) | Planejador: Claude (PLANEJADOR)

---

## Status Geral

| Fase | DEMs | 01_FUNCIONAL | 02_TECNICA | 03-05 Dev |
|------|------|:---:|:---:|:---:|
| Fase 0 — Fundação | 001-003 | ✅ | ✅ | ⏳ |
| Fase 1 — Core | 004-009 | ✅ | ✅ | ⏳ |
| Fase 2 — Inteligência | 010-011 | ✅ | ✅ | ⏳ |
| Fase 3 — Frontends | 012-015 | ✅ | ✅ | ⏳ |

---

## Detalhamento por DEM

| DEM | Nome | 01_FUNCIONAL | 02_TECNICA | Commit | Observações |
|-----|------|:---:|:---:|--------|-------------|
| DEM-001 | Estrutura Base do Repositório | ✅ | ✅ | — | ADR-001/002 definidos |
| DEM-002 | Infraestrutura Docker + PostgreSQL | ✅ | ✅ | — | pgvector, OLLAMA |
| DEM-003 | Core FastAPI + TenantContext | ✅ | ✅ | — | BaseModule ABC |
| DEM-004 | Keycloak Config | ✅ | ✅ | `48ae2c9` | realm-export.json, setup_keycloak.py |
| DEM-005 | Admin Backend | ✅ | ✅ | `c2055bc` | TenantService, CRUD /admin/ |
| DEM-006 | Admin Frontend (Blazor) | ✅ | ✅ | `381a85c` | MudBlazor, OIDC |
| DEM-007 | Módulo Financeiro | ✅ | ✅ | `c8746c7` | APScheduler, fatura overdue |
| DEM-008 | Testes E2E | ✅ | ✅ | `1392358` | pytest + httpx, conftest |
| DEM-009 | RAG Ingest Pipeline | ✅ | ✅ | `5ff6139` | pdfplumber, pgvector, watcher |
| DEM-010 | SLM + OLLAMA | ✅ | ✅ | `6ec3592` | streaming SSE, RAG+SLM |
| DEM-011 | Gestor Backend | ✅ | ✅ | `6ec3592` | profile, docs, usage_report |
| DEM-012 | Gestor Frontend (Blazor) | ✅ | ✅ | `6ec3592` | MudBlazor, upload |
| DEM-013 | Cuidado Backend | ✅ | ✅ | `6ec3592` | pacientes, encontros, notas SOAP |
| DEM-014 | Programas de Saúde | ✅ | ✅ | `6ec3592` | matrículas, overdue, coverage |
| DEM-015 | Frontend Clínico (React) | ✅ | ✅ | `6ec3592` | SSE streaming, Mantine UI |

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Concluído / Aprovado |
| 🔄 | Em andamento |
| ⏳ | Aguardando início |
| ❌ | Bloqueado |

---

## Próximos Passos (Fase Dev)

Os documentos 01_FUNCIONAL e 02_TECNICA de todas as 15 DEMs estão aprovados e commitados.
A Fase Dev (03_IMPLEMENTACAO → 04_TESTES → 05_REVISAO) pode iniciar a partir de DEM-001.

**Ordem sugerida de implementação**:
1. DEM-001 → DEM-003 (estrutura + core)
2. DEM-004 → DEM-005 (auth + admin)
3. DEM-007 + DEM-009 (financeiro + RAG)
4. DEM-010 → DEM-011 (SLM + gestor)
5. DEM-013 → DEM-014 (cuidado + programas)
6. DEM-006 + DEM-012 + DEM-015 (frontends)
7. DEM-008 (E2E cobrindo tudo)
