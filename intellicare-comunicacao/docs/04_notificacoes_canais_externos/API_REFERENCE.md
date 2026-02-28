# API Reference - Canais Externos (D4)

## Visão Geral

Referência completa de APIs para os 4 canais externos de notificação do IntelliCare.

**Base URL**: `http://localhost:8005/api/v1`

---

## 1. Push Notifications

### POST /push/subscribe

Inscreve um dispositivo para receber push notifications.

**Request Body**:
```json
{
  "user_id": "string",
  "device_id": "string",
  "provider": "vapid|fcm",
  "subscription_data": {
    "endpoint": "string",
    "keys": {
      "p256dh": "string",
      "auth": "string"
    }
  }
}
```

**Response** (201):
```json
{
  "subscription_id": "uuid",
  "user_id": "string",
  "device_id": "string",
  "provider": "vapid|fcm",
  "created_at": "2026-02-19T10:00:00Z"
}
```

**Errors**:
- `400` - Invalid subscription data
- `409` - Subscription already exists

---

### POST /push/send

Envia push notification para um usuário.

**Request Body**:
```json
{
  "user_id": "string",
  "title": "string",
  "body": "string",
  "data": {
    "key": "value"
  },
  "provider": "vapid|fcm",
  "device_id": "string (optional)"
}
```

**Response** (200):
```json
{
  "message_id": "string",
  "status": "sent|failed",
  "provider": "vapid|fcm",
  "recipients_count": 1,
  "errors": []
}
```

**Errors**:
- `400` - Invalid request
- `404` - User has no subscriptions
- `500` - Provider error

---

### DELETE /push/unsubscribe

Remove inscrição de dispositivo.

**Request Body**:
```json
{
  "user_id": "string",
  "device_id": "string"
}
```

**Response** (200):
```json
{
  "success": true,
  "message": "Subscription removed"
}
```

---

### GET /push/subscriptions/{user_id}

Lista inscrições de um usuário.

**Response** (200):
```json
{
  "user_id": "string",
  "subscriptions": [
    {
      "subscription_id": "uuid",
      "device_id": "string",
      "provider": "vapid|fcm",
      "created_at": "2026-02-19T10:00:00Z"
    }
  ],
  "count": 1
}
```

---

### POST /push/test

Envia notificação de teste.

**Request Body**:
```json
{
  "user_id": "string",
  "device_id": "string (optional)"
}
```

**Response** (200):
```json
{
  "success": true,
  "message_id": "string"
}
```

---

## 2. WhatsApp Business API

### POST /whatsapp/send

Envia mensagem WhatsApp.

**Request Body** (Template):
```json
{
  "to": "+5511999999999",
  "template_name": "clinical_alert",
  "template_params": {
    "patient_name": "João Silva",
    "alert_type": "Glicemia Elevada",
    "value": "250 mg/dL",
    "action": "Verificar medicação"
  }
}
```

**Request Body** (Text - dentro de 24h):
```json
{
  "to": "+5511999999999",
  "text": "Olá! Seu resultado de exame está pronto."
}
```

**Response** (200):
```json
{
  "message_id": "wamid.HBgNNTU...",
  "status": "sent",
  "to": "+5511999999999"
}
```

**Errors**:
- `400` - Invalid phone number or template
- `403` - Template not approved
- `429` - Rate limit exceeded
- `500` - Meta API error

---

### GET /whatsapp/status/{message_id}

Consulta status de mensagem.

**Response** (200):
```json
{
  "message_id": "wamid.HBgNNTU...",
  "status": "sent|delivered|read|failed",
  "timestamp": "2026-02-19T10:00:00Z",
  "error": null
}
```

---

### POST /whatsapp/webhook

Webhook para receber eventos da Meta (configurado automaticamente).

**Request Body** (Meta):
```json
{
  "object": "whatsapp_business_account",
  "entry": [...]
}
```

**Response** (200):
```json
{
  "success": true
}
```

---

### GET /whatsapp/webhook

Verificação de webhook pela Meta.

**Query Params**:
- `hub.mode=subscribe`
- `hub.verify_token=<token>`
- `hub.challenge=<challenge>`

**Response** (200):
```
<challenge>
```

---

### GET /whatsapp/templates

Lista templates disponíveis.

**Response** (200):
```json
{
  "templates": [
    {
      "name": "clinical_alert",
      "language": "pt_BR",
      "status": "approved",
      "params": ["patient_name", "alert_type", "value", "action"]
    }
  ],
  "count": 5
}
```

---

## 3. SMS

### POST /sms/send

Envia SMS.

