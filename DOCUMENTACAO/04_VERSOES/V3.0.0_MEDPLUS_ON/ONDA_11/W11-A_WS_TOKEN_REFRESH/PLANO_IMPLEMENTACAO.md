# W11-A — WS Token Refresh — Plano de Implementação

**Workstream:** W11-A
**Estimativa:** 5 dias
**Responsável:** DEV1 (execução DEV2 em 2026-02-25)
**Status Atual:** ✅ Concluído

---

## Ordem de Execução

| # | Task | Dias | Depende |
|---|------|------|---------|
| 1 | Handler token-refresh (parse + validate) | 2 | — |
| 2 | Atualizar connection context com novo token | 1 | 1 |
| 3 | Background check de expiração + refresh-required | 1 | 1 |
| 4 | Fechar conexão quando expirado sem refresh | 0.5 | 1 |
| 5 | Testes + documentação | 0.5 | 1-4 |

---

## Passo a Passo

### Passo 1: Handler token-refresh
- No WebSocket message handler: detectar type=token-refresh
- Extrair token do payload
- Validar JWT (assinatura, exp, issuer)
- Retornar token-refresh-ack

### Passo 2: Atualizar context
- connection_context["token"] = novo_token
- connection_context["token_exp"] = exp claim
- Garantir que subscriptions usem token atualizado para autorização

### Passo 3: refresh-required
- Task periódica (ou on-message): verificar exp do token
- Se expires_in < 300: emitir refresh-required
- Cliente responsável por obter novo token (refresh grant)

### Passo 4: Fechar conexão expirada
- Ao processar mensagem ou evento: verificar se token expirou
- Se expirado e sem refresh recente: close(4001, "Token expired")

### Passo 5: Testes
- test_token_refresh_success
- test_token_refresh_expired
- test_refresh_required_emitted
- test_connection_closed_when_expired

---

## Checklist de Entrega

- [x] Mensagem token-refresh tratada
- [x] token-refresh-ack enviado
- [x] refresh-required emitido antes de expirar
- [x] Conexão fechada quando token expira
- [x] Rate limit
- [x] Testes passando

---

## Evidências de Execução (2026-02-25)

### Implementação
- Implementação feita no WebSocket real de subscriptions do módulo de comunicação:
  - `intellicare-comunicacao/comunicacao/subscriptions/ws_handler.py`
- Ajustes entregues:
  - suporte a query `token` na conexão WS
  - mensagem de entrada `token-refresh`
  - resposta `token-refresh-ack` (success true/false + erro)
  - emissão de `refresh-required` com `expires_in`
  - encerramento com `close(4001, \"Token expired\")`
  - rate limit de refresh por conexão

### Configurações
- `WS_REFRESH_REQUIRED_THRESHOLD` (default: 300s)
- `WS_TOKEN_REFRESH_RATE_LIMIT` (default: 60s)
- `WS_TOKEN_ISSUER` (opcional para validação de issuer)

### Testes
- Arquivo: `intellicare-comunicacao/tests/test_ws_token_refresh.py`
- Comando:
  - `pytest -q -o addopts=\"\" tests/test_ws_token_refresh.py`
- Resultado:
  - `4 passed`
