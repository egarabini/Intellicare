# WANDA — Especificacoes Funcionais
**Data:** 2026-03-04
**Versao:** 3.0.0
**Modulo:** intellicare-wanda (porta 8004)
**Papel:** Orquestrador central de IA — cerebro do IntelliCare

---

## 1. Proposito

A WANDA e o orquestrador central de inteligencia artificial do IntelliCare.
Ela recebe requisicoes do portal e dos modulos, interpreta a intencao clinica,
roteia para os agentes especializados certos e agrega as respostas em uma
resposta coesa e util para o profissional de saude.

WANDA e o unico ponto de contato com o LLM para o usuario final.

---

## 2. Funcionalidades Implementadas

### 2.1 Registro e Descoberta de Modulos (v2.0)
- Registry de todos os modulos ativos com health check
- Descoberta automatica de modulos via service discovery
- Circuit breaker para modulos indisponiveis

### 2.2 IPS-First (v2.0)
- International Patient Summary (IPS) como contexto primario
- Gera resumo de paciente buscando dados de GRAHAME + GERALDA
- Injeta contexto IPS em todas as analises

### 2.3 MCP Client (v2.0)
- Cliente MCP para MINERVA (extracao de documentos)
- Cliente MCP para PIERRE (busca cientifica)
- Integrar ferramentas MCP como tools do LangGraph

### 2.4 LangGraph Workflows (v3.0)
- Grafo de workflows para processar requisicoes complexas
- Nos: intent_detector, context_builder, tool_selector, aggregator, responder
- LLM (Ollama) para deteccao de intencao e geracao de resposta

### 2.5 AlertHub (v3.0)
- Hub central de alertas clinicos
- Recebe alertas de todos os modulos via Redis Streams
- Roteia alertas para COMUNICACAO baseado em urgencia e preferencias

---

## 3. Funcionalidades da Versao 3.0 (finalizar)

### 3.1 LLM Intent Routing
- Classificar intencao da query: pesquisa, analise_paciente, alerta, protocolo, dados
- Rotear para subgrafos especializados no LangGraph
- Ex: "qual protocolo para DRC?" -> subgrafo PIERRE
- Ex: "resuma o historico do paciente 123" -> subgrafo IPS+GRAHAME

### 3.2 Aggregation Inteligente
- Coletar respostas de multiplos modulos em paralelo
- Usar LLM para agregar em resposta coesa
- Incluir fontes e nivel de confianca

### 3.3 AlertHub Completo
- Categorias: critico, urgente, rotina, informativo
- Regras de escalada por categoria
- Dashboard de alertas para gestores (via portal)
- Integracao com Rocket.Chat para alertas de equipe

### 3.4 Tracing e Metricas
- Tracing distribuido (OpenTelemetry) para cada requisicao
- Metricas por modulo invocado (latencia, taxa de erro)
- Dashboard Grafana com heat map de uso

---

## 4. Casos de Uso Principais

### UC-01: Consulta Clinica Complexa
**Ator:** Medico
**Query:** "Paciente 456 tem DRC e DM2. Qual o manejo ideal?"
**Fluxo:** Intent -> analise_paciente + protocolo | WANDA busca IPS (GRAHAME+GERALDA) em paralelo com diretrizes (PIERRE) | Agrega: contexto do paciente + evidencia clinica | Resposta estruturada

### UC-02: Alerta de Valor Critico
**Ator:** GRAHAME (CDS Hook trigger)
**Fluxo:** Creatinina > 10 -> CDS Hook dispara -> WANDA AlertHub recebe -> Categoriza como critico -> COMUNICACAO envia RC urgente para medico + SMS para paciente

### UC-03: Upload de Exame
**Ator:** Profissional via portal
**Fluxo:** Upload PDF -> WANDA detecta documento -> Invoca MINERVA (MCP) -> MINERVA extrai resultados -> WANDA cria FHIR Observations via GRAHAME -> Atualiza plano GERALDA se necessario

---

## 5. Criterios de Aceite (v3.0)

- [ ] Health check responde 200
- [ ] Query clinica retorna resposta com evidencia (PIERRE) + contexto (GRAHAME)
- [ ] Upload de documento extrai resultados (MINERVA MCP)
- [ ] Alerta critico e roteado para COMUNICACAO em < 5s
- [ ] LangGraph grafo funcional com pelo menos 3 nos
- [ ] Cobertura de testes >= 70%
- [ ] Tracing OpenTelemetry ativo

---

*WANDA v3.0 — Especificacoes Funcionais — 2026-03-04*
