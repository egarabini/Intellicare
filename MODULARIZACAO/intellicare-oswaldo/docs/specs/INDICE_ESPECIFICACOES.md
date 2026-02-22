# OSWALDO — Indice de Especificacoes Funcionais

> Motor de Doencas Cronicas — Evolucao v1.0 -> v2.0
> Homenagem a Oswaldo Cruz (1872-1917), medico sanitarista e fundador da saude publica brasileira.

## Contexto

A Oswaldo v1.0.0 (~132 testes core, ~79% cobertura) entregou um base solida com:
- Estadiamento clinico correto para CKD, DM2 e HAS (KDIGO, ADA, ESC/ESH)
- Sistema de alertas threshold + trend
- Perfis de doenca configurados via YAML
- 6 endpoints REST com persistencia FHIR/PostgreSQL

**Gap analysis (2026-02-16) identificou ~60% das funcionalidades previstas como nao implementadas.**

A evolucao para v2.0 fecha esses gaps:
- Historico de estadiamento persistido com timeline
- Confidence score preenchido com algoritmo real
- Recomendacoes clinicas estruturadas (ABNT/PCDT)
- Subagente com contrato Wanda (`/api/v1/analyze`)
- Conselheiro de medicamentos baseado em guidelines
- Calculadora de risco cardiovascular (Framingham, CKD-EPI)
- Extensao a novas doencas cronicas
- Integracoes com Florence e Zilda
- Publicacao de alertas via Redis Stream

## Principios

1. **Guidelines primeiro** — KDIGO, ADA, SBC, PCDT do MS como fonte de verdade
2. **Extensibilidade via YAML** — nova doenca = novo arquivo YAML, sem codigo
3. **Graceful degradation** — Florence/Zilda indisponiveis nao travam o Oswaldo
4. **Compatibilidade v1.0** — todos os 98 testes existentes continuam passando
5. **Rastreabilidade** — toda recomendacao citada tem referencia da guideline

## Mapa de Fases

| Fase | Diretorio | Escopo | Pre-Requisitos |
|:---:|-----------|--------|----------------|
| 1 | `fase-01-completar-base/` | Historico + Confidence + Contrato Wanda | v1.0 |
| 2 | `fase-02-algoritmos-clinicos/` | Medicamentos + Risco CV + Novas doencas | Fase 1 |
| 3 | `fase-03-integracao-eventos/` | Florence + Zilda + Redis Stream | Fase 2 |

## Especificacoes por Fase

### Fase 1: Completar Base e Integrar com Wanda
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-O001 | [Historico e Tendencias](fase-01-completar-base/EF-O001_HISTORICO_TENDENCIAS.md) | Timeline de estadiamento + endpoint especifico |
| EF-O002 | [Confidence Score e Recomendacoes](fase-01-completar-base/EF-O002_CONFIDENCE_RECOMENDACOES.md) | Score de confianca + recomendacoes clinicas estruturadas |
| EF-O003 | [Subagente e Contrato Wanda](fase-01-completar-base/EF-O003_SUBAGENTE_CONTRATO_WANDA.md) | LangChain tools + /api/v1/analyze |

### Fase 2: Algoritmos Clinicos Avancados
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-O004 | [Conselheiro de Medicamentos](fase-02-algoritmos-clinicos/EF-O004_MEDICATION_ADVISOR.md) | Recomendacoes farmacologicas baseadas em PCDT/guidelines |
| EF-O005 | [Risco Cardiovascular](fase-02-algoritmos-clinicos/EF-O005_RISCO_CARDIOVASCULAR.md) | Framingham, CKD-EPI, risco Donabedian |
| EF-O006 | [Extensao de Doencas](fase-02-algoritmos-clinicos/EF-O006_EXTENSAO_DOENCAS.md) | DPOC, ICC, Dislipidemia via YAML |

### Fase 3: Integracao e Orquestracao
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-O007 | [Integracao Florence](fase-03-integracao-eventos/EF-O007_INTEGRACAO_FLORENCE.md) | Enriquecimento com exames e RAG clinico |
| EF-O008 | [Integracao Zilda](fase-03-integracao-eventos/EF-O008_INTEGRACAO_ZILDA.md) | Disponibilidade de servicos por territorio |
| EF-O009 | [Publicacao de Eventos](fase-03-integracao-eventos/EF-O009_EVENTOS_REDIS_STREAM.md) | Alertas e atualizacoes via Redis Stream |

## Dependencias Externas

| Servico | Uso |
|---------|-----|
| PostgreSQL | Persistencia FHIR (ja implementado) |
| Redis | Cache de IPS + publicacao de eventos |
| Ollama | LLM local para subagente (llama3.1:8b) |
| Florence (8002) | Enriquecimento com exames e RAG |
| Zilda (8003) | Verificacao de disponibilidade de servicos |
| Wanda (8007) | Orquestradora — consome `/api/v1/analyze` |

## Compatibilidade

Todos os **98 testes v1.0** devem continuar passando apos cada fase.
Os **6 endpoints existentes** nao devem quebrar.
