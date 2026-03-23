---
tipo: plano-execucao
demanda: DEM-071
titulo: Linha do Tempo Clínica
status: em-execucao
dev: DEV-2
criado: 2026-03-21
---

# DEM-071 — Plano de Execução

## Estimativa

Tempo estimado: ~3.5h | Complexidade: média

O núcleo é a query `UNION ALL` no PostgreSQL. Uma vez que ela retorna dados corretos e paginados, o componente React é direto.

---

## Ordem de execução

### Bloco 1 — Backend (1.5h)
1. Criar `TimelineEvent` e `TimelineResponse` em `schemas.py`
2. Implementar `get_patient_timeline()` em `services.py`
   - Testar a query SQL isolada primeiro no psql
   - Garantir paginação via `OFFSET/LIMIT`
3. Adicionar endpoint `GET /cuidado/patients/{id}/timeline` em `routes.py`

### Bloco 2 — Testes (45min)
4. Criar `tests/test_timeline.py`:
   - `test_timeline_returns_all_types()`
   - `test_timeline_filter_by_type()`
   - `test_timeline_filter_by_days()`
   - `test_timeline_pagination()`
5. Rodar — sem regressões

### Bloco 3 — Frontend (1.5h)
6. Criar `ClinicalTimeline.tsx` com cards por tipo e ícones Mantine
7. Criar `useTimeline.ts` com React Query + filtros
8. Adicionar aba "Linha do Tempo" no `PatientProfile.tsx`
9. Rebuild ClinicoUI

---

## Gotcha — UNION ALL e tenant isolation

A query unifica 4 tabelas. Todas devem usar `tenant_session(ctx)` — não misturar schemas. Testar com 2 tenants distintos para confirmar isolamento.

---

## Entrega

```
feat(cuidado): linha do tempo clínica — timeline unificada encounters+notes+prescriptions+journeys
```
Hash → enviar para o ARQUITETO fechar DEM-071.
