# IntelliCare V5.1.0 — WANDA: A Orquestradora Completa

**Data:** 2026-02-16
**Versao:** 5.1.0
**Status:** Planejamento — pronto para desenvolvimento
**DEV responsavel:** DEV-WANDA (independente, apos V5.0.1)

---

## 1. Contexto e Evolucao

| Versao | Marco | O que entrega |
|--------|-------|----------------|
| V1 | POC | Monolito, agentes acoplados |
| V2 | LEGO | 8 modulos independentes |
| V3 | Agentes nomeados | 6 agentes, ~705 testes, FHIR R4 |
| V4 | Maturidade clinica | Oswaldo (9 EFs), Donabedian (7 pilares), Florence (9 EFs) |
| V5.0.0 | Specs completas | Comunicacao (7 dominios), OCR/SuperZ especificados |
| **V5.0.1** | **MCP Servers** | **MINERVA (OCR, 8008) + PIERRE (SuperZ, 8009) implementados** |
| **V5.1.0** | **WANDA Orquestradora** | **WANDA como cerebro central de toda a plataforma** |

---

## 2. O Que E a V5.1.0

V5.1.0 e o **ponto de culminacao** do IntelliCare: WANDA conecta todos os modulos, consome as ferramentas MCP, integra com comunicacao e produz inteligencia clinica sintetica que nenhum agente isolado consegue entregar.

### A Metafora

```
V5.0.x entregou as pecas LEGO.
V5.1.0 monta o brinquedo.
```

Com V5.1.0:
- Um medico pergunta ao bot @intellicare no Rocket.Chat: *"Como esta Maria Santos?"*
- WANDA aciona: Oswaldo (estadiamento DRC) + Florence (interpretar exames) + Geralda (plano de cuidado) + PIERRE (guideline KDIGO 2024) + MINERVA (laudo PDF mais recente)
- WANDA consolida tudo e responde em PT-BR com citacoes e recomendacoes de conduta
- Se houver alerta critico, WANDA envia notificacao via Comunicacao (Rocket.Chat + WhatsApp)

---

## 3. Arquitetura V5.1.0

```
                        ╔═══════════════════════════════════════╗
                        ║         WANDA (Porta 8007)            ║
                        ║    Orquestradora Suprema V2.0         ║
                        ║                                        ║
                        ║  ┌─────────────────────────────────┐  ║
                        ║  │     LangGraph Agent Graph        │  ║
                        ║  │  ┌────────┐ ┌────────────────┐  │  ║
                        ║  │  │ Router │→│ PlanningNode   │  │  ║
                        ║  │  └────────┘ └────────────────┘  │  ║
                        ║  │  ┌─────────────────────────────┐ │  ║
                        ║  │  │      ToolExecutionNode      │ │  ║
                        ║  │  │  HTTP Tools | MCP Tools      │ │  ║
                        ║  │  └─────────────────────────────┘ │  ║
                        ║  │  ┌─────────────────────────────┐ │  ║
                        ║  │  │     SynthesisNode            │ │  ║
                        ║  │  │  Qwen2.5-72B (Ollama)        │ │  ║
                        ║  │  └─────────────────────────────┘ │  ║
                        ║  └─────────────────────────────────┘  ║
                        ║                                        ║
                        ║  MCP Client ──────────────────────►   ║
                        ╚════════════════════════════════════════╝
                              │                    │
              ┌───────────────┼────────────────────┼───────────────┐
              │               │                    │               │
    ┌─────────▼──────┐ ┌──────▼───────┐ ┌─────────▼──────┐ ┌─────▼──────┐
    │ HTTP Modules   │ │ MCP Servers  │ │ Comunicacao    │ │  FLOWISE   │
    │ :8001 Oswaldo  │ │ :8008 MINERVA│ │ Rocket.Chat    │ │  Dr. Nise  │
    │ :8002 Florence │ │ :8009 PIERRE │ │ Jitsi/Telecon  │ │  Chatbot   │
    │ :8003 Zilda    │ └──────────────┘ │ WhatsApp/SMS   │ └────────────┘
    │ :8004 Donabed  │                  └────────────────┘
    │ :8006 Geralda  │
    │ :3000 Portal   │
    └────────────────┘
              │
    ┌─────────▼──────────────────────────────────┐
    │           KESTRA (Event Orchestration)      │
    │  Triggers proativos: revisao diaria,        │
    │  relatorio semanal, ciclo de adesao         │
    └────────────────────────────────────────────┘
```

