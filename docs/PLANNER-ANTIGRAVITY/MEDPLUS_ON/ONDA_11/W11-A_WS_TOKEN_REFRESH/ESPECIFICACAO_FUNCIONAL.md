# W11-A — WS Token Refresh — Especificação Funcional

**Workstream:** W11-A
**Responsável:** DEV1
**Módulo:** `intellicare-grahame` (WebSocket)
**Status:** Especificação
**Data:** 2026-02-24

---

## 1. Objetivo

Permitir renovação de token em conexões WebSocket longas, evitando desconexão quando o token expira (ex: sessões de médicos em plantão de 12h).

---

## 2. Contexto de Negócio

### Problema Atual
- Token JWT expira (ex: 1h)
- WebSocket mantém conexão por horas
- Ao expirar: subscriptions param de receber eventos ou conexão cai

### Solução Proposta
- Cliente envia mensagem `token-refresh` com novo token
- Servidor valida e atualiza contexto da conexão
- Ou: servidor emite evento solicitando refresh antes de expirar

### Benefícios
- Sessões longas estáveis
- Sem reconexão manual
- Alinhado a Medplum v5.0.15+

---

## 3. Requisitos Funcionais

### RF-001 — Mensagem token-refresh
- Cliente envia `{ "type": "token-refresh", "token": "Bearer xxx" }` no WebSocket
- Servidor valida token e atualiza contexto da conexão
- Resposta: `{ "type": "token-refresh-ack", "success": true }` ou erro

### RF-002 — Evento refresh-required
- Servidor emite `{ "type": "refresh-required", "expires_in": 300 }` quando token expira em menos de 5 min
- Cliente deve enviar token-refresh antes de expirar

### RF-003 — Rejeição de conexão expirada
- Se token expirado e sem refresh: fechar conexão com código 4001 (token expired)
- Cliente pode reconectar com novo token

### RF-004 — Auditoria
- Log de refresh bem-sucedido
- Log de tentativa com token inválido

---

## 4. Requisitos Não-Funcionais

### RNF-001 — Segurança
- Validar assinatura e claims do novo token
- Não aceitar token expirado
- Rate limit: 1 refresh a cada 60s por conexão

---

## 5. Cenários de Teste

| # | Cenário | Entrada | Saída Esperada |
|---|---------|---------|----------------|
| 1 | token-refresh válido | token-refresh com token novo | success |
| 2 | token-refresh expirado | token-refresh com token expirado | error, conexão mantida |
| 3 | refresh-required | token próximo de expirar | evento emitido |
| 4 | Sem refresh após expirar | token expira | conexão fechada 4001 |
