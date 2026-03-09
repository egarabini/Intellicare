# ONDA_11 — Entrega

**Data:** 2026-02-25
**Status:** Implementado

---

## Resumo

A ONDA_11 (Refinamentos) foi implementada:

| Workstream | Status | Local |
|------------|--------|-------|
| W11-A WS Token Refresh | OK | intellicare-comunicacao/ws_handler.py |
| W11-B CodeSystem/$validate-code | OK | terminology_routes (já existia) |
| W11-C Display language (i18n) | OK | display_resolver, accept_language (já existia) |

---

## W11-A — WS Token Refresh

- **Arquivo:** `comunicacao/subscriptions/ws_handler.py`
- **Alteração:** Task `_receive_client_messages` que escuta mensagens do cliente
- **Protocolo:** Cliente envia `{"type": "token-refresh", "token": "Bearer ..."}` → servidor responde `{"type": "token-refresh-ack", "success": true}`

---

## W11-B — CodeSystem/$validate-code

- **Já implementado** em `terminology_routes.py`
- Endpoints: `GET /CodeSystem/$validate-code`, `POST /fhir/CodeSystem/$validate-code`

---

## W11-C — Display language (i18n)

- **Já implementado:** `display_resolver`, `parse_accept_language`
- Operações $lookup, $expand, $translate respeitam `Accept-Language`
