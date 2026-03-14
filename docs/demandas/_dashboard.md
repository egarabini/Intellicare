---
tipo: dashboard
titulo: Dashboard de Demandas
atualizado: 2026-03-13
---

# Dashboard de Demandas — IntelliCare V3

## Status de Implementação

| DEM | Nome | Módulo | Status | Commit 03 |
|-----|------|--------|--------|-----------|
| DEM-001 | Vault Obsidian | docs | ✅ implementado | `2e77d2c` |
| DEM-002 | Infra Docker | infra | ✅ implementado | `984f565` |
| DEM-003 | IntelliCare Core | intellicare-core | ✅ implementado | `1df59c6` |
| DEM-004 | Keycloak Config | infra/keycloak | ✅ implementado | `3266b58` |
| DEM-005 | Admin Backend | admin | ✅ implementado | `73c85d0` |
| DEM-006 | Admin Frontend | admin (React) | ✅ implementado | `095fd51` |
| DEM-007 | Financeiro | financeiro | ✅ implementado | `e61846d` |
| DEM-008 | E2E Integration | tests | ✅ implementado | `1392358` |
| DEM-009 | PGVector RAG | vector | ✅ implementado | `5d9f39b` |
| DEM-010 | SLM Ollama | slm | ✅ implementado | `4b026fb` |
| DEM-011 | Gestor Backend | gestor | ✅ implementado | `16b2b93` |
| DEM-012 | Gestor Frontend | gestor (React) | ✅ implementado | `4448449` |
| DEM-013 | Cuidado Backend | cuidado | ✅ implementado | `13b1e26` |
| DEM-014 | Programas Saúde | programas | ✅ implementado | `6c4d2f2` |
| DEM-015 | Frontend Clínico | cuidado (React) | ✅ implementado | `96ac614` |

---

## Dataview (Obsidian)

> As queries abaixo funcionam apenas no Obsidian com plugin Dataview ativo.

### Em Execução

```dataview
TABLE fase, modulo, dev, criado AS "Criado"
FROM "demandas"
WHERE tipo = "especificacao-funcional" AND status = "em-execucao"
SORT fase ASC
```

### Concluídas

```dataview
TABLE fase, modulo, concluido AS "Concluído"
FROM "demandas"
WHERE tipo = "finalizacao"
SORT concluido DESC
```
