---
tipo: dashboard
titulo: Dashboard de Demandas
atualizado: 2026-03-13
---

# Dashboard de Demandas — IntelliCare V3

> Gerado automaticamente pelo Dataview. Abra no Obsidian para ver os dados.

---

## Em Execução

```dataview
TABLE fase, modulo, dev, criado AS "Criado"
FROM "demandas"
WHERE tipo = "especificacao-funcional" AND status = "em-execucao"
SORT fase ASC
```

## Aprovadas (aguardando execução)

```dataview
TABLE fase, modulo, sprint
FROM "demandas"
WHERE tipo = "especificacao-funcional" AND status = "aprovado"
SORT fase ASC
```

## Concluídas

```dataview
TABLE fase, modulo, concluido AS "Concluído"
FROM "demandas"
WHERE tipo = "finalizacao"
SORT concluido DESC
```

## Todas as DEMs (visão geral)

```dataview
TABLE fase, sprint, status, modulo
FROM "demandas"
WHERE tipo = "especificacao-funcional"
SORT fase ASC, sprint ASC
```
