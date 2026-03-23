---
tipo: plano-execucao
demanda: DEM-081
titulo: GestorUI KPIs Clínicos
status: em-execucao
dev: DEV-2
criado: 2026-03-22
---

# DEM-081 — Plano de Execução

## Estimativa

Tempo estimado: ~4h | Complexidade: média

Backend é agregação SQL direta — sem lógica complexa. O esforço principal está no frontend (Recharts + filtros reativos + layout de cards).

---

## Ordem de execução

### Bloco 1 — Migration 020 (20min)
1. Criar `db/tenant_migrations/020_prescription_interaction_count.sql`
2. Aplicar: `psql -f 020_prescription_interaction_count.sql`
3. Verificar coluna `interaction_warnings_count` presente em `prescriptions`

### Bloco 2 — Backend KPIs (60min)
4. Criar `modules/admin/kpis.py` com `get_clinical_kpis()` (ver `02_TECNICA.md`)
5. Adicionar `ClinicalKPIsResponse` em `admin/schemas.py`
6. Adicionar endpoint `GET /admin/kpis/clinical` em `admin/routes.py` com role `GESTOR`
7. Testar via curl com token gestor — verificar JSON retornado

### Bloco 3 — Testes backend (30min)
8. Criar `test_clinical_kpis.py` com 3 testes
9. `pytest test_clinical_kpis.py -v`

### Bloco 4 — Frontend (90min)
10. Criar `useClinicalKPIs.ts` hook com react-query
11. Criar `IndicadoresPage.tsx`:
    - Filtros (período + médico) com estado controlado
    - 6 StatCards em `SimpleGrid cols={3}`
    - `BarChart` Top Médicos (Recharts)
    - `LineChart` Interações por dia (Recharts)
12. Adicionar rota `/indicadores` em `App.tsx`
13. Adicionar NavLink "Indicadores" no menu lateral (ícone `IconChartBar`)
14. Testar no browser: filtros atualizam todos os cards

---

## Gotcha — Recharts já está disponível

`recharts` está na lista de libs disponíveis no frontend React. Não precisa instalar — só importar:
```tsx
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
```

---

## Gotcha — `interaction_warnings_count` não retroativo

A coluna `interaction_warnings_count` começa zerada para prescrições existentes — só prescrições criadas após a migration terão valores. KPI de interações vai mostrar 0 para dados históricos. Isso é esperado e deve ser comunicado ao gestor na UI com uma nota: "Dados disponíveis a partir de [data da migration]".

---

## Gotcha — filtro por profissional não afeta KPIs de interação

O KPI "Interações Detectadas" não é por profissional (o checker é chamado por prescrição, não por médico). Quando o filtro de médico estiver ativo, este KPI deve exibir "N/A" ou ser desabilitado visualmente para evitar confusão.

---

## Entrega

```
feat(gestor): KPIs clínicos — dashboard encounters/prescrições/Florence/interações + Recharts
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