**Request Body**:
```json
{
  "to": "+5511999999999",
  "text": "Lembrete: Consulta amanhã às 14h com Dr. Silva",
  "provider": "twilio|zenvia|sns (optional)"
}
```

**Response** (200):
```json
{
  "message_id": "SM123...",
  "status": "sent|queued",
  "provider": "twilio",
  "to": "+5511999999999"
}
```

**Errors**:
- `400` - Invalid phone number or text
- `413` - Message too long (>160 chars)
- `500` - Provider error (tries fallback)

---

### GET /sms/status/{message_id}

Consulta status de SMS.

**Response** (200):
```json
{
  "message_id": "SM123...",
  "status": "sent|delivered|failed",
  "provider": "twilio",
  "timestamp": "2026-02-19T10:00:00Z",
  "error": null
}
```

---

### GET /sms/providers

Lista providers disponíveis.

**Response** (200):
```json
{
  "providers": ["twilio", "zenvia"],
  "default_provider": "twilio",
  "fallback_providers": ["twilio", "zenvia"]
}
```

---

## 4. Email

### POST /email/send

Envia email.

**Request Body** (Template):
```json
{
  "to": ["paciente@example.com"],
  "subject": "Alerta Clínico - Glicemia Elevada",
  "template_name": "clinical_alert.html",
  "template_data": {
    "severity": "high",
    "title": "Glicemia Elevada Detectada",
    "message": "Sua glicemia está em 250 mg/dL.",
    "patient_name": "João Silva"
  }
}
```

**Request Body** (HTML direto):
```json
{
  "to": ["paciente@example.com"],
  "subject": "Lembrete de Consulta",
  "body_html": "<p>Olá! Lembrete: consulta amanhã às <strong>14h</strong>.</p>",
  "body_text": "Olá! Lembrete: consulta amanhã às 14h."
}
```

**Response** (200):
```json
{
  "message_id": "<abc123@intellicare>",
  "status": "sent",
  "recipients": ["paciente@example.com"],
  "count": 1
}
```

**Errors**:
- `400` - Invalid email or template
- `413` - Attachment too large
- `500` - SMTP error

---

### GET /email/templates

Lista templates disponíveis.

**Response** (200):
```json
{
  "templates": [
    "base.html",
    "clinical_alert.html",
    "daily_report.html",
    "teleconsult_confirmation.html"
  ],
  "count": 4
}
```

---

### POST /email/templates/preview

Preview de template renderizado.

**Request Body**:
```json
{
  "template_name": "clinical_alert.html",
  "template_data": {
    "severity": "high",
    "title": "Teste",
    "message": "Mensagem de teste"
  }
}
```

**Response** (200):
```json
{
  "html": "<html>...</html>",
  "text": "Texto plano..."
}
```

---

## 5. Channels (Geral)

### GET /channels

Lista canais disponíveis.

**Response** (200):
```json
{
  "channels": ["rocketchat", "jitsi", "push", "whatsapp", "sms", "email"],
  "count": 6
}
```

---

### GET /channels/{channel}/health

Verifica saúde de um canal.

**Response** (200):
```json
{
  "channel": "push",
  "healthy": true,
  "latency_ms": 45,
  "last_check": "2026-02-19T10:00:00Z",
  "details": {
    "vapid_enabled": true,
    "fcm_enabled": true
  }
}
```

---

### POST /channels/{channel}/test

Testa canal com mensagem de teste.

**Request Body**:
```json
{
  "recipient": "test@example.com"
}
```

**Response** (200):
```json
{
  "success": true,
  "message_id": "test-123",
  "latency_ms": 120
}
```

---

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Bad Request - Dados inválidos |
| 401 | Unauthorized - Token inválido |
| 403 | Forbidden - Sem permissão |
| 404 | Not Found - Recurso não encontrado |
| 409 | Conflict - Recurso já existe |
| 413 | Payload Too Large - Mensagem muito grande |
| 429 | Too Many Requests - Rate limit |
| 500 | Internal Server Error - Erro do servidor |
| 502 | Bad Gateway - Erro do provider externo |
| 503 | Service Unavailable - Serviço indisponível |

---

## Rate Limits

| Canal | Limite |
|-------|--------|
| Push | 1000/min por usuário |
| WhatsApp | 80/min por número (Meta) |
| SMS | 100/min (Twilio) |
| Email | 50/min (SMTP) |

---

## Autenticação

Todos os endpoints requerem autenticação via JWT Keycloak:

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8005/api/v1/push/send
```

---

## Próximos Passos

1. Configure variáveis de ambiente (ver `GUIA_CONFIGURACAO.md`)
2. Teste endpoints com Postman/curl
3. Integre com D1 para roteamento automático
4. Monitore métricas no Grafana

