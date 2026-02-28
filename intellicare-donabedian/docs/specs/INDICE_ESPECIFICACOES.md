# DONABEDIAN — Indice de Especificacoes Funcionais

> Avaliacao de Qualidade Assistencial — Evolucao v1.0 -> v2.0
> Homenagem a Avedis Donabedian (1919-2000), medico e epidemiologista, pai da avaliacao de qualidade em saude.

## Contexto

O Donabedian v1.0.0 (~363 testes, ~80% cobertura) entregou uma base robusta com:
- 30 endpoints REST (CRUD completo)
- Dashboard Streamlit com radar dos 7 pilares e timeline
- Schema isolation OLTP/OLAP com consolidacao automatica
- Seed com 15+ indicadores e 12 meses de dados
- Autenticacao Keycloak e event publishing

**Gap analysis (2026-02-16) identificou que os pilares de Donabedian estao implementados como "estrutura de dados", mas as funcionalidades de analise real (benchmarking, equidade, custo-beneficio, integracao com dados clinicos) ainda nao existem.**

A evolucao para v2.0 transforma o Donabedian de um "banco de dados de indicadores" em um **motor de avaliacao de qualidade** que:
- Responde a Wanda via subagente conversacional
- Gera relatorios executivos automaticamente
- Compara com benchmarks nacionais e regionais
- Analisa equidade e disparidades
- Calcula eficiencia real (custo-beneficio)
- Alimenta-se automaticamente de dados do Oswaldo e Zilda

## Principios

1. **Donabedian + pilares + triada** — cada funcionalidade referencia o pilar que fortalece
2. **Sem reinventar** — indicadores de DATASUS ja processados pela Zilda; Donabedian consome
3. **Gestores como usuarios primarios** — relatorios, benchmarks e graficos sao para gestao
4. **Compatibilidade v1.0** — todos os 363 testes existentes continuam passando
5. **Audit trail** — toda avaliacao deve ser rastreavel com data, fonte e metodologia

## Mapa de Fases

| Fase | Diretorio | Escopo | Pre-Requisitos |
|:---:|-----------|--------|----------------|
| 1 | `fase-01-integracao-wanda/` | Subagente Wanda + Relatorios + CSV Import | v1.0 |
| 2 | `fase-02-analise-avancada/` | Benchmarking + Equidade + Eficiencia | Fase 1 |
| 3 | `fase-03-automacao-dados/` | Integracao Oswaldo + Zilda + Alertas | Fase 2 |

## Especificacoes por Fase

### Fase 1: Integracao com Wanda e Gestao de Dados
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-D001 | [Subagente e Contrato Wanda](fase-01-integracao-wanda/EF-D001_SUBAGENTE_CONTRATO_WANDA.md) | LangChain tools + /api/v1/analyze |
| EF-D002 | [Relatorios de Qualidade](fase-01-integracao-wanda/EF-D002_RELATORIOS.md) | PDF/HTML + comparativo de periodos |
| EF-D003 | [Importacao em Lote](fase-01-integracao-wanda/EF-D003_IMPORTACAO_LOTE.md) | CSV/JSON bulk upload + validacao |

### Fase 2: Analise Avancada de Qualidade
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-D004 | [Benchmarking Nacional](fase-02-analise-avancada/EF-D004_BENCHMARKING.md) | Comparacao com DATASUS e padroes MS |
| EF-D005 | [Equidade e Estratificacao](fase-02-analise-avancada/EF-D005_EQUIDADE.md) | Disparidades demograficas e regionais |
| EF-D006 | [Custo-Beneficio e Eficiencia](fase-02-analise-avancada/EF-D006_EFICIENCIA_CUSTO.md) | QALY, ROI, analise de valor |

### Fase 3: Automacao e Dados em Tempo Real
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-D007 | [Integracao Oswaldo](fase-03-automacao-dados/EF-D007_INTEGRACAO_OSWALDO.md) | Indicadores clinicos auto-alimentados |
| EF-D008 | [Integracao Zilda](fase-03-automacao-dados/EF-D008_INTEGRACAO_ZILDA.md) | Indicadores territoriais + cobertura ESF |
| EF-D009 | [Alertas e Recomendacoes](fase-03-automacao-dados/EF-D009_ALERTAS_RECOMENDACOES.md) | Alertas inteligentes para gestao |

## Dependencias Externas

| Servico | Uso |
|---------|-----|
| PostgreSQL | Persistencia (ja implementado — 2 schemas) |
| Redis | Cache + eventos (ja implementado parcialmente) |
| Ollama | LLM local para subagente (llama3.1:8b) |
| Oswaldo (8001) | Indicadores clinicos (estadiamento, alertas) |
| Zilda (8003) | Indicadores territoriais (CNES, DATASUS, ESF) |
| Wanda (8007) | Orquestradora — consome `/api/v1/analyze` |

## Compatibilidade

Todos os **363 testes v1.0** devem continuar passando apos cada fase.
Os **30 endpoints existentes** nao devem quebrar.