---

## 4. O que WANDA V2.0 Sabe Fazer

### 4.1 Consultas Sinteticas (Multi-Modulo)

```
Medico: "Resuma o caso clinico de Maria Santos"
  │
  ▼
WANDA (LangGraph):
  ├── Oswaldo → estadiamento DRC G3b, DM2 descompensada, HAS estagio 2
  ├── Florence → interpret lab (eGFR 28.5↓, HbA1c 8.2%, creatinina 2.1)
  ├── Geralda → plano de cuidado: 14 tarefas, 8 concluidas, 2 atrasadas
  ├── PIERRE → busca "KDIGO 2024 DRC G3b manejo" → retorna recomendacoes
  └── MINERVA → ultimo laudo PDF → extrai dados e indexa
  │
  ▼
Sintese consolidada em PT-BR com fonte para cada dado
```

### 4.2 Comandos via Bot Rocket.Chat

| Comando | WANDA aciona | Retorna |
|---------|-------------|---------|
| `/paciente P001` | Oswaldo + Florence + Geralda | Resumo clinico formatado |
| `/alertas hoje` | Oswaldo alerts list | Feed de alertas por severidade |
| `/exames P001` | Florence + MINERVA (laudos PDF) | Resultados interpretados |
| `/guideline "SGLT2 DRC"` | PIERRE.web_search + PIERRE.search_pubmed | Evidencias + citacoes |
| `/teleconsulta P001` | Comunicacao.schedule + Jitsi JWT | Link de sala + convite |
| `/drnise "o que e diabetes"` | FLOWISE Dr. Nise flow | Resposta educativa LLM |

### 4.3 Alertas Proativos (KESTRA-triggered)

```
KESTRA (06:00 diario) ──► POST WANDA /api/v1/proactive/daily-review
  │
  ├── Para cada paciente ativo:
  │     Oswaldo → risk_score atual
  │     Se score piorou > 10% → AlertaAutomatic0
  │
  ├── Florence → delta_check nos exames das ultimas 24h
  │     Se flag critico → Alerta CRITICAL via Comunicacao
  │
  └── Geralda → tarefas atrasadas no plano de cuidado
        → Lembrete via WhatsApp ao paciente
```

### 4.4 Dr. Nise — Chatbot do Paciente (FLOWISE)

```
Paciente via Portal/WhatsApp: "o que e diabetes?"
  │
  ▼
WANDA.handle_patient_query()
  │
  ├── Classifica: educacional → delega ao FLOWISE Dr. Nise
  │     FLOWISE: RAG em base de conhecimento + Ollama
  │     → Resposta educativa em linguagem simples
  │
  └── Classifica: clinica → envia para agente competente
        Ex: "minha glicemia esta alta" → Oswaldo → alerta profissional
```

---

## 5. Especificacoes Funcionais WANDA V2.0

13 EFs distribuidas em 4 fases de desenvolvimento paralelo:

### Fase 1 — Fundacao (CRITICA — primeiro)
| EF | Titulo | Dependencias |
|----|--------|-------------|
| **EF-W001** | Module Registry V2 (HTTP + MCP) | Nenhuma |
| **EF-W002** | IPS-First (FHIR Patient Summary) | EF-W001 |
| **EF-W003** | LLM Router (Qwen via Ollama) | EF-W001 |
| **EF-W011** | MCP Client Integration (MINERVA + PIERRE) | EF-W001, V5.0.1 pronto |

### Fase 2 — Orquestracao LangGraph
| EF | Titulo | Dependencias |
|----|--------|-------------|
| **EF-W004** | Agregacao Inteligente Multi-Modulo | Fase 1 |
| **EF-W005** | LangGraph Agent Graph | Fase 1 |
| **EF-W006** | Acoes Proativas (KESTRA integration) | Fase 1 |

