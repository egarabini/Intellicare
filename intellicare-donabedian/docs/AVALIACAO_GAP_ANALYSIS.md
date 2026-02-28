# Donabedian — Gap Analysis (2026-02-16)

> Avaliacao do que esta implementado vs. especificado na v1.0.0 — base para a evolucao v2.0.
> Feito pelo DEV1 com alto nivel de maturidade tecnica.

## Resumo Executivo

O Donabedian v1.0.0 (~363 testes, ~80% cobertura) e o modulo mais maduro da plataforma — entregou CRUD completo, 30 endpoints REST, dashboard Streamlit com 4 paginas (radar dos 7 pilares, timeline, indicadores), autenticacao Keycloak, schema isolation OLTP/OLAP, consolidacao via Redis Stream e seed com 15+ indicadores.

**Maturidade geral: 7/10** — infraestrutura robusta, pilares conceituais; funcionalidades avancadas e integracoes ainda pendentes.

---

## O que foi Entregue (Core Solido)

| Componente | Maturidade | Notas |
|-----------|-----------|-------|
| Modelos de dados (4 tabelas) | 9/10 | UUID, audit, soft delete, optimistic locking |
| API REST (30 endpoints) | 9/10 | CRUD completo, Keycloak, type-safe |
| Dashboard Streamlit (4 paginas) | 8/10 | Radar 7 pilares, timeline 12m, indicadores |
| Testes (363 funcs, ~80% cov) | 8/10 | Models, schemas, API, integration, E2E |
| Schema isolation (OLTP/OLAP) | 9/10 | intellicare_donabedian + _analitico |
| Consolidacao Redis | 7/10 | Worker assincrono operacional→analitico |
| Calculo de scores (7 pilares) | 7/10 | Ponderado por peso, status automatico |
| Seed data (15+ indicadores) | 8/10 | 12 meses de dados, associacoes pilares |

---

## Maturidade por Pilar de Donabedian

| Pilar | Score | Implementado | Faltando |
|-------|-------|-------------|---------|
| **1. Eficacia** | 6/10 | Indicadores seed, calculo score | Benchmark, comparativo nacional |
| **2. Efetividade** | 6/10 | Medicoes, status automatico | DATASUS, FHIR real, predicao |
| **3. Eficiencia** | 5/10 | Indicadores seed basicos | Custo-beneficio, QALY, ROI |
| **4. Otimidade** | 5/10 | Recomendacoes basicas (alerts) | Otimizacao Pareto, priorizacao |
| **5. Aceitabilidade** | 6/10 | Satisfacao como indicador | Tracking real de adesao, NPS |
| **6. Legitimidade** | 6/10 | Cobertura ESF como indicador | Validacao contra normas SUS |
| **7. Equidade** | 4/10 | Conceitual | Estratificacao demografica, disparidades |

**Score medio dos pilares: 5.4/10 — implementacao conceitual, nao analitica**

---

## Gaps Criticos (0% implementados)

| Gap | Impacto | Justificativa |
|-----|---------|---------------|
| Subagente + `/api/v1/analyze` (contrato Wanda) | **BLOQUEADOR** | Wanda nao consegue usar o Donabedian sem este endpoint |
| Relatorios PDF/HTML | Alto | Gestores precisam de relatorio para reunioes de qualidade |
| Importacao em lote (CSV) | Alto | Hospitais tem dados exportados de outros sistemas |
| Benchmarking (DATASUS/nacional) | Alto | Pilar Efetividade sem referencia = "efetivo em relacao a que?" |
| Equidade — estratificacao demografica | Medio | Pilar mais fraco, apenas conceitual |
| Custo-beneficio (QALY/ROI) | Medio | Pilar Eficiencia sem calculo real |

---

## Gaps Parciais

| Gap | Status | Detalhe |
|-----|--------|---------|
| Recomendacoes automatizadas | Parcial | Alertas de semaforo existem, sem recomendacao clinica/gestao |
| Multi-tenancy | Parcial | Setup parcial via DATABASE_SCHEMA, sem UI de gestao |
| Redis cache na API | Parcial | Streamlit usa cache local, API nao tem Redis cache |
| RBAC testado | Parcial | Keycloak integrado mas sem testes de permissoes |

---

## Mapa de Gaps para Especificacoes v2.0

### Fase 1 — Integracao com Wanda e Gestao de Dados
| EF | Titulo |
|----|--------|
| EF-D001 | Subagente Donabedian + Contrato Wanda (`/api/v1/analyze`) |
| EF-D002 | Relatorios de Qualidade (PDF/HTML + comparativo) |
| EF-D003 | Importacao em Lote (CSV/JSON upload) |

### Fase 2 — Analise Avancada de Qualidade
| EF | Titulo |
|----|--------|
| EF-D004 | Benchmarking e Referencia Nacional (DATASUS) |
| EF-D005 | Equidade e Estratificacao Demografica |
| EF-D006 | Eficiencia: Custo-Beneficio e QALY |

### Fase 3 — Automacao e Dados em Tempo Real
| EF | Titulo |
|----|--------|
| EF-D007 | Integracao Oswaldo (indicadores clinicos auto-alimentados) |
| EF-D008 | Integracao Zilda (indicadores territoriais + ESF) |
| EF-D009 | Alertas Inteligentes e Recomendacoes para Gestao |

---

## Compatibilidade

Os **363 testes v1.0** devem continuar passando apos cada fase.
Os **30 endpoints existentes** nao devem quebrar.
A estrutura do banco (4 tabelas + 2 schemas) e base imutavel.
