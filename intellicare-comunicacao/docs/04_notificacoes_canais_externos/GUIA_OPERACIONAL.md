# Guia Operacional - Canais Externos (D4)

## Visão Geral

Este guia descreve procedimentos operacionais para deploy, monitoramento e troubleshooting dos canais externos.

---

## 1. Deploy em Produção

### 1.1. Pré-requisitos

- [ ] Python 3.11+ instalado
- [ ] PostgreSQL 14+ configurado
- [ ] Redis 7+ configurado
- [ ] Variáveis de ambiente configuradas
- [ ] Certificados SSL/TLS válidos
- [ ] Contas configuradas:
  - [ ] Firebase (FCM)
  - [ ] Meta Business (WhatsApp)
  - [ ] Twilio (SMS)
  - [ ] Zenvia (SMS fallback)
  - [ ] SMTP (Email)

### 1.2. Checklist de Deploy

```bash
# 1. Clonar repositório
git clone https://github.com/seu-org/intellicare-comunicacao.git
cd intellicare-comunicacao

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
nano .env  # Editar com valores reais

# 5. Executar migrações
alembic upgrade head

# 6. Verificar configuração
python -m comunicacao.cli check-config

# 7. Testar canais
python -m comunicacao.cli test-channels

# 8. Iniciar aplicação
uvicorn comunicacao.api.app:create_app --host 0.0.0.0 --port 8005
```

### 1.3. Variáveis de Ambiente Críticas

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/intellicare

# Redis
REDIS_URL=redis://localhost:6379/0

# Push (VAPID)
VAPID_PUBLIC_KEY=<chave_publica>
VAPID_PRIVATE_KEY=<chave_privada>
VAPID_SUBJECT=mailto:admin@intellicare.com.br

# Push (FCM)
FCM_PROJECT_ID=<projeto_firebase>
FCM_CREDENTIALS_PATH=/path/to/firebase-credentials.json

# WhatsApp
WHATSAPP_ACCESS_TOKEN=<token_meta>
WHATSAPP_PHONE_NUMBER_ID=<id_numero>
WHATSAPP_WEBHOOK_VERIFY_TOKEN=<token_webhook>

# SMS (Twilio)
TWILIO_ACCOUNT_SID=<account_sid>
TWILIO_AUTH_TOKEN=<auth_token>
TWILIO_FROM_NUMBER=+15551234567

# SMS (Zenvia)
ZENVIA_API_TOKEN=<api_token>
ZENVIA_FROM_NAME=IntelliCare

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@intellicare.com.br
SMTP_PASSWORD=<senha_app>
SMTP_FROM_EMAIL=noreply@intellicare.com.br
SMTP_USE_TLS=true

# Keycloak
KEYCLOAK_URL=https://keycloak.gsi.srv.br
KEYCLOAK_REALM=bemcuidar
KEYCLOAK_CLIENT_ID=intellicare-comunicacao
```

---

## 2. Monitoramento

### 2.1. Health Checks

```bash
# Verificar saúde geral
curl http://localhost:8005/api/v1/health

# Verificar canais específicos
curl http://localhost:8005/api/v1/channels/push/health
curl http://localhost:8005/api/v1/channels/whatsapp/health
curl http://localhost:8005/api/v1/channels/sms/health
curl http://localhost:8005/api/v1/channels/email/health
```

### 2.2. Métricas Prometheus

Acessar: `http://localhost:8005/metrics`

**Métricas Principais**:
```
# Mensagens enviadas por canal
communication_messages_sent_total{channel="push|whatsapp|sms|email"}

# Taxa de falha por canal
communication_messages_failed_total{channel="push|whatsapp|sms|email"}

# Latência de envio
communication_dispatch_duration_seconds{channel="push|whatsapp|sms|email"}

# Health check
communication_channel_health{channel="push|whatsapp|sms|email"}
```

### 2.3. Dashboards Grafana

**Dashboards Disponíveis**:
1. **Overview** - Visão geral de todos os canais
2. **Channels** - Métricas detalhadas por canal
3. **External Notifications** - Específico para D4
4. **SLA** - Métricas de SLA e disponibilidade

**Importar Dashboards**:
```bash
# Copiar JSONs para Grafana
cp docs/07_dashboard_monitoramento/dashboards/*.json /var/lib/grafana/dashboards/
```

### 2.4. Logs

**Localização**:
- Logs de aplicação: `/var/log/intellicare/comunicacao.log`
- Logs de erro: `/var/log/intellicare/comunicacao-error.log`

**Filtrar por canal**:
```bash
# Push
tail -f /var/log/intellicare/comunicacao.log | grep "PushDispatcher"

# WhatsApp
tail -f /var/log/intellicare/comunicacao.log | grep "WhatsAppDispatcher"

# SMS
tail -f /var/log/intellicare/comunicacao.log | grep "SMSDispatcher"

# Email
tail -f /var/log/intellicare/comunicacao.log | grep "EmailDispatcher"
```

