# Mapeamento — Slides ↔ PLANNER-ANTIGRAVITY

**Objetivo:** Rastreabilidade entre cada slide e a documentação fonte.

---

## Tabela de Mapeamento

| Slide | Título | Documentos Fonte | Seções |
|-------|--------|------------------|--------|
| 1 | Título | DIARIO_DE_BORDO, CONTROLE_GERAL | Visão geral |
| 2 | O que temos hoje | CONTROLE_GERAL, v3_investidores | 7 agentes, LEGO |
| 3 | Multi-Tenancy | ANALISE_MULTI_TENANCY | §2–§6 |
| 4 | Novos Módulos | ANALISE_MULTI_TENANCY §3–§4, F1/F2 specs | admin, gestor |
| 5 | Roadmap Paralelo | PLANO_MESTRE, T1–T5 | Trilhas, prioridades |
| 6 | Demo Investidores | PLANO_DEMO_INVESTIDORES | 3 DEVs, Pierre, Minerva |
| 7 | TenantContext | F0_ESPECIFICACAO_FUNCIONAL | RF-F0-001 a RF-F0-006 |
| 8 | Stack e Arquitetura | v3_investidores, FLUXO_DE_TRABALHO | Stack, princípios |
| 9 | Mercado | v3_investidores, ANALISE §9 | SaaS, LGPD |
| 10 | Fechamento | PLANO_DEMO, CONTROLE_GERAL | Próximos passos |

---

## Deep Dive — Conteúdo por Slide

### Slide 2 — Deep Dive: Arquitetura LEGO
- Fonte: v3_investidores slide 3
- Conteúdo: APIs padronizadas, comercialização individual, deploy containerizado

### Slide 3 — Deep Dive: Fluxo Onboarding
- Fonte: ANALISE_MULTI_TENANCY §5
- Conteúdo: SuperAdmin → Admin → KC → DB → Gestor

### Slide 4 — Deep Dive: F1–F5
- Fonte: MULTI_TENANCY/DESENVOLVIMENTO/
- Conteúdo: F0 TenantContext, F1 admin, F2 gestor, F3 portal, F4 módulos, F5 billing

### Slide 5 — Deep Dive: Dependências
- Fonte: PLANO_MESTRE, T2_MULTI_TENANCY
- Conteúdo: Tabela de paralelismo, grafo F0→F1→F2

### Slide 6 — Deep Dive: 3 DEVs
- Fonte: PLANO_DEMO_INVESTIDORES
- Conteúdo: DEV1 Portal, DEV2 Pierre, DEV3 Minerva, cronograma

### Slide 7 — Deep Dive: Requisitos F0
- Fonte: F0_ESPECIFICACAO_FUNCIONAL
- Conteúdo: RF-F0-001 a RF-F0-006, fluxo de requisição

### Slide 8 — Deep Dive: Princípios
- Fonte: v3_investidores slide 7
- Conteúdo: Modularidade, event-driven, schema separation, LGPD

### Slide 9 — Deep Dive: Modelo de Negócio
- Fonte: v3_investidores slide 8
- Conteúdo: Tiers, diferenciais, stack open-source
