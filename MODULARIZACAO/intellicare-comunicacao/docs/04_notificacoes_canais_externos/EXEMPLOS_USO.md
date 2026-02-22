# Exemplos de Uso - Canais Externos (D4)

## Visão Geral

Este documento apresenta exemplos práticos de uso dos 4 canais externos de notificação.

---

## 1. Push Notifications

### Inscrever Dispositivo (VAPID)

```bash
curl -X POST http://localhost:8005/api/v1/push/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "device_id": "device-456",
    "provider": "vapid",
    "subscription_data": {
      "endpoint": "https://fcm.googleapis.com/fcm/send/...",
      "keys": {
        "p256dh": "BNcRd...",
        "auth": "tBHI..."
      }
    }
  }'
```

### Enviar Push Notification

```bash
curl -X POST http://localhost:8005/api/v1/push/send \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "title": "Alerta Clínico",
    "body": "Glicemia elevada detectada: 250 mg/dL",
    "data": {
      "patient_id": "12345",
      "alert_type": "high_glucose",
      "severity": "high"
    },
    "provider": "vapid"
  }'
```

### Resposta

```json
{
  "message_id": "push-abc123",
  "status": "sent",
  "provider": "vapid",
  "recipients_count": 1
}
```

---

## 2. WhatsApp Business API

### Enviar Mensagem com Template

```bash
curl -X POST http://localhost:8005/api/v1/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+5511999999999",
    "template_name": "clinical_alert",
    "template_params": {
      "patient_name": "João Silva",
      "alert_type": "Glicemia Elevada",
      "value": "250 mg/dL",
      "action": "Verificar medicação"
    }
  }'
```

### Enviar Mensagem de Texto (dentro de 24h)

```bash
curl -X POST http://localhost:8005/api/v1/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+5511999999999",
    "text": "Olá! Seu resultado de exame está pronto."
  }'
```

### Resposta

```json
{
  "message_id": "wamid.HBgNNTU...",
  "status": "sent",
  "to": "+5511999999999"
}
```

### Webhook (Receber Status)

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "statuses": [{
          "id": "wamid.HBgNNTU...",
          "status": "delivered",
          "timestamp": "1708345200"
        }]
      }
    }]
  }]
}
```

---

## 3. SMS

### Enviar SMS (Twilio)

```bash
curl -X POST http://localhost:8005/api/v1/sms/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+5511999999999",
    "text": "Lembrete: Consulta amanhã às 14h com Dr. Silva",
    "provider": "twilio"
  }'
```

### Enviar SMS com Fallback Automático

```bash
curl -X POST http://localhost:8005/api/v1/sms/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+5511999999999",
    "text": "Seu código de verificação é: 123456"
  }'
```

Se Twilio falhar, tenta Zenvia automaticamente.

### Listar Providers Disponíveis

```bash
curl http://localhost:8005/api/v1/sms/providers
```

Resposta:
```json
{
  "providers": ["twilio", "zenvia"],
  "default_provider": "twilio",
  "fallback_providers": ["twilio", "zenvia"]
}
```

---

## 4. Email

### Enviar Email com Template

```bash
curl -X POST http://localhost:8005/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["paciente@example.com"],
    "subject": "Alerta Clínico - Glicemia Elevada",
    "template_name": "clinical_alert.html",
    "template_data": {
      "severity": "high",
      "title": "Glicemia Elevada Detectada",
      "message": "Sua glicemia está em 250 mg/dL. Por favor, verifique sua medicação.",
      "patient_name": "João Silva",
      "patient_id": "12345",
      "timestamp": "2026-02-19 10:30:00",
      "recommendations": [
        "Verificar dose de insulina",
        "Medir glicemia novamente em 2 horas",
        "Contatar médico se persistir"
      ],
      "action_url": "https://portal.intellicare.com.br/patient/12345/alerts"
    }
  }'
```

### Enviar Email HTML Direto

```bash
curl -X POST http://localhost:8005/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["paciente@example.com"],
    "subject": "Lembrete de Consulta",
    "body_html": "<p>Olá! Lembrete: consulta amanhã às <strong>14h</strong>.</p>"
  }'
```

### Listar Templates Disponíveis

```bash
curl http://localhost:8005/api/v1/email/templates
```

Resposta:
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

### Preview de Template

```bash
curl -X POST http://localhost:8005/api/v1/email/templates/preview \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "clinical_alert.html",
    "template_data": {
      "severity": "high",
      "title": "Teste",
      "message": "Mensagem de teste",
      "patient_name": "João Silva",
      "patient_id": "12345",
      "timestamp": "2026-02-19 10:00:00"
    }
  }'
```

---

## 5. Integração com D1 (Roteamento)

### Enviar Intent com Múltiplos Canais

```bash
curl -X POST http://localhost:8005/api/v1/routing/send \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "alert-12345",
    "intent_type": "clinical_alert",
    "priority": "high",
    "patient_id": "patient-123",
    "channels": ["push", "whatsapp", "sms", "email"],
    "fallback_channels": ["email"],
    "template_id": "clinical_alert",
    "template_data": {
      "severity": "high",
      "title": "Glicemia Elevada",
      "message": "Glicemia: 250 mg/dL",
      "patient_name": "João Silva"
    },
    "metadata": {
      "alert_type": "high_glucose",
      "value": 250
    }
  }'
```

### Fluxo de Roteamento

1. **RuleMatcher** seleciona regra aplicável
2. **RecipientResolver** resolve destinatários (push, whatsapp, sms, email)
3. **LGPDComplianceGateway** verifica preferências e quiet hours
4. **TemplateRenderer** renderiza template para cada canal
5. **DispatcherManager** despacha para cada dispatcher
6. **Dispatchers** enviam via APIs externas
7. **ExternalMessageLog** registra no banco

### Consultar Status

```bash
curl http://localhost:8005/api/v1/routing/intents/alert-12345
```

Resposta:
```json
{
  "intent_id": "alert-12345",
  "status": "completed",
  "channels_sent": ["push", "whatsapp", "email"],
  "channels_failed": ["sms"],
  "timeline": [
    {
      "timestamp": "2026-02-19T10:00:00Z",
      "event": "intent_received"
    },
    {
      "timestamp": "2026-02-19T10:00:01Z",
      "event": "dispatched",
      "channel": "push",
      "status": "sent"
    },
    {
      "timestamp": "2026-02-19T10:00:02Z",
      "event": "dispatched",
      "channel": "whatsapp",
      "status": "sent"
    },
    {
      "timestamp": "2026-02-19T10:00:03Z",
      "event": "dispatched",
      "channel": "sms",
      "status": "failed",
      "error": "Provider unavailable"
    },
    {
      "timestamp": "2026-02-19T10:00:04Z",
      "event": "dispatched",
      "channel": "email",
      "status": "sent"
    }
  ]
}
```

---

## 6. Health Checks

### Verificar Saúde de Todos os Canais

```bash
curl http://localhost:8005/api/v1/channels
```

```bash
curl http://localhost:8005/api/v1/channels/push/health
curl http://localhost:8005/api/v1/channels/whatsapp/health
curl http://localhost:8005/api/v1/channels/sms/health
curl http://localhost:8005/api/v1/channels/email/health
```

---

## Próximos Passos

1. Configure variáveis de ambiente (ver `GUIA_CONFIGURACAO.md`)
2. Teste cada canal individualmente
3. Configure regras de roteamento
4. Monitore métricas no Grafana

