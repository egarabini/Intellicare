# GERALDA — Indice de Especificacoes Funcionais

> Agente de Acompanhamento do Paciente — Evolucao v1.0 -> v2.0
> Homenagem a Geralda Lopes da Silva, enfermeira brasileira pioneira no cuidado comunitario.

## Contexto

A Geralda v1.0.0 (108 testes, 96% cobertura) implementa um motor CRUD em memoria com 24 endpoints REST para planos de cuidado, tarefas, lembretes e educacao em saude.

A evolucao para v2.0 transforma a Geralda em um **agente inteligente real**, com:
- Persistencia em banco de dados (PostgreSQL)
- Inteligencia artificial local (Ollama + LangChain)
- Protocolo MCP (Model-Context-Protocol) para jornada do paciente
- Integracao com todos os agentes do ecossistema via Wanda
- Comunicacao em tempo real com pacientes (Synapse/Element)
- Agendamento de consultas online (Jitsi)

## Principios Arquiteturais

1. **IA como assistente, nunca decisora** — Toda acao clinica requer validacao humana
2. **Execucao deterministica** — Protocolos auditaveis e versionados
3. **FHIR R4 como lingua franca** — Dados clinicos sempre em FHIR
4. **Ollama para autonomia** — LLM local, sem dependencia de APIs externas
5. **Separacao Model-Context-Protocol** — Estado, contexto e regras separados
6. **Seguranca primeiro** — IPS-First, LGPD, logs de auditoria

## Mapa de Fases

| Fase | Diretorio | Escopo | Pre-Requisitos |
|:---:|-----------|--------|----------------|
| 1 | `fase-01-fundacao-persistencia/` | PostgreSQL + FHIR CarePlan | Core v1.0 |
| 2 | `fase-02-motor-ia/` | Ollama + LangChain + NLP | Fase 1 |
| 3 | `fase-03-mcp-protocolo/` | Eventos + Contextos + Protocolos | Fase 1 |
| 4 | `fase-04-integracao-agentes/` | Wanda + Florence + Oswaldo | Fases 1-3 |
| 5 | `fase-05-jornada-paciente/` | Ciclo completo do paciente | Fases 1-4 |
| 6 | `fase-06-comunicacao-agendamento/` | Synapse + Jitsi + Notificacoes | Fases 1-5 |

## Especificacoes por Fase

### Fase 1: Fundacao e Persistencia
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-001 | [Persistencia PostgreSQL](fase-01-fundacao-persistencia/EF-001_PERSISTENCIA_POSTGRESQL.md) | Migrar de in-memory para PostgreSQL com Alembic |
| EF-002 | [Integracao FHIR CarePlan](fase-01-fundacao-persistencia/EF-002_INTEGRACAO_FHIR_CAREPLAN.md) | Ler/escrever CarePlan FHIR R4 |

### Fase 2: Motor de IA
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-003 | [Integracao Ollama](fase-02-motor-ia/EF-003_INTEGRACAO_OLLAMA.md) | LLM local para raciocinio clinico |
| EF-004 | [Linguagem Acessivel](fase-02-motor-ia/EF-004_LINGUAGEM_ACESSIVEL.md) | Simplificacao de linguagem medica via IA |
| EF-005 | [Educacao Personalizada](fase-02-motor-ia/EF-005_EDUCACAO_PERSONALIZADA.md) | Conteudo educativo gerado/adaptado por IA |

### Fase 3: MCP — Protocolo
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-006 | [Motor de Eventos](fase-03-mcp-protocolo/EF-006_MOTOR_EVENTOS.md) | Sistema de eventos da jornada do paciente |
| EF-007 | [Contextos de Jornada](fase-03-mcp-protocolo/EF-007_CONTEXTOS_JORNADA.md) | Identificacao e gestao de contextos |
| EF-008 | [Protocolos Institucionais](fase-03-mcp-protocolo/EF-008_PROTOCOLOS_INSTITUCIONAIS.md) | Motor de protocolos versionados |

### Fase 4: Integracao Inter-Agentes
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-009 | [Integracao Wanda](fase-04-integracao-agentes/EF-009_INTEGRACAO_WANDA.md) | Orquestracao via Wanda |
| EF-010 | [Integracao Florence e Oswaldo](fase-04-integracao-agentes/EF-010_INTEGRACAO_FLORENCE_OSWALDO.md) | Consumo de dados clinicos e cronicos |
| EF-011 | [Integracao Comunicacao](fase-04-integracao-agentes/EF-011_INTEGRACAO_COMUNICACAO.md) | Synapse/Element para mensageria |

### Fase 5: Jornada do Paciente
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-012 | [Ciclo de Vida do Paciente](fase-05-jornada-paciente/EF-012_CICLO_VIDA_PACIENTE.md) | Admissao -> Tratamento -> Alta -> Acompanhamento |
| EF-013 | [Pre e Pos Consulta](fase-05-jornada-paciente/EF-013_PRE_POS_CONSULTA.md) | Preparacao e follow-up de consultas |
| EF-014 | [Adesao Inteligente](fase-05-jornada-paciente/EF-014_ADESAO_INTELIGENTE.md) | Monitoramento preditivo de adesao |

### Fase 6: Comunicacao e Agendamento
| ID | Documento | Descricao |
|----|-----------|-----------|
| EF-015 | [Notificacoes em Tempo Real](fase-06-comunicacao-agendamento/EF-015_NOTIFICACOES_TEMPO_REAL.md) | Push notifications via Synapse |
| EF-016 | [Agendamento de Consultas](fase-06-comunicacao-agendamento/EF-016_AGENDAMENTO_CONSULTAS.md) | Integracao Jitsi para teleconsultas |
| EF-017 | [Canal Equipe-Paciente](fase-06-comunicacao-agendamento/EF-017_CANAL_EQUIPE_PACIENTE.md) | Chat bidirecional com IA |

## Fluxo de Trabalho

```
1. DEV0 gera ESPECIFICACAO FUNCIONAL (este documento)
      |
2. DEV(n) le e gera ESPECIFICACAO TECNICA + PLANO DE IMPLEMENTACAO
      |
3. Equipe analisa e autoriza desenvolvimento
      |
4. DEV(n) implementa com testes (>= 80% cobertura)
      |
5. DEV0 revisa e integra
```

## Dependencias Externas

| Servico | Porta | Uso |
|---------|-------|-----|
| PostgreSQL | 5432 | Persistencia |
| Ollama | 11434 | LLM local |
| FHIR Server (HAPI) | 8080 | Dados clinicos |
| Synapse (Matrix) | 8008 | Mensageria |
| Jitsi Meet | 8443 | Videoconferencia |
| Keycloak | 8180 | Autenticacao |
| Redis | 6379 | Cache + Eventos |

## Contato

- **DEV0**: Especificacoes funcionais, revisao, integracao
- **DEV(n)**: Especificacao tecnica e implementacao por fase
