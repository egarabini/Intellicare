# WANDA — Indice de Especificacoes Funcionais

> Agente Orquestradora do Ecossistema IntelliCare — Evolucao v1.0 -> v2.0
> Homenagem a Wanda de Aguiar Horta, enfermeira brasileira pioneira na sistematizacao da assistencia de enfermagem.
>
> **Documento de visao:** `DOCUMENTACAO/INTELLICARE_V5_1_VISAO_GERAL.md`
> **Versao:** 2.0 (IntelliCare V5.1.0) — 13 EFs (10 base + 3 novas para V5)

## Contexto

A Wanda v1.0.0 (69 testes, 93% cobertura) implementa:
- Descoberta dinamica de modulos via HTTP (`/api/v1/info`)
- Roteamento por palavras-chave (sem LLM)
- Agregacao simples de respostas
- Regras de seguranca (IPS-First, anti-fabricacao)
- 8 endpoints REST

A evolucao para v2.0 transforma a Wanda em uma **orquestradora verdadeiramente inteligente**:
- Roteamento por LLM (intencao, nao keywords)
- LangGraph para workflows multi-agente complexos
- Registro persistente de modulos (PostgreSQL)
- Monitoramento proativo de saude dos agentes
- Circuit breaker e resiliencia
- Orquestracao proativa (nao so reativa)
- Observabilidade completa (traces, metricas, logs)

## Principios Arquiteturais

1. **Wanda nao sabe de clinica** — ela roteadora, nao clinica
2. **Desacoplamento total** — Wanda nunca importa outros agentes diretamente
3. **HTTP como contrato** — toda comunicacao via `/api/v1/analyze` padrao
4. **IPS-First obrigatoria** — toda consulta com patient_id carrega IPS antes
5. **Safety-first** — regras de seguranca sao inviolaveis
6. **LLM como raciocinio, nao resposta** — LLM decide rota, agentes respondem
7. **Observabilidade total** — toda decisao rastreavel

## Papel da Wanda no Ecossistema