### Fase 3 — Comunicacao e Alertas
| EF | Titulo | Dependencias |
|----|--------|-------------|
| **EF-W007** | Motor de Alertas (Comunicacao V2) | Fase 1, Comunicacao D1-D2 |
| **EF-W012** | Bot Rocket.Chat Commands Handler | EF-W007, Comunicacao D2 |
| **EF-W013** | Dr. Nise / FLOWISE Integration | Fase 1 |

### Fase 4 — Resiliencia e Observabilidade
| EF | Titulo | Dependencias |
|----|--------|-------------|
| **EF-W008** | Circuit Breaker (graceful degradation) | Fase 1 |
| **EF-W009** | Rastreabilidade (correlation_id E2E) | Fase 1 |
| **EF-W010** | Metricas e Monitoramento (Prometheus) | Todas |

---

## 6. Dependencias Entre Versoes

```
V5.0.1 (DEV1 agora)
  MINERVA :8008 — GET /mcp/tools funcional
  PIERRE :8009  — GET /mcp/tools funcional
        │
        │ Quando /mcp/tools estiver respondendo
        ▼
V5.1.0 DEV-WANDA pode iniciar EF-W011 (MCP Client)
        │
        │ Em paralelo:
        ▼
Comunicacao DEV2 (D1 Engine + D2 Rocket.Chat)
        │
        │ Quando POST /api/v1/routing/send funcionar
        ▼
EF-W007 (Alertas via Comunicacao) pode ser integrado
```

### Ordem de Desenvolvimento Seguro

```
DEV1  ── V5.0.1: MINERVA ──────────────────────────► done
DEV1  ── V5.0.1: PIERRE  ──────────────────────────► done
                                                        │
DEV-WANDA ─── Fase 1 (EF-W001, W002, W003, W011) ──────┘
             │
             │ Paralelo com:
DEV2  ─── Comunicacao D1 + D2 (RC Dispatcher + Bot) ──►
             │
DEV-WANDA ─── Fase 2 (EF-W004, W005, W006)
             │
DEV-WANDA ─── Fase 3 (EF-W007, W012, W013)
             │
DEV-WANDA ─── Fase 4 (EF-W008, W009, W010)
```

**Sem dependencias circulares. WANDA consome — nao e consumida — pelos outros modulos.**

---

## 7. Stack Tecnico WANDA V2.0

| Componente | Tecnologia | Funcao |
|------------|------------|--------|
| Framework | Python 3.11 + FastAPI | API REST |
| Orquestracao | LangGraph 0.2+ | Agent graph, tool calling |
| LLM | Qwen2.5-72B via Ollama | Raciocinio, sintese, routing |
| MCP Client | `mcp` SDK (Anthropic) | Consome MINERVA e PIERRE |
| HTTP Client | httpx (async) | Consome modulos via REST |
| Circuit Breaker | `pybreaker` | Resiliencia |
| Cache | Redis (TTL por tipo de query) | Performance |
| Scheduler Trigger | KESTRA webhook | Acoes proativas |
| Bot Integration | Rocket.Chat REST API | Comandos do @intellicare |
| Chatbot | FLOWISE REST API | Dr. Nise (educacao do paciente) |
| Tracing | OpenTelemetry + Jaeger | Rastreabilidade E2E |
| Metricas | Prometheus + Grafana | Monitoramento |

---

## 8. Portas e Contratos

### Contrato WANDA (producer)
```
GET  /api/v1/health                     # Health check padrao
GET  /api/v1/info                       # Info + capabilities
POST /api/v1/query                      # Query sintetica livre
POST /api/v1/aggregate/patient/{id}     # Agregacao de paciente
POST /api/v1/proactive/daily-review     # Trigger proativo (KESTRA)
POST /api/v1/bot/command                # Comando do bot RC
POST /api/v1/chat/patient               # Chatbot do paciente
GET  /api/v1/metrics                    # Prometheus
```

### Contrato de Entrada (quem chama a WANDA)
| Caller | Endpoint | Caso de uso |
|--------|----------|-------------|
| Bot RC @intellicare | POST /api/v1/bot/command | `/paciente P001` |
| KESTRA | POST /api/v1/proactive/daily-review | Revisao diaria 06:00 |
| Portal Web | POST /api/v1/query | Perguntas do medico no portal |
| Paciente (WhatsApp) | POST /api/v1/chat/patient | Dr. Nise chatbot |

