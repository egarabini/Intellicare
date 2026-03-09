# W9-A — AI Operation + SSE — Especificação Técnica

**Workstream:** W9-A
**Módulo:** `intellicare-grahame` + `intellicare-wanda`
**Data:** 2026-02-24

---

## 1. Arquitetura

```
Cliente (Portal/App)
    │
    │ POST /fhir/$ai
    │ Accept: text/event-stream
    │ Body: { prompt, agent, context }
    ▼
┌─────────────────────────────────────────────────┐
│  Grahame API (FastAPI)                          │
│  POST /fhir/$ai  ou  POST /ai                   │
│  - Valida payload                                │
│  - Resolve context (FHIR refs)                   │
│  - Chama Wanda/Florence/Geralda                  │
└─────────────────────────────────────────────────┘
    │
    │ HTTP async
    ▼
┌─────────────────────────────────────────────────┐
│  Wanda / Florence / Geralda                      │
│  - Gera resposta (streaming ou completa)        │
│  - Retorna AsyncGenerator[str] ou str           │
└─────────────────────────────────────────────────┘
    │
    │ SSE: data: {chunk}\n\n
    ▼
Cliente recebe chunks em tempo real
```

---

## 2. Contrato API

### Request

```http
POST /fhir/$ai HTTP/1.1
Accept: text/event-stream
Content-Type: application/json
Authorization: Bearer {token}

{
  "prompt": "Interprete este resultado de glicemia",
  "agent": "florence",
  "context": {
    "observation": "Observation/123",
    "patient": "Patient/456"
  }
}
```

### Response (SSE)

```
event: chunk
data: { "text": "O resultado indica " }

event: chunk
data: { "text": "glicemia de jejum elevada." }

event: done
data: { "full_text": "...", "tokens_used": 150 }
```

### Response (JSON fallback)

```json
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "result", "valueString": "Resposta completa..." }
  ]
}
```

---

## 3. Estrutura de Código

```
intellicare-grahame/
├── grahame/
│   ├── api/
│   │   ├── ai_routes.py       # NOVO — POST /ai, POST /fhir/$ai
│   │   └── sse_utils.py       # NOVO — helpers SSE
│   └── services/
│       └── ai_operation_service.py  # NOVO — orquestra chamada
```

---

## 4. Dependências

- `sse-starlette` ou `aiostream` para SSE
- `httpx` para chamar Wanda/Florence/Geralda
- `intellicare-wanda` API para streaming

---

## 5. Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `AI_OPERATION_TIMEOUT` | 120 | Timeout em segundos |
| `AI_OPERATION_RATE_LIMIT` | 10 | Reqs/min por usuário |
| `WANDA_AI_URL` | http://wanda:8000 | URL do Wanda |

---

## 6. Testes

- Unit: `ai_operation_service` com mock
- Integration: `POST /ai` com streaming SSE
- E2E: Cliente recebe chunks em ordem
