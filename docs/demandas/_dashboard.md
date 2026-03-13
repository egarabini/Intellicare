---
tipo: dashboard
titulo: Dashboard de Demandas
atualizado: 2026-03-13
---

# Dashboard de Demandas — IntelliCare V3

> Abra no Obsidian com o plugin Dataview ativado para ver os dados dinâmicos.
> No GitHub, as queries aparecem como blocos de código (comportamento esperado).

---

## Em Execução

```dataview
TABLE fase, modulo, dev, criado AS "Criado"
FROM "demandas"
WHERE tipo = "especificacao-funcional" AND status = "em-execucao"
SORT fase ASC
```

---

## Aprovadas (aguardando execução)

```dataview
TABLE fase, sprint, modulo
FROM "demandas"
WHERE tipo = "especificacao-funcional" AND status = "aprovado"
SORT fase ASC
```

---

## Concluídas

```dataview
TABLE fase, modulo, concluido AS "Concluído"
FROM "demandas"
WHERE tipo = "finalizacao"
SORT concluido DESC
```

---

## Todas as DEMs

```dataview
TABLE fase, sprint, status, modulo
FROM "demandas"
WHERE tipo = "especificacao-funcional"
SORT fase ASC, sprint ASC
```

---

## Referência rápida — Mapeamento fases → DEMs

| DEM | Fase | Sprint | Módulo | Status |
|-----|------|--------|--------|--------|
| DEM-000 | 0 | 0.0 | — | ✅ Concluído |
| DEM-001 | 0 | 0.1 | docs | ✅ Concluído |
| DEM-002 | 1 | 1.0 | infra | ⏳ Pendente |
| DEM-003 | 1 | 1.1 | core | ⏳ Pendente |
| DEM-004 | 1 | 1.2 | keycloak | ⏳ Pendente |
| DEM-005 | 1 | 1.3 | admin | ⏳ Pendente |
| DEM-006 | 1 | 1.4 | admin | ⏳ Pendente |
| DEM-007 | 1 | 1.5 | admin | ⏳ Pendente |
| DEM-008 | 2 | 2.1 | gestor | ⏳ Pendente |
| DEM-009 | 2 | 2.2 | gestor | ⏳ Pendente |
| DEM-010 | 2 | 2.3 | gestor | ⏳ Pendente |
| DEM-011 | 3 | 3.1 | cuidado | ⏳ Pendente |
| DEM-012 | 3 | 3.2 | cuidado | ⏳ Pendente |
| DEM-013 | 3 | 3.3 | cuidado | ⏳ Pendente |
| DEM-014 | 3 | 3.4 | cuidado | ⏳ Pendente |
| DEM-015 | 3 | 3.5 | cuidado | ⏳ Pendente |