---

## 9. Criterios de Aceitacao V5.1.0

- [ ] 13 EFs implementadas com testes
- [ ] LangGraph agent graph com tools HTTP (6 modulos) + MCP (MINERVA, PIERRE)
- [ ] `/api/v1/aggregate/patient/{id}` consolida dados de todos os modulos em < 5s
- [ ] Bot RC @intellicare responde a 6 comandos clinicos (via EF-W012)
- [ ] Dr. Nise via FLOWISE responde a perguntas educativas em PT-BR
- [ ] KESTRA trigger dispara revisao proativa diaria
- [ ] Circuit Breaker: se modulo cai, WANDA responde gracefully (sem crash)
- [ ] Correlation_id propagado em todos os logs (E2E rastreabilidade)
- [ ] Prometheus exporta metricas por modulo chamado e por tipo de query
- [ ] >= 80 testes (unitarios + integracao)
- [ ] Cobertura >= 80%
- [ ] `docker compose up` standalone (WANDA sobe sem dependencias externas)

---

## 10. Valor Clinico V5.1.0

### Para o Medico
- **Antes**: consulta 6 sistemas separados para entender o caso
- **Depois**: `/paciente P001` no Rocket.Chat → resposta consolidada em 3s

### Para o Gestor
- **Antes**: gera relatorio manualmente, cruzando dados de varios sistemas
- **Depois**: KESTRA dispara relatorio semanal automatico via WANDA → Donabedian → PDF

### Para o Paciente
- **Antes**: liga para a UBS para tirar duvida sobre medicacao
- **Depois**: manda mensagem no WhatsApp → Dr. Nise responde (educacao) ou agenda teleconsulta (clinico)

### Para o Sistema
- **Antes**: alertas criticos chegam com atraso ou perdem-se em filas
- **Depois**: WANDA detecta em tempo real via Redis Stream → alerta imediato via RC + WhatsApp

---

## 11. Entregaveis V5.1.0

| Entregavel | Descricao |
|-----------|-----------|
| 13x ESPECIFICACAO_FUNCIONAL | EF-W001 a EF-W013 (pasta specs/) |
| 13x ESPECIFICACAO_TECNICA | Implementacao detalhada por EF |
| Codigo WANDA V2.0 | Python, LangGraph, MCP Client |
| docker-compose.yml | `docker compose up` standalone |
| Testes | >= 80 testes, >= 80% cobertura |
| Integracao E2E | WANDA + todos os modulos rodando |
| Documentacao | README atualizado, docstrings |

---

## 12. Cronograma Estimado

```
Semana 1-2: DEV-WANDA escreve 13 ETs + Planos de Implementacao
Semana 3-4: Fase 1 — EF-W001, W002, W003, W011 (fundacao + MCP Client)
Semana 5-6: Fase 2 — EF-W004, W005, W006 (LangGraph orquestracao)
Semana 7-8: Fase 3 — EF-W007, W012, W013 (comunicacao + Dr. Nise)
Semana 9:   Fase 4 — EF-W008, W009, W010 (resiliencia + metricas)
Semana 10:  Integracao E2E + Testes completos + Homologacao
```

**Prerequisito:** V5.0.1 (MINERVA + PIERRE) funcional antes da Semana 3.

---

## 13. Glossario V5.1.0

| Termo | Significado |
|-------|------------|
| **MCP Client** | WANDA consome ferramentas MINERVA e PIERRE via MCP |
| **LangGraph** | Framework de grafos de agentes (nodes + edges + state) |
| **Dr. Nise** | Chatbot de educacao do paciente, hospedado no FLOWISE |
| **KESTRA trigger** | KESTRA chama WANDA via webhook para acoes proativas |
| **correlation_id** | UUID gerado na borda, propagado em todas as chamadas |
| **IPS** | International Patient Summary — perfil FHIR do paciente |
| **Circuit Breaker** | Quando modulo cai X vezes → OPEN state → falha rapida sem esperar timeout |