---

## 3. Troubleshooting

### 3.1. Push Notifications

**Problema**: Push não está sendo enviado

**Diagnóstico**:
```bash
# 1. Verificar configuração
curl http://localhost:8005/api/v1/channels/push/health

# 2. Verificar logs
tail -f /var/log/intellicare/comunicacao.log | grep "PushDispatcher"

# 3. Testar envio
curl -X POST http://localhost:8005/api/v1/push/test \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user"}'
```

**Soluções Comuns**:
- Verificar se chaves VAPID estão corretas
- Verificar se FCM credentials path está correto
- Verificar se usuário tem subscriptions ativas
- Verificar se endpoint de subscription está válido

---

### 3.2. WhatsApp

**Problema**: Mensagens não estão sendo entregues

**Diagnóstico**:
```bash
# 1. Verificar configuração
curl http://localhost:8005/api/v1/channels/whatsapp/health

# 2. Verificar templates
curl http://localhost:8005/api/v1/whatsapp/templates

# 3. Verificar logs de webhook
tail -f /var/log/intellicare/comunicacao.log | grep "WhatsAppWebhook"
```

**Soluções Comuns**:
- Verificar se token de acesso está válido (renovar se expirado)
- Verificar se templates foram aprovados pela Meta
- Verificar se número está no formato internacional (+55...)
- Verificar se está dentro da janela de 24h para mensagens de texto
- Verificar rate limits da Meta (80 msg/min)

---

### 3.3. SMS

**Problema**: SMS não está sendo enviado

**Diagnóstico**:
```bash
# 1. Verificar providers disponíveis
curl http://localhost:8005/api/v1/sms/providers

# 2. Verificar configuração
curl http://localhost:8005/api/v1/channels/sms/health

# 3. Verificar logs
tail -f /var/log/intellicare/comunicacao.log | grep "SMSDispatcher"
```

**Soluções Comuns**:
- Verificar credenciais Twilio/Zenvia
- Verificar se número está no formato internacional (+55...)
- Verificar se mensagem não excede 160 caracteres
- Verificar fallback chain (Twilio → Zenvia)
- Verificar saldo da conta Twilio/Zenvia

---

### 3.4. Email

**Problema**: Emails não estão sendo enviados

**Diagnóstico**:
```bash
# 1. Verificar configuração SMTP
curl http://localhost:8005/api/v1/channels/email/health

# 2. Testar conexão SMTP
telnet smtp.gmail.com 587

# 3. Verificar logs
tail -f /var/log/intellicare/comunicacao.log | grep "EmailDispatcher"
```

**Soluções Comuns**:
- Verificar credenciais SMTP
- Verificar se TLS está habilitado
- Verificar se porta está correta (587 para TLS, 465 para SSL)
- Verificar se senha de app está correta (Gmail)
- Verificar se templates existem
- Verificar se email não está sendo marcado como spam

---

## 4. Manutenção

### 4.1. Backup

```bash
# Backup de banco de dados
pg_dump -U postgres intellicare > backup_$(date +%Y%m%d).sql

# Backup de configurações
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env comunicacao/templates/
```

### 4.2. Limpeza de Logs

```bash
# Limpar logs antigos (>30 dias)
find /var/log/intellicare/ -name "*.log" -mtime +30 -delete

# Limpar external_message_log (>90 dias)
psql -U postgres intellicare -c "DELETE FROM comunicacao_operacional.external_message_log WHERE sent_at < NOW() - INTERVAL '90 days';"
```

### 4.3. Atualização

```bash
# 1. Backup
pg_dump -U postgres intellicare > backup_pre_update.sql

# 2. Pull latest
git pull origin main

# 3. Atualizar dependências
pip install -r requirements.txt --upgrade

# 4. Executar migrações
alembic upgrade head

# 5. Reiniciar aplicação
systemctl restart intellicare-comunicacao
```

---

## 5. Alertas

### 5.1. Alertas Críticos

**Configurar alertas no Grafana**:
- Service Down (>5min)
- High Failure Rate (>10%)
- High Latency (>5s)
- LGPD Violation

### 5.2. Contatos de Emergência

- **DevOps**: devops@intellicare.com.br
- **Suporte**: suporte@intellicare.com.br
- **On-call**: +55 11 99999-9999

---

## 6. SLA

| Canal | Disponibilidade | Latência Média | Taxa de Sucesso |
|-------|----------------|----------------|-----------------|
| Push | 99.9% | <500ms | >95% |
| WhatsApp | 99.5% | <2s | >90% |
| SMS | 99.5% | <3s | >90% |
| Email | 99.9% | <5s | >95% |

---

## Próximos Passos

1. Configure monitoramento (Prometheus + Grafana)
2. Configure alertas críticos
3. Teste procedimentos de backup/restore
4. Documente runbooks específicos
5. Treine equipe de operações

