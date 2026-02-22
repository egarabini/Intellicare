# Guia de Configuração - Canais Externos (D4)

## Visão Geral

Este guia descreve como configurar os 4 canais externos de notificação do IntelliCare:

1. **Push Notifications** (VAPID/FCM)
2. **WhatsApp Business API** (Meta Graph API)
3. **SMS** (Twilio/Zenvia/SNS)
4. **Email** (SMTP)

---

## 1. Push Notifications (D4.2)

### Variáveis de Ambiente

```bash
# VAPID (Web Push - RFC 8292)
VAPID_PUBLIC_KEY=<chave_publica_vapid>
VAPID_PRIVATE_KEY=<chave_privada_vapid>
VAPID_SUBJECT=mailto:admin@intellicare.com.br
VAPID_ENABLED=true

# FCM (Firebase Cloud Messaging)
FCM_PROJECT_ID=<projeto_firebase>
FCM_CREDENTIALS_PATH=/path/to/firebase-credentials.json
FCM_ENABLED=true

# Geral
PUSH_ENABLED=true
PUSH_DEFAULT_PROVIDER=vapid  # ou "fcm"
```

### Geração de Chaves VAPID

```bash
# Instalar py-vapid
pip install py-vapid

# Gerar chaves
vapid --gen

# Saída:
# Public Key: <chave_publica>
# Private Key: <chave_privada>
```

### Configuração FCM

1. Acesse [Firebase Console](https://console.firebase.google.com/)
2. Crie um projeto ou use existente
3. Vá em **Project Settings** → **Service Accounts**
4. Clique em **Generate New Private Key**
5. Salve o arquivo JSON e configure `FCM_CREDENTIALS_PATH`

---

## 2. WhatsApp Business API (D4.3)

### Variáveis de Ambiente

```bash
# Meta Graph API v18.0
WHATSAPP_ACCESS_TOKEN=<token_acesso_meta>
WHATSAPP_PHONE_NUMBER_ID=<id_numero_whatsapp>
WHATSAPP_BUSINESS_ACCOUNT_ID=<id_conta_business>
WHATSAPP_WEBHOOK_VERIFY_TOKEN=<token_verificacao_webhook>
WHATSAPP_ENABLED=true

# Geral
WHATSAPP_API_VERSION=v18.0
WHATSAPP_TIMEOUT=30
```

### Configuração Meta Business

1. Acesse [Meta for Developers](https://developers.facebook.com/)
2. Crie um app ou use existente
3. Adicione produto **WhatsApp Business Platform**
4. Configure número de telefone
5. Gere token de acesso permanente
6. Configure webhook (URL: `https://seu-dominio/api/v1/whatsapp/webhook`)

### Templates Pré-aprovados

Os seguintes templates estão disponíveis (devem ser aprovados pela Meta):

- `clinical_alert` - Alertas clínicos
- `medication_reminder` - Lembretes de medicação
- `teleconsult_invite` - Convites para teleconsulta
- `appointment_confirmation` - Confirmação de consulta
- `lab_results_ready` - Resultados de exames prontos

---

## 3. SMS (D4.4)

### Variáveis de Ambiente

```bash
# Twilio (Provider principal)
TWILIO_ACCOUNT_SID=<account_sid>
TWILIO_AUTH_TOKEN=<auth_token>
TWILIO_FROM_NUMBER=+15551234567
TWILIO_ENABLED=true

# Zenvia (Provider fallback)
ZENVIA_API_TOKEN=<api_token>
ZENVIA_FROM_NAME=IntelliCare
ZENVIA_ENABLED=true

# Amazon SNS (Provider opcional)
AWS_ACCESS_KEY_ID=<access_key>
AWS_SECRET_ACCESS_KEY=<secret_key>
AWS_REGION=us-east-1
SNS_ENABLED=false

# Geral
SMS_ENABLED=true
SMS_DEFAULT_PROVIDER=twilio
SMS_FALLBACK_PROVIDERS=twilio,zenvia
SMS_MAX_MESSAGE_LENGTH=160
```

### Configuração Twilio

1. Acesse [Twilio Console](https://console.twilio.com/)
2. Crie conta ou faça login
3. Vá em **Account** → **API Keys & Tokens**
4. Copie **Account SID** e **Auth Token**
5. Compre número de telefone em **Phone Numbers**

### Configuração Zenvia

1. Acesse [Zenvia Console](https://app.zenvia.com/)
2. Crie conta ou faça login
3. Vá em **API** → **Tokens**
4. Gere novo token de API
5. Configure nome do remetente

---

## 4. Email (D4.5)

### Variáveis de Ambiente

```bash
# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@intellicare.com.br
SMTP_PASSWORD=<senha_app>
SMTP_FROM_EMAIL=noreply@intellicare.com.br
SMTP_FROM_NAME=IntelliCare
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT=30
SMTP_ENABLED=true

# Templates
EMAIL_TEMPLATES_DIR=comunicacao/templates/email
EMAIL_ENABLED=true
EMAIL_MAX_RECIPIENTS=50
EMAIL_MAX_ATTACHMENT_SIZE_MB=10
```

### Configuração Gmail SMTP

1. Acesse [Google Account](https://myaccount.google.com/)
2. Vá em **Security** → **2-Step Verification**
3. Role até **App passwords**
4. Gere senha de app para "Mail"
5. Use a senha gerada em `SMTP_PASSWORD`

### Templates Disponíveis

- `clinical_alert.html` - Alertas clínicos
- `teleconsult_confirmation.html` - Confirmação de teleconsulta
- `daily_report.html` - Relatório diário
- `base.html` - Template base (herança)

---

## Integração com D1 (Engine de Roteamento)

Todos os dispatchers são registrados automaticamente no `DispatcherManager` durante o startup da aplicação.

### Verificar Dispatchers Registrados

```bash
curl http://localhost:8005/api/v1/channels
```

Resposta esperada:
```json
{
  "channels": ["rocketchat", "jitsi", "push", "whatsapp", "sms", "email"],
  "count": 6
}
```

### Health Check de Canais

```bash
# Verificar saúde de todos os canais
curl http://localhost:8005/api/v1/channels/push/health
curl http://localhost:8005/api/v1/channels/whatsapp/health
curl http://localhost:8005/api/v1/channels/sms/health
curl http://localhost:8005/api/v1/channels/email/health
```

---

## Troubleshooting

### Push não funciona
- Verifique se chaves VAPID estão corretas
- Verifique se FCM credentials path está correto
- Teste com `POST /api/v1/push/test`

### WhatsApp não funciona
- Verifique se token de acesso está válido
- Verifique se templates foram aprovados pela Meta
- Verifique logs de webhook

### SMS não funciona
- Verifique credenciais Twilio/Zenvia
- Verifique se número está no formato internacional (+55...)
- Teste fallback chain

### Email não funciona
- Verifique credenciais SMTP
- Teste conexão com `telnet smtp.gmail.com 587`
- Verifique se TLS está habilitado

---

## Próximos Passos

1. Configure variáveis de ambiente
2. Teste cada canal individualmente
3. Configure regras de roteamento no D1
4. Monitore métricas no Grafana (D7)

