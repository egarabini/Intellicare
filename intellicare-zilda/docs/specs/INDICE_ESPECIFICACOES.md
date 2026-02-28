# ZILDA — Indice de Especificacoes Funcionais

> Agente de Dados Territoriais e Saude Brasileira — Evolucao v1.0 -> v2.0
> Homenagem a Zilda Arns (1934-2010), medica pediatra e sanitarista, fundadora da Pastoral da Crianca.

## Contexto

A Zilda v1.0.0 (68 testes, 95% cobertura) entregou uma base solida com:
- Integracao com API CNES (estabelecimentos, tipos, regioes)
- Motor territorial basico (resumo, contexto regional)
- 9 endpoints REST com cache em memoria

**Gap analysis (2026-02-16) identificou ~70% das funcionalidades especificadas como nao implementadas.**

A evolucao para v2.0 fecha esses gaps:
- Enriquecimento completo do CNES (leitos, profissionais, servicos)
- Subagente com contrato Wanda (`/api/v1/analyze`)
- Cliente DATASUS (internacoes, mortalidade, nascimentos)
- Cobertura de equipes de Saude da Familia (e-SUS APS)
- Motor de analise de vazios assistenciais
- Analise de oferta vs demanda por territorio

## Principios

1. **APIs publicas primeiro** — usar o que o MS disponibiliza antes de scraping
2. **Cache agressivo** — dados do DATASUS nao mudam com frequencia
3. **Graceful degradation** — API externa indisponivel nao crasha o modulo
4. **FHIR como saida** — dados territoriais exportaveis como FHIR Location/Organization
5. **Compatibilidade v1.0** — todos os 68 testes existentes continuam passando

## Mapa de Fases

| Fase | Diretorio | Escopo | Pre-Requisitos |
|:---:|-----------|--------|----------------|
| 1 | `fase-01-completar-cnes/` | CNES completo + Subagente Wanda | v1.0 |
| 2 | `fase-02-datasus/` | DATASUS (SIH, SIM, SIA, SINASC) | Fase 1 |
| 3 | `fase-03-analise-territorial/` | ESF + Vazios + Oferta vs Demanda | Fase 2 |

## Especificacoes por Fase

### Fase 1: Completar CNES e Integrar com Wanda
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-Z001 | [Enriquecimento CNES](fase-01-completar-cnes/EF-Z001_ENRIQUECIMENTO_CNES.md) | Leitos, profissionais e servicos da API CNES |
| EF-Z002 | [Subagente e Contrato Wanda](fase-01-completar-cnes/EF-Z002_SUBAGENTE_CONTRATO_WANDA.md) | LangChain tools + /api/v1/analyze |

### Fase 2: DATASUS
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-Z003 | [DATASUS Producao Hospitalar](fase-02-datasus/EF-Z003_DATASUS_HOSPITALAR.md) | SIH — internacoes por municipio/CID |
| EF-Z004 | [DATASUS Mortalidade e Nascimentos](fase-02-datasus/EF-Z004_DATASUS_SIM_SINASC.md) | SIM e SINASC — indicadores vitais |

### Fase 3: Analise Territorial Avancada
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-Z005 | [Cobertura ESF](fase-03-analise-territorial/EF-Z005_COBERTURA_ESF.md) | Equipes Saude da Familia via e-SUS APS |
| EF-Z006 | [Motor de Vazios Assistenciais](fase-03-analise-territorial/EF-Z006_VAZIOS_ASSISTENCIAIS.md) | Identificar regioes sem cobertura adequada |
| EF-Z007 | [Analise Oferta vs Demanda](fase-03-analise-territorial/EF-Z007_OFERTA_DEMANDA.md) | Capacidade instalada vs necessidade populacional |

## Dependencias Externas

| Servico | URL | Uso |
|---------|-----|-----|
| CNES API | `https://apidadosabertos.saude.gov.br/cnes/` | Estabelecimentos, profissionais, leitos, servicos |
| DATASUS OpenData | `https://apidadosabertos.saude.gov.br` | SIH, SIM, SIA, SINASC |
| e-SUS APS | `https://sisab.saude.gov.br` | Equipes ESF, cobertura |
| IBGE API | `https://servicodados.ibge.gov.br` | Populacao, municipios, regioes |

## Compatibilidade

Todos os **68 testes v1.0** devem continuar passando apos cada fase.
Os **9 endpoints existentes** nao devem quebrar.
