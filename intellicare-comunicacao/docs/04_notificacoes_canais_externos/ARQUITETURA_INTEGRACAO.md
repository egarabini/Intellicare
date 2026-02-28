# Arquitetura de Integração - D4 com D1

## Visão Geral

Este documento descreve como os **4 canais externos** (D4) se integram com o **Engine de Roteamento** (D1) do módulo IntelliCare Comunicação.

---

## Componentes Principais

### D1 - Engine de Roteamento

**Responsabilidades:**
- Receber intents de comunicação
- Aplicar regras de roteamento
- Selecionar canais apropriados
- Resolver destinatários
- Verificar conformidade LGPD
- Renderizar templates
- Despachar mensagens via dispatchers

**Componentes:**
- `RoutingEngine` - Orquestrador principal
- `DispatcherManager` - Gerencia dispatchers de canais
- `RuleMatcher` - Seleciona regras aplicáveis
- `RecipientResolver` - Resolve destinatários
- `LGPDComplianceGateway` - Verifica conformidade
- `TemplateRenderer` - Renderiza templates

### D4 - Canais Externos

**Responsabilidades:**
- Implementar protocolo `ChannelDispatcher`
- Enviar mensagens via APIs externas
- Gerenciar estado de entrega
- Validar destinatários
- Reportar saúde do canal

**Canais:**
1. **Push** (D4.2) - VAPID/FCM
2. **WhatsApp** (D4.3) - Meta Graph API
3. **SMS** (D4.4) - Twilio/Zenvia/SNS
4. **Email** (D4.5) - SMTP

---

## Protocolo ChannelDispatcher

Todos os dispatchers implementam a interface `ChannelDispatcher` com 7 métodos obrigatórios:

```python
class ChannelDispatcher(Protocol):
    channel: str  # Nome do canal (ex: "push", "whatsapp", "sms", "email")
    
    async def send(self, message: ChannelMessage) -> DispatchResult:
        """Envia mensagem pelo canal."""
        
    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        """Consulta status de entrega."""
        
    async def cancel(self, channel_message_id: str) -> bool:
        """Cancela mensagem (se suportado)."""
        
    async def health_check(self) -> ChannelHealth:
        """Verifica saúde do canal."""
        
    async def test_send(self, recipient: ResolvedRecipient) -> DispatchResult:
        """Envia mensagem de teste."""
        
    async def get_capabilities(self) -> ChannelCapabilities:
        """Retorna capacidades do canal."""
        
    async def validate_recipient(self, recipient: ResolvedRecipient) -> RecipientValidation:
        """Valida destinatário."""
```

---

## Fluxo de Integração

### 1. Startup (Registro de Dispatchers)

```
app.py (lifespan)
    ↓
create_default_dispatcher_manager()
    ↓
Registrar dispatchers:
    - RocketChatDispatcher (D2)
    - JitsiDispatcher (D3)
    - PushDispatcher (D4.2)
    - WhatsAppDispatcher (D4.3)
    - SMSDispatcher (D4.4)
    - EmailDispatcher (D4.5)
    ↓
DispatcherManager.register(dispatcher)
    ↓
Dispatchers disponíveis para RoutingEngine
```

### 2. Envio de Mensagem

```
Cliente/Redis Event
    ↓
POST /api/v1/routing/send
    ↓
RoutingEngine.send_intent(intent)
    ↓
RuleMatcher.match(intent) → Regras aplicáveis
    ↓
RecipientResolver.resolve(intent) → Destinatários
    ↓
LGPDComplianceGateway.check(intent) → Verificação LGPD
    ↓
TemplateRenderer.render(template, data) → Conteúdo renderizado
    ↓
DispatcherManager.dispatch(channel, message)
    ↓
Dispatcher.send(message) → API Externa
    ↓
ExternalMessageLog (banco de dados)
    ↓
DispatchResult → Cliente
```

### 3. Fallback e Retry

