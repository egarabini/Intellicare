# W9-A — AI Operation + SSE — Especificação Funcional

**Workstream:** W9-A
**Responsável:** DEV2
**Módulo:** `intellicare-grahame` + `intellicare-wanda`
**Status:** 📋 Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Expor operação AI padronizada via endpoint FHIR com **streaming SSE** (Server-Sent Events), permitindo respostas longas em tempo real sem bloquear o cliente. Reutiliza Florence/Geralda como backend.

---

## 2. Contexto de Negócio

### Problema Atual
- Agentes Florence/Geralda respondem via APIs internas
- Sem endpoint padronizado FHIR para IA
- Respostas longas bloqueiam o cliente (timeout, UX ruim)

### Solução Proposta
- Endpoint `POST /fhir/$ai` ou `POST /ai` com streaming SSE
- Cliente recebe tokens/chunks em tempo real
- Fallback para resposta completa se cliente não suportar SSE

### Benefícios
- **UX superior** — usuário vê resposta sendo escrita
- **Padronização** — operação AI documentada como FHIR
- **Compatibilidade** — Medplum suporta desde v5.0.11+

---

## 3. Requisitos Funcionais

### RF-001 — Endpoint AI Operation
- **Endpoint:** `POST /fhir/$ai` ou `POST /ai`
- **Payload:** `{ "prompt": string, "context": object?, "agent": "florence"|"geralda" }`
- **Resposta:** JSON ou SSE stream

### RF-002 — Streaming SSE
- **Content-Type:** `text/event-stream`
- **Eventos:** `chunk` (texto), `done` (fim), `error` (erro)
- **Formato:** `data: {chunk}\n\n`
- **Timeout:** Configurável (default 120s)

### RF-003 — Seleção de Agente
- **florence:** Interpretação de exames, laudos
- **geralda:** Plano de cuidado, orientações
- **Default:** Florence se não especificado

### RF-004 — Contexto
- Aceitar `context` (Patient, Observation, etc.) para enriquecer prompt
- Referências FHIR resolvidas antes de enviar ao agente

### RF-005 — Fallback
- Se `Accept: text/event-stream` não presente → resposta JSON completa
- Se timeout → retornar parcial + status 206

### RF-006 — Cancelamento
- Cliente pode fechar conexão para cancelar
- Servidor deve interromper processamento

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Performance
- Primeiro chunk: < 2s
- Throughput: 50+ tokens/s

### RNF-002 — Segurança
- Autenticação obrigatória
- Rate limit por usuário (ex: 10 req/min)

### RNF-003 — Auditoria
- Log de todas as operações AI (prompt, agent, user_id)

---

## 5. Cenários de Teste

| # | Cenário | Entrada | Saída Esperada |
|---|---------|---------|----------------|
| 1 | Streaming SSE | POST /ai, Accept: text/event-stream | Chunks em tempo real |
| 2 | Resposta JSON | POST /ai, Accept: application/json | JSON completo |
| 3 | Agente Florence | agent: "florence" | Resposta interpretativa |
| 4 | Agente Geralda | agent: "geralda" | Resposta de cuidado |
| 5 | Cancelamento | Fechar conexão durante stream | Processamento interrompido |

---

## 6. Referências

- Medplum AI Operation v5.0.11+
- SSE: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- FHIR Operations: https://www.hl7.org/fhir/operations.html
