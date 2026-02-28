# W9-A — AI Operation + SSE — Plano de Implementação

**Workstream:** W9-A
**Estimativa:** 14 dias
**Responsável:** DEV2

---

## Ordem de Execução

| # | Task | Dias | Depende |
|---|------|------|---------|
| 1 | Criar `ai_operation_service` (orquestra Wanda) | 2 | — |
| 2 | Implementar streaming no Wanda/Florence (se não existir) | 3 | — |
| 3 | Criar `ai_routes.py` com POST /ai | 2 | 1 |
| 4 | Implementar SSE response (sse-starlette) | 2 | 1, 3 |
| 5 | Implementar fallback JSON | 1 | 3 |
| 6 | Resolver context (FHIR refs) | 2 | 1 |
| 7 | Rate limit + auditoria | 1 | 3 |
| 8 | Testes unitários + integração | 1 | 1-7 |

---

## Passo a Passo

### Passo 1: ai_operation_service
- Criar `grahame/services/ai_operation_service.py`
- Método `stream_ai(prompt, agent, context) -> AsyncGenerator[str]`
- Chamar Wanda/Florence/Geralda
- Tratar timeout e cancelamento

### Passo 2: Streaming no Wanda
- Verificar se Wanda já retorna streaming
- Se não: adicionar endpoint streaming em Wanda
- Retornar `AsyncGenerator[str]` de chunks

### Passo 3: ai_routes.py
- `POST /ai` e `POST /fhir/$ai`
- Validar payload (Pydantic)
- Chamar `ai_operation_service` stream

### Passo 4: SSE Response
- Usar `StreamingResponse` com `text/event-stream`
- Formato: `event: chunk\ndata: {json}\n\n`
- Evento `done` ao finalizar

### Passo 5: Fallback JSON
- Se `Accept: text/event-stream` ausente → acumular chunks e retornar JSON

### Passo 6: Context Resolution
- Resolver referências FHIR (Observation/123, Patient/456)
- Incluir dados no contexto enviado ao agente

### Passo 7: Rate Limit + Auditoria
- Rate limit por user_id (Redis ou in-memory)
- Log de todas as operações AI

### Passo 8: Testes
- `test_ai_operation_service` (mock Wanda)
- `test_ai_routes_sse` (TestClient)
- `test_ai_routes_json_fallback`

---

## Checklist de Entrega

- [ ] POST /ai com SSE funcional
- [ ] Fallback JSON funcional
- [ ] Agentes Florence e Geralda suportados
- [ ] Context resolution
- [ ] Rate limit
- [ ] Auditoria
- [ ] Testes passando