```
RoutingEngine.send_intent(intent)
    ↓
Dispatcher.send(message) → FALHA
    ↓
FallbackMonitor detecta falha
    ↓
Seleciona próximo canal (fallback_channels)
    ↓
Dispatcher.send(message) → SUCESSO
    ↓
TimelineEvent registra fallback
```

---

## Registro de Dispatchers

### Código (app.py)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    dispatcher_manager = create_default_dispatcher_manager()
    
    # D4.2 - Push Notifications
    try:
        from comunicacao.channels.push import PushConfig, PushDispatcher
        push_config = PushConfig.from_env()
        async with get_db_session() as db:
            push_dispatcher = PushDispatcher(db=db, config=push_config)
            dispatcher_manager.register(push_dispatcher)
            logger.info("PushDispatcher registrado (D4.2)")
    except Exception as exc:
        logger.warning("PushDispatcher não disponível: %s", exc)
    
    # D4.3 - WhatsApp
    # D4.4 - SMS
    # D4.5 - Email
    # ... (similar pattern)
```

---

## Tabelas de Banco de Dados

### external_message_log

Armazena log unificado de todas as mensagens externas:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | ID único |
| channel | VARCHAR | Canal (push, whatsapp, sms, email) |
| direction | VARCHAR | Direção (outbound, inbound) |
| intent_id | VARCHAR | ID do intent (D1) |
| correlation_id | VARCHAR | ID de correlação |
| recipient_id | VARCHAR | ID do destinatário |
| provider_message_id | VARCHAR | ID na API externa |
| status | VARCHAR | Status (pending, sent, delivered, failed) |
| message_content | JSON | Conteúdo da mensagem |
| sent_at | TIMESTAMP | Data/hora de envio |
| delivered_at | TIMESTAMP | Data/hora de entrega |
| error_code | VARCHAR | Código de erro |
| error_message | TEXT | Mensagem de erro |

### push_subscriptions

Armazena inscrições de push notifications:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | ID único |
| user_id | VARCHAR | ID do usuário |
| device_id | VARCHAR | ID do dispositivo |
| provider | VARCHAR | Provider (vapid, fcm) |
| subscription_data | JSON | Dados da inscrição |
| created_at | TIMESTAMP | Data de criação |

### whatsapp_sessions

Armazena janelas de 24h do WhatsApp:

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | ID único |
| phone_number | VARCHAR | Número de telefone |
| session_start | TIMESTAMP | Início da janela |
| session_end | TIMESTAMP | Fim da janela |
| last_message_at | TIMESTAMP | Última mensagem |

---

## APIs de Integração

### Endpoints de Canais

```bash
# Listar canais disponíveis
GET /api/v1/channels

# Health check de canal
GET /api/v1/channels/{channel}/health

# Testar canal
POST /api/v1/channels/{channel}/test
```

### Endpoints Específicos

```bash
# Push
POST /api/v1/push/subscribe
POST /api/v1/push/send

# WhatsApp
POST /api/v1/whatsapp/send
POST /api/v1/whatsapp/webhook

# SMS
POST /api/v1/sms/send
GET /api/v1/sms/providers

# Email
POST /api/v1/email/send
GET /api/v1/email/templates
```

---

## Métricas e Observabilidade

### Métricas Prometheus (D7)

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

### Dashboards Grafana

- **Overview** - Visão geral de todos os canais
- **Channels** - Métricas por canal
- **External Notifications** - Específico para D4

---

## Conformidade LGPD (D6)

Todos os dispatchers respeitam:

1. **Preferências de comunicação** - Verificadas antes do envio
2. **Quiet hours** - Não enviar fora do horário permitido
3. **Consent log** - Registrar consentimento
4. **Audit trail** - Trilha de auditoria completa

---

## Próximos Passos

1. ✅ Implementar dispatchers (D4.1-D4.5)
2. ✅ Registrar no DispatcherManager (D4.6)
3. ⏳ Testes de integração (D4.7)
4. ⏳ Documentação operacional (D4.7)
5. ⏳ Monitoramento e alertas (D7)

