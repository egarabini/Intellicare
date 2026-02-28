# W11-A — WS Token Refresh — Especificação Técnica

**Workstream:** W11-A
**Módulo:** `intellicare-grahame` (WebSocket)
**Data:** 2026-02-24

---

## 1. Arquitetura

```
Cliente WebSocket
    │
    │ { "type": "token-refresh", "token": "Bearer xxx" }
    ▼
┌─────────────────────────────────────────────────────────────┐
│  WebSocket Handler                                           │
│  - Parse mensagem type=token-refresh                          │
│  - Validar token (JWT verify)                                 │
│  - Atualizar connection_context.token                        │
│  - Emitir token-refresh-ack                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Contrato de Mensagens

### Cliente -> Servidor (token-refresh)

```json
{
  "type": "token-refresh",
  "token": "Bearer eyJhbGciOiJIUzI1NiIs..."
}
```

### Servidor -> Cliente (token-refresh-ack)

```json
{
  "type": "token-refresh-ack",
  "success": true
}
```

### Servidor -> Cliente (refresh-required)

```json
{
  "type": "refresh-required",
  "expires_in": 300
}
```

### Servidor -> Cliente (erro)

```json
{
  "type": "token-refresh-ack",
  "success": false,
  "error": "Token expired"
}
```

---

## 3. Fluxo

1. Conexão WebSocket estabelecida com token inicial
2. Background job verifica expiração (ex: a cada 1 min)
3. Se expires_in < 300s: emitir refresh-required
4. Cliente envia token-refresh
5. Servidor valida, atualiza contexto, emite ack
6. Se token expira sem refresh: fechar com code 4001

---

## 4. Estrutura de Código

```
intellicare-grahame/
├── grahame/
│   ├── websocket/
│   │   ├── handler.py          # Modificar: tratar token-refresh
│   │   └── token_refresh.py    # NOVO — validação e atualização
```

---

## 5. Variáveis de Ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| WS_REFRESH_REQUIRED_THRESHOLD | 300 | Emitir refresh-required quando faltar N segundos |
| WS_TOKEN_REFRESH_RATE_LIMIT | 60 | Segundos entre refreshes permitidos |
