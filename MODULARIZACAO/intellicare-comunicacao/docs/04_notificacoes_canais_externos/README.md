# D4 - Notificações Externas

## Visão Geral

O **D4 - Notificações Externas** implementa 4 canais de comunicação externa para o IntelliCare:

1. **Push Notifications** (VAPID/FCM) - Notificações web e mobile
2. **WhatsApp Business API** (Meta Graph API) - Mensagens WhatsApp
3. **SMS** (Twilio/Zenvia/SNS) - Mensagens de texto
4. **Email** (SMTP) - Emails com templates HTML

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    D1 - Engine de Roteamento                │
│                                                              │
│  RoutingEngine → DispatcherManager → Dispatchers            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  D4 - Canais Externos                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PushDispatcher│  │WhatsAppDisp. │  │ SMSDispatcher│      │
│  │              │  │              │  │              │      │
│  │ VAPID / FCM  │  │ Meta Graph   │  │ Twilio/Zenvia│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐                                           │
│  │EmailDispatcher│                                          │
│  │              │                                           │
│  │ SMTP/Jinja2  │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    APIs Externas                             │
│                                                              │
│  Firebase FCM  │  Meta WhatsApp  │  Twilio  │  SMTP Server  │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes

### D4.1 - Base Infrastructure ✅
- Estrutura de pastas
- Modelos compartilhados (ExternalMessageLog, PushSubscription, WhatsAppSession, ChannelConfig)
- Migration de banco de dados (4 tabelas)

### D4.2 - Push Notifications ✅
- PushDispatcher (implementa ChannelDispatcher)
- VAPIDPushService (Web Push - RFC 8292)
- FCMPushService (Firebase Cloud Messaging)
- API endpoints (5 endpoints)
- Testes (7 unit tests)

### D4.3 - WhatsApp Business API ✅
- WhatsAppDispatcher (implementa ChannelDispatcher)
- WhatsAppClient (Meta Graph API v18.0)
- WhatsAppWebhookHandler (processa eventos)
- 5 templates pré-aprovados
- API endpoints (5 endpoints)
- Testes (23 unit tests)

### D4.4 - SMS (Twilio/Zenvia) ✅
- SMSDispatcher (implementa ChannelDispatcher)
- Multi-provider (Twilio, Zenvia, SNS)
- Fallback automático
- API endpoints (2 endpoints)
- Testes (17 unit tests)

### D4.5 - Email (SMTP) ✅
- EmailDispatcher (implementa ChannelDispatcher)
- EmailTemplateEngine (Jinja2)
- 4 templates HTML responsivos
- API endpoints (3 endpoints)
- Testes (18 unit tests)

### D4.6 - Integration with D1 ✅
- Registro de dispatchers no DispatcherManager
- Integração com RoutingEngine
- Documentação de integração

### D4.7 - Tests and Documentation ✅
- Testes de integração E2E
- Documentação técnica completa
- Guias operacionais

---

## Estatísticas

| Métrica | Valor |
|---------|-------|
| **Total de Linhas** | ~7,500 linhas |
| **Arquivos Criados** | 60+ arquivos |
| **Testes Unitários** | 65+ testes |
| **Cobertura Estimada** | ~90% |
| **API Endpoints** | 15 endpoints |
| **Dispatchers** | 4 dispatchers |
| **Providers** | 7 providers |
| **Templates** | 9 templates |
| **Tabelas de Banco** | 4 tabelas |

---

## Documentação

### Guias de Uso
- **[GUIA_CONFIGURACAO.md](GUIA_CONFIGURACAO.md)** - Como configurar cada canal
- **[EXEMPLOS_USO.md](EXEMPLOS_USO.md)** - Exemplos práticos de uso
- **[GUIA_OPERACIONAL.md](GUIA_OPERACIONAL.md)** - Deploy, monitoramento e troubleshooting

### Referência Técnica
- **[API_REFERENCE.md](API_REFERENCE.md)** - Referência completa de APIs
- **[MODELOS_DADOS.md](MODELOS_DADOS.md)** - Modelos de dados (Pydantic/SQLAlchemy)
- **[ARQUITETURA_INTEGRACAO.md](ARQUITETURA_INTEGRACAO.md)** - Arquitetura de integração D4-D1

