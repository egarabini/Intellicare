---
tipo: especificacao-funcional
demanda: DEM-081
titulo: GestorUI KPIs Clínicos
sprint: 2026-05-09
status: em-execucao
dev: DEV-2
criado: 2026-03-22
depende_de: [DEM-055, DEM-058, DEM-077, DEM-039]
tags: [gestor, kpi, dashboard, metricas, clinico]
---

# DEM-081 — GestorUI KPIs Clínicos

## Objetivo

Adicionar uma página de KPIs clínicos ao GestorUI, dando ao gestor visibilidade sobre a atividade clínica da unidade: volume de consultas, prescrições, notas Florence, alertas de interação detectados e jornadas CarePlanner encerradas — com filtros por período e por profissional.

---

## Personas

**Gestor:** acessa GestorUI → "Indicadores Clínicos" e visualiza painéis consolidados da unidade. Pode filtrar por médico específico e por período (últimos 7, 30, 90 dias).

**Diretor Clínico:** usa os KPIs para avaliar produtividade por médico, taxa de uso da IA e taxa de interações medicamentosas detectadas.

---

## KPIs a exibir

| KPI | Descrição | Granularidade |
|-----|-----------|--------------|
| Consultas realizadas | Total de encounters com status `closed` | Por período, por médico |
| Notas Florence geradas | Total de `clinical_notes` | Por período, por médico |
| Prescrições emitidas | Total de `prescriptions` | Por período, por médico |
| Interações detectadas | Chamadas ao `/check-interactions` com ≥1 warning | Por período |
| Sugestões IA aceitas | Encounters com nota Florence gerada via IA | Por período |
| Jornadas CarePlanner | Total de journeys por status (OPEN/CLOSED/EXPIRED) | Por período |

---

## Layout da página

```
┌─ Indicadores Clínicos ─────────────────────────────────────────────┐
│  Período: [Últimos 7 dias ▼]   Médico: [Todos ▼]   [Aplicar]      │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Consultas    │  │ Prescrições  │  │ Notas Florence│             │
│  │     142      │  │     89       │  │     76        │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Interações   │  │ Sugestões IA │  │ Jornadas     │             │
│  │ Detectadas   │  │ Aceitas      │  │ CarePlanner  │             │
│  │     12       │  │     54       │  │  31 / 8 / 4  │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  Top Médicos (prescrições)          Interações por dia             │
│  ┌─────────────────────────┐        ┌──────────────────────────┐  │
│  │ Recharts BarChart       │        │ Recharts LineChart       │  │
│  └─────────────────────────┘        └──────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Critérios de aceite

1. Página `/gestor/indicadores` carrega com dados do período padrão (últimos 30 dias)
2. Filtro por período atualiza todos os KPIs simultaneamente
3. Filtro por médico filtra todos os KPIs individuais (não os agregados de interação)
4. Gráfico "Top Médicos" exibe ranking de prescrições no período
5. Gráfico "Interações por dia" exibe série temporal de alertas detectados
6. `GET /admin/kpis/clinical` retorna todos os KPIs em uma única chamada
7. 3+ testes automatizados

---

## Fora de escopo

- Export CSV/PDF dos KPIs (fase futura)
- Alertas automáticos ao gestor (ex: taxa de interação alta)
- Comparativo entre períodos