```
┌─────────────────────────────────────────────────────────────────┐
│                         WANDA                                    │
│                (Orquestradora Central)                           │
│                                                                  │
│   ┌──────────┐                               ┌──────────────┐  │
│   │ Portal   │──────────────────────────────►│              │  │
│   │ (User)   │                               │   WANDA      │  │
│   └──────────┘                               │   v2.0       │  │
│                                              │              │  │
│   ┌──────────┐    Descoberta HTTP            │  LangGraph   │  │
│   │ Geralda  │◄────────────────────────────►│  Routing     │  │
│   └──────────┘                               │  Aggregation │  │
│                                              │  Safety      │  │
│   ┌──────────┐                               └──────┬───────┘  │
│   │ Florence │◄─────────────────────────────────────┤          │
│   └──────────┘                                      │          │
│                                                      │          │
│   ┌──────────┐                                      │          │
│   │ Oswaldo  │◄─────────────────────────────────────┤          │
│   └──────────┘                                      │          │
│                                                      │          │
│   ┌──────────┐                                      │          │
│   │  Zilda   │◄─────────────────────────────────────┘          │
│   └──────────┘                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisitos V5.1.0

| Prerequisito | Status | Necessario para |
|---|---|---|
| V5.0.1 MINERVA (:8008 /mcp/tools) | ⏳ DEV1 em andamento | EF-W011 |
| V5.0.1 PIERRE (:8009 /mcp/tools) | ⏳ DEV1 em andamento | EF-W011 |
| Comunicacao D1+D2 (/api/v1/routing) | ⏳ DEV2 em andamento | EF-W007 |
| Ollama qwen2.5:72b | ✅ Operacional | EF-W003, W004 |
| FLOWISE | ✅ Operacional | EF-W013 |
| KESTRA | ✅ Operacional | EF-W006 |

## Mapa de Fases

| Fase | Diretorio | Escopo | Pre-Requisitos |
|:---:|-----------|--------|----------------|
| 1 | `fase-01-fundacao-orquestracao/` | PostgreSQL + Module Registry + MCP Client | Core v1.0, V5.0.1 |
| 2 | `fase-02-motor-roteamento-ia/` | Ollama + LangChain + Intent Routing | Fase 1 |
| 3 | `fase-03-orquestracao-avancada/` | LangGraph Workflows + Proactive + Bot RC + Dr. Nise | Fase 2 |
| 4 | `fase-04-observabilidade-resiliencia/` | Circuit Breaker + Traces + Metricas | Fase 1 |

## Especificacoes por Fase

### Fase 1: Fundacao e Orquestracao
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-W001 | [Persistencia e Module Registry](fase-01-fundacao-orquestracao/EF-W001_PERSISTENCIA_MODULE_REGISTRY.md) | PostgreSQL + registro persistente de agentes HTTP e MCP |
| EF-W002 | [IPS-First Aprimorado](fase-01-fundacao-orquestracao/EF-W002_IPS_FIRST_APRIMORADO.md) | Cache de IPS, validacao e enriquecimento |
| **EF-W011** | **[MCP Client Integration](fase-01-fundacao-orquestracao/EF-W011_MCP_CLIENT.md)** | **[NOVO V5] Consome MINERVA (:8008) e PIERRE (:8009) via MCP SSE** |

### Fase 2: Motor de Roteamento com IA
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-W003 | [Roteamento por Intencao (LLM)](fase-02-motor-roteamento-ia/EF-W003_ROTEAMENTO_INTENCAO.md) | Substituir keywords por LLM via Ollama — roteia para HTTP ou MCP |
| EF-W004 | [Agregacao Inteligente](fase-02-motor-roteamento-ia/EF-W004_AGREGACAO_INTELIGENTE.md) | LLM agrega respostas multi-agente + MCP em sintese coerente |

### Fase 3: Orquestracao Avancada
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-W005 | [Workflows LangGraph](fase-03-orquestracao-avancada/EF-W005_WORKFLOWS_LANGGRAPH.md) | Fluxos multi-passo complexos com HTTP tools + MCP tools |
| EF-W006 | [Orquestracao Proativa (KESTRA)](fase-03-orquestracao-avancada/EF-W006_ORQUESTRACAO_PROATIVA.md) | KESTRA aciona WANDA para revisoes e relatorios agendados |
| EF-W007 | [Coordenacao de Alertas](fase-03-orquestracao-avancada/EF-W007_COORDENACAO_ALERTAS.md) | Agregar alertas multi-agente → Comunicacao (Rocket.Chat) |
| **EF-W012** | **[Bot Rocket.Chat Handler](fase-03-orquestracao-avancada/EF-W012_BOT_RC_HANDLER.md)** | **[NOVO V5] Processa comandos do @intellicare (/paciente, /guideline, etc.)** |
| **EF-W013** | **[Dr. Nise / FLOWISE](fase-03-orquestracao-avancada/EF-W013_DR_NISE_FLOWISE.md)** | **[NOVO V5] Chatbot do paciente delegado ao FLOWISE** |

### Fase 4: Observabilidade e Resiliencia
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-W008 | [Circuit Breaker e Resiliencia](fase-04-observabilidade-resiliencia/EF-W008_CIRCUIT_BREAKER.md) | Tolerancia a falha de agentes HTTP e MCP servers |
| EF-W009 | [Rastreabilidade de Decisoes](fase-04-observabilidade-resiliencia/EF-W009_RASTREABILIDADE.md) | correlation_id propagado em todos os modulos chamados |
| EF-W010 | [Metricas e Observabilidade](fase-04-observabilidade-resiliencia/EF-W010_METRICAS_OBSERVABILIDADE.md) | Prometheus — latencia por modulo, MCP calls, bot commands |

## Fluxo de Trabalho

```
1. DEV0 gera ESPECIFICACAO FUNCIONAL (este documento)
      |
2. DEV(n) le e gera ESPECIFICACAO TECNICA + PLANO DE IMPLEMENTACAO
      |
3. Equipe analisa e autoriza desenvolvimento
      |
4. DEV(n) implementa com testes (>= 85% cobertura)
      |
5. DEV0 revisa e integra
```

## Dependencias Externas

| Servico | Porta | Uso |
|---------|-------|-----|
| PostgreSQL | 5432 | Module registry, execucoes, audit |
| Ollama | 11434 | Qwen2.5-72B — routing, agregacao e sintese |
| Redis | 6379 | Cache IPS, Circuit Breaker state |
| Prometheus | 9090 | Metricas |
| Agentes HTTP | 8001-8007 | Oswaldo, Florence, Zilda, Donabedian, Comunicacao, Geralda, Portal |
| **MINERVA (MCP)** | **8008** | **OCR — parse_lab_result, extract_document, search_documents** |
| **PIERRE (MCP)** | **8009** | **SuperZ — web_search, search_pubmed, check_regulatory, analyze_text** |
| **FLOWISE** | (servidor) | **Dr. Nise chatbot — education flow** |
| **KESTRA** | (servidor) | **Webhooks para triggers proativos** |
| **Rocket.Chat** | (servidor) | **Bot @intellicare — incoming webhooks** |

## Compatibilidade v1.0

Todos os 8 endpoints existentes devem continuar funcionando:
- `GET /api/v1/health`
- `GET /api/v1/info`
- `POST /api/v1/analyze`
- `POST /api/v1/query`
- `POST /api/v1/events`
- `GET /api/v1/discover`
- `GET /api/v1/modules`
- `POST /api/v1/orchestrate`

Os 69 testes existentes devem continuar passando apos cada fase.
