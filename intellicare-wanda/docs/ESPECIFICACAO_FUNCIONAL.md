# intellicare-wanda — Especificacao Funcional

> Homenagem a Wanda de Aguiar Horta, enfermeira brasileira pioneira na sistematizacao da assistencia de enfermagem.

## 1. Proposito

O intellicare-wanda e a **orquestradora inteligente** do ecossistema IntelliCare. Ela coordena modulos especializados, roteia consultas para o agente adequado, agrega respostas e garante seguranca clinica. Wanda so faz sentido quando 2 ou mais modulos estao ativos.

## 2. Valor de Negocio

- Integracao transparente entre modulos sem acoplamento
- Raciocinio multi-dominio (clinica + gestao + territorio)
- Seguranca clinica pela regra IPS-First
- Resposta consolidada e rastreavel

## 3. Funcionalidades

### 3.1 Orquestracao via LangGraph
- Grafo de supervisor-worker
- Routing inteligente baseado na intencao da consulta
- Agregacao de respostas de multiplos agentes
- Recursao controlada (max depth configurável)

### 3.2 Descoberta Dinamica de Modulos
- Consulta /api/v1/info de cada modulo registrado
- Routing baseado em capabilities declaradas
- Adaptacao automatica quando modulos sao adicionados/removidos

### 3.3 Regra IPS-First
- Sempre carrega o IPS do paciente antes de qualquer analise
- Garante que o contexto clinico completo esta disponivel
- Previne analises sem contexto

### 3.4 Safety Rules
- Nunca fabrica dados clinicos
- Validacao de interacoes medicamentosas
- Operacoes read-only em dominio sensivel
- Logs auditaveis de decisoes

### 3.5 Integracao com MCP
- Ponte para FHIR Server via MCP
- Ponte para RNDS via MCP
- Ponte para Careplanner via MCP

## 4. Quando Usar

| Cenario | Wanda Necessaria? |
|---------|:---:|
| So Oswaldo rodando | Nao |
| Oswaldo + Florence | Sim — coordena analises |
| Qualquer 2+ modulos | Sim |
| Portal com 1 modulo | Nao — portal chama direto |

## 5. Origem do Codigo

- `agentes/wanda/graph/` — main_graph, supervisor, aggregator
- `agentes/wanda/adapters/` — mcp_adapter (20k+ linhas)
- `agentes/wanda/rules/` — safety_rules
- `agentes/wanda/prompts/` — system_prompt
- `agentes/wanda/subagents/` — base, patient_iq, careplanner, zilda
- `agentes/wanda/tests/` — 11 arquivos de teste

## 6. Adaptacao para LEGO

A principal mudanca: Wanda NAO importa agentes diretamente. Em vez disso:
- Descobre modulos ativos via HTTP (/api/v1/info)
- Chama agentes via suas APIs REST (/api/v1/analyze)
- Usa capabilities declaradas para routing

Isso desacopla Wanda dos agentes — adicionar um novo agente nao requer mudanca na Wanda.
