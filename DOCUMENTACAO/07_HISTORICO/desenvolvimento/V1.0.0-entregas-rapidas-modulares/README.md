# V1.0.0 — Entregas Rápidas Modulares

**Data:** 2026-02-20  
**Abordagem:** Entregas que podem ser processadas e finalizadas rapidamente por um dev, sem interferir em outros módulos

---

## O que estamos desenvolvendo

Enquanto as fases principais (Estabilização, Git, Deploy, Monitoramento, Produção) são processadas, esta abordagem identifica **entregas rápidas** que:

1. **São modulares** — trabalho em um módulo não bloqueia outros
2. **Têm baixo acoplamento** — alterações isoladas, sem dependências cruzadas
3. **Podem ser finalizadas em tempo curto** — horas ou poucos dias por item
4. **Não exigem coordenação complexa** — um dev pode executar de ponta a ponta

### Entregas rápidas identificadas

| # | Entregável | Módulo(s) | Tempo est. | Interferência |
|---|------------|-----------|------------|---------------|
| 1 | **Exportar OpenAPI por módulo** | Cada módulo isolado | 1–2h/módulo | Nenhuma |
| 2 | **Padronizar /health e /info** | Cada módulo isolado | 30min/módulo | Nenhuma |
| 3 | **README por módulo** | Cada módulo isolado | 1h/módulo | Nenhuma |
| 4 | **.env.example por módulo** | Cada módulo isolado | 30min/módulo | Nenhuma |
| 5 | **Lint/format (Ruff) por módulo** | Cada módulo isolado | 30min/módulo | Nenhuma |
| 6 | **Endpoint /metrics (Prometheus)** | Cada módulo isolado | 1h/módulo | Nenhuma |

**Prioridade sugerida para início rápido:** Itens 1 e 2 (OpenAPI + health/info) — já têm plano em `docs/PLANO_UNIFICACAO_OPENAPI.md`.

---

## O que esperamos alcançar

1. **Acúmulo de valor em paralelo** — enquanto dev1/dev2 trabalham nas fases principais, outro dev pode avançar em itens modulares
2. **Redução de débito técnico** — documentação, padronização e qualidade incrementais
3. **Base para Fase 3 (Deploy)** — OpenAPI exportado e .env.example facilitam orquestração
4. **Base para Fase 4 (Monitoramento)** — /metrics em cada módulo habilita Prometheus
5. **Governança sem bloqueio** — cada módulo evolui de forma independente quando possível

---

## Estrutura desta pasta

```
V1.0.0-entregas-rapidas-modulares/
├── README.md                    ← Este arquivo (o que desenvolvemos, o que esperamos)
├── Fase1/                       ← Especificações da Fase 1 (Estabilização)
├── Fase2/                       ← Especificações da Fase 2 (Git)
├── Fase3/                       ← Especificações da Fase 3 (Deploy)
├── Fase4/                       ← Especificações da Fase 4 (Monitoramento)
└── Fase5/                       ← Especificações da Fase 5 (Produção)
```

As pastas de cada fase contêm referência às especificações funcionais (em `docs/PLANNER-CURSOR/especificacoes/FaseN/`) e sugestões de entregas rápidas que complementam cada fase.

---

## Relação com as fases principais

| Fase principal | Entregas rápidas que a antecipam ou complementam |
|----------------|--------------------------------------------------|
| Fase 1 | Padronizar /health, ambientes virtuais por módulo |
| Fase 2 | — (Git é centralizado) |
| Fase 3 | .env.example, OpenAPI exportado (facilita orquestração) |
| Fase 4 | /metrics em cada módulo (Prometheus) |
| Fase 5 | Lint, testes unitários por módulo |

---

## Critério para incluir nova entrega rápida

- Pode ser feita em **um único módulo** (ou em módulos sem dependência entre si)
- **Tempo estimado:** até 1 dia de trabalho
- **Sem impacto** em outros módulos ou no portal
- **Reversível** ou de baixo risco