---

## Quick Start

### 1. Configurar Variáveis de Ambiente

```bash
# Push (VAPID)
VAPID_PUBLIC_KEY=<chave_publica>
VAPID_PRIVATE_KEY=<chave_privada>
VAPID_SUBJECT=mailto:admin@intellicare.com.br

# WhatsApp
WHATSAPP_ACCESS_TOKEN=<token_meta>
WHATSAPP_PHONE_NUMBER_ID=<id_numero>

# SMS (Twilio)
TWILIO_ACCOUNT_SID=<account_sid>
TWILIO_AUTH_TOKEN=<auth_token>
TWILIO_FROM_NUMBER=+15551234567

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@intellicare.com.br
SMTP_PASSWORD=<senha_app>
```

### 2. Executar Migrações

```bash
alembic upgrade head
```

### 3. Iniciar Aplicação

```bash
uvicorn comunicacao.api.app:create_app --host 0.0.0.0 --port 8005
```

### 4. Verificar Canais

```bash
curl http://localhost:8005/api/v1/channels
```

### 5. Testar Canal

```bash
# Push
curl -X POST http://localhost:8005/api/v1/push/test \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user"}'

# WhatsApp
curl -X POST http://localhost:8005/api/v1/whatsapp/send \
  -H "Content-Type: application/json" \
  -d '{"to": "+5511999999999", "text": "Teste"}'

# SMS
curl -X POST http://localhost:8005/api/v1/sms/send \
  -H "Content-Type: application/json" \
  -d '{"to": "+5511999999999", "text": "Teste"}'

# Email
curl -X POST http://localhost:8005/api/v1/email/send \
  -H "Content-Type: application/json" \
  -d '{"to": ["test@example.com"], "subject": "Teste", "body_html": "<p>Teste</p>"}'
```

---

## Protocolo ChannelDispatcher

Todos os dispatchers implementam a interface `ChannelDispatcher` com 7 métodos:

```python
class ChannelDispatcher(Protocol):
    channel: str
    
    async def send(self, message: ChannelMessage) -> DispatchResult
    async def get_status(self, channel_message_id: str) -> DeliveryStatus
    async def cancel(self, channel_message_id: str) -> bool
    async def health_check(self) -> ChannelHealth
    async def test_send(self, recipient: ResolvedRecipient) -> DispatchResult
    async def get_capabilities(self) -> ChannelCapabilities
    async def validate_recipient(self, recipient: ResolvedRecipient) -> RecipientValidation
```

---

## Integração com D1

Os dispatchers são registrados automaticamente no `DispatcherManager` durante o startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    dispatcher_manager = create_default_dispatcher_manager()
    
    # Registrar PushDispatcher
    push_dispatcher = PushDispatcher(db=db, config=push_config)
    dispatcher_manager.register(push_dispatcher)
    
    # Registrar WhatsAppDispatcher
    whatsapp_dispatcher = WhatsAppDispatcher(db=db, config=whatsapp_config)
    dispatcher_manager.register(whatsapp_dispatcher)
    
    # Registrar SMSDispatcher
    sms_dispatcher = SMSDispatcher(db=db, config=sms_config)
    dispatcher_manager.register(sms_dispatcher)
    
    # Registrar EmailDispatcher
    email_dispatcher = EmailDispatcher(db=db, config=email_config)
    dispatcher_manager.register(email_dispatcher)
```

---

## Próximos Passos

1. ✅ Implementar dispatchers (D4.1-D4.5)
2. ✅ Integrar com D1 (D4.6)
3. ✅ Criar testes e documentação (D4.7)
4. ⏳ Configurar monitoramento (D7)
5. ⏳ Deploy em produção

---

## Suporte

- **Documentação**: Ver arquivos `.md` nesta pasta
- **Issues**: Abrir issue no GitHub
- **Email**: suporte@intellicare.com.br

