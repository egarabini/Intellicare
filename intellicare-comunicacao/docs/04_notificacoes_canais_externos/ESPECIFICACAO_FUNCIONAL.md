# Domínio 4 — Notificações e Canais Externos
## Especificação Funcional Detalhada

**Identificadores**: EF-COM-030, EF-COM-031, EF-COM-032, EF-COM-033  
**Prioridade Global**: ALTA  
**Sprint**: S4–S5  
**Dependências**: D1 (IChannelDispatcher, DispatcherManager, TemplateRenderer)  
**Dependentes**: D3 (envio de links teleconsulta), D5 (eventos), D7 (métricas)

---

## 1. OBJETIVO

Implementar os dispatchers de canais externos de comunicação com pacientes e profissionais fora do Rocket.Chat:

1. **Push Notifications** (Web/Mobile via VAPID/FCM)
2. **WhatsApp** (via WhatsApp Business API / Meta Cloud API)
3. **SMS** (via gateway compatível — Twilio, Zenvia, ou equivalente)
4. **Email** (via SMTP com templates HTML)

Cada canal implementa `IChannelDispatcher` do Domínio 1, sendo ativado pelo `DispatcherManager` conforme as regras de roteamento.

**Estado Atual**: Nenhum canal externo implementado. Apenas Rocket.Chat operacional.

---

## 2. CONTEXTO ARQUITETURAL

```
┌─────────────────────────────────────────────────────────────────┐
│                    intellicare-comunicacao                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              DispatcherManager (D1)                      │    │
│  │                                                         │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │  Push    │ │ WhatsApp │ │   SMS    │ │  Email   │   │    │
│  │  │Dispatcher│ │Dispatcher│ │Dispatcher│ │Dispatcher│   │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │    │
│  │       │             │            │             │         │    │
│  └───────┼─────────────┼────────────┼─────────────┼─────────┘    │
│          │             │            │             │              │
└──────────┼─────────────┼────────────┼─────────────┼──────────────┘
           │             │            │             │
           ▼             ▼            ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ VAPID/   │  │ Meta     │  │ Twilio/  │  │ SMTP     │
    │ FCM      │  │ Cloud    │  │ Zenvia   │  │ Server   │
    │ Server   │  │ API      │  │ API      │  │          │
    └──────────┘  └──────────┘  └──────────┘  └──────────┘
           │             │            │             │
           ▼             ▼            ▼             ▼
       Browser       WhatsApp      Phone         Inbox
       (SW)         (paciente)   (paciente)    (profissional)
```

---

## 3. EF-COM-030 — Push Notifications (VAPID/FCM)

### 3.1 Descrição Funcional

Notificações push para navegadores (Web Push via VAPID) e apps mobile (Firebase Cloud Messaging). Usadas para alertas em tempo real quando o profissional está fora do Rocket.Chat.

### 3.2 PushDispatcher

```python
class PushDispatcher(IChannelDispatcher):
    """Dispatcher para Push Notifications (VAPID + FCM)."""
    
    def __init__(self, config: PushConfig):
        self._config = config
        self._vapid = VAPIDPushService(config.vapid)
        self._fcm = FCMPushService(config.fcm) if config.fcm else None
    
    @property
    def channel_name(self) -> str:
        return "push"
    
    @property
    def display_name(self) -> str:
        return "Push Notification"
    
    async def is_available(self) -> bool:
        """Verifica se pelo menos um serviço push está configurado."""
        return True  # VAPID sempre disponível se chaves configuradas
    
    async def send(
        self, 
        recipient: ResolvedRecipient, 
        content: RenderedContent, 
        metadata: Dict
    ) -> DispatchResult:
        """
        Envia push notification.
        
        Lógica:
        1. Buscar subscriptions do usuário (pode ter várias: desktop, mobile)
        2. Para cada subscription:
           a. Se subscription.type == "web" → VAPID
           b. Se subscription.type == "fcm" → FCM
        3. Enviar em paralelo para todas as subscriptions
        4. Retornar resultado consolidado
        """
    
    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        """Push não tem read receipt nativo. Retorna DELIVERED se enviado sem erro."""
        return DeliveryStatus.DELIVERED
    
    async def get_health(self) -> ChannelHealth:
        """VAPID: OK se chaves configuradas. FCM: testa token."""
    
    async def supports_read_receipt(self) -> bool:
        return False
    
    async def supports_rich_content(self) -> bool:
        return True  # Suporta icon, badge, actions


class PushConfig(BaseModel):
    vapid: VAPIDConfig
    fcm: Optional[FCMConfig] = None


class VAPIDConfig(BaseModel):
    """Configuração VAPID para Web Push."""
    private_key: str            # VAPID private key (base64url)
    public_key: str             # VAPID public key (base64url)
    subject: str = "mailto:intellicare@gsi.srv.br"
    ttl: int = 86400            # Time-to-live em segundos


class FCMConfig(BaseModel):
    """Configuração Firebase Cloud Messaging."""
    project_id: str
    service_account_key_path: str    # Caminho para o JSON da service account
    default_topic: str = "intellicare-alerts"
```

### 3.3 Modelo de Subscription

```python
class PushSubscription(BaseModel):
    """Subscription de push notification de um dispositivo."""
    
    id: UUID = Field(default_factory=uuid4)
    user_id: str                          # Keycloak user_id
    subscription_type: str                # "web" | "fcm"
    
    # Web Push (VAPID)
    endpoint: Optional[str]               # URL do push service
    p256dh_key: Optional[str]             # Chave pública do cliente
    auth_key: Optional[str]               # Auth secret do cliente
    
    # FCM
    fcm_token: Optional[str]              # Token do dispositivo Firebase
    
    # Metadata
    device_name: Optional[str]            # "Chrome Desktop", "Android App"
    user_agent: Optional[str]
    active: bool = True
    last_used_at: Optional[datetime]
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PushPayload(BaseModel):
    """Payload enviado na push notification."""
    title: str                            # Título da notificação
    body: str                             # Corpo da mensagem
    icon: str = "/icons/intellicare-192.png"
    badge: str = "/icons/badge-72.png"
    tag: Optional[str]                    # Agrupa notificações (ex: "alert-P001")
    data: Optional[Dict]                  # Dados extras para o Service Worker
    actions: Optional[List[Dict]]         # Botões de ação
    # Exemplo de actions:
    # [
    #   { "action": "view", "title": "Ver Detalhes", "icon": "/icons/view.png" },
    #   { "action": "dismiss", "title": "Dispensar" }
    # ]
    require_interaction: bool = False     # True para alertas CRITICAL
    renotify: bool = True                 # Vibrar novamente mesmo com mesmo tag
    silent: bool = False                  # Sem som (para LOW severity)
```

### 3.4 Serviços Push

```python
class VAPIDPushService:
    """Envia Web Push via protocolo VAPID (RFC 8292)."""
    
    def __init__(self, config: VAPIDConfig):
        self._config = config
    
    async def send(self, subscription: PushSubscription, payload: PushPayload) -> bool:
        """
        Envia push via VAPID.
        
        Usa: pywebpush ou aiohttp direto
        
        Fluxo:
        1. Serializar payload como JSON
        2. Criptografar com chaves do subscription (p256dh, auth)
        3. Assinar com VAPID private key
        4. POST para subscription.endpoint
        5. Se 201 → sucesso
        6. Se 410 (Gone) → marcar subscription como inativa
        7. Se 429 → retry com backoff
        """


class FCMPushService:
    """Envia Push via Firebase Cloud Messaging v1 API."""
    
    def __init__(self, config: FCMConfig):
        self._config = config
    
    async def send(self, subscription: PushSubscription, payload: PushPayload) -> bool:
        """
        Envia via FCM HTTP v1 API.
        
        POST https://fcm.googleapis.com/v1/projects/{project_id}/messages:send
        Authorization: Bearer {access_token}
        Body: {
            "message": {
                "token": subscription.fcm_token,
                "notification": {
                    "title": payload.title,
                    "body": payload.body,
                    "image": payload.icon
                },
                "data": payload.data,
                "android": { "priority": "high" },
                "webpush": { "headers": { "Urgency": "high" } }
            }
        }
        """
    
    async def send_to_topic(self, topic: str, payload: PushPayload) -> bool:
        """Envia para topic (ex: todos os médicos)."""
```

### 3.5 API Endpoints Push

```yaml
# ── Subscriptions ──
POST /api/v1/push/subscribe
  Description: Registra subscription de push notification
  Auth: Keycloak (qualquer usuário autenticado)
  Body:
    subscription_type: "web" | "fcm"
    # Se web:
    endpoint: str
    p256dh_key: str
    auth_key: str
    # Se fcm:
    fcm_token: str
    device_name: Optional[str]
  Response 201: { subscription_id: str }

DELETE /api/v1/push/subscribe/{subscription_id}
  Description: Remove subscription
  Auth: Keycloak (owner)
  Response 200: { deleted: true }

GET /api/v1/push/subscriptions
  Description: Lista subscriptions do usuário
  Auth: Keycloak (owner ou admin)
  Response 200: List[PushSubscription]

# ── VAPID Public Key ──
GET /api/v1/push/vapid-key
  Description: Retorna VAPID public key para o frontend
  Auth: None (público)
  Response 200: { publicKey: str }

# ── Teste ──
POST /api/v1/push/test
  Description: Envia push de teste para o usuário
  Auth: Keycloak
  Response 200: { sent_to: int, failed: int }
```

### 3.6 Testes Esperados Push

```
test_push/
├── test_dispatcher.py
│   ├── test_send_to_web_subscription
│   ├── test_send_to_fcm_subscription
│   ├── test_send_to_multiple_devices
│   ├── test_expired_subscription_marked_inactive
│   ├── test_critical_alert_requires_interaction
│   ├── test_low_severity_silent
│   └── test_health_check
├── test_vapid.py
│   ├── test_valid_vapid_keys
│   ├── test_send_encrypted_payload
│   ├── test_410_marks_inactive
│   └── test_429_retries
├── test_fcm.py
│   ├── test_send_to_token
│   ├── test_send_to_topic
│   └── test_invalid_token_handled
└── test_api.py
    ├── test_subscribe_web
    ├── test_subscribe_fcm
    ├── test_unsubscribe
    ├── test_get_vapid_key_public
    └── test_send_test_notification
```

---

## 4. EF-COM-031 — WhatsApp (Business API)

### 4.1 Descrição Funcional

Canal primário de comunicação com pacientes. Utiliza a **Meta Cloud API** (WhatsApp Business Platform) para enviar:

1. **Message Templates** (pré-aprovados pela Meta) — alertas, lembretes, convites
2. **Session Messages** (dentro da janela de 24h) — respostas interativas
3. **Interactive Messages** — botões, listas de opções

### 4.2 WhatsAppDispatcher

```python
class WhatsAppDispatcher(IChannelDispatcher):
    """Dispatcher para WhatsApp Business API (Meta Cloud API)."""
    
    def __init__(self, config: WhatsAppConfig):
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def channel_name(self) -> str:
        return "whatsapp"
    
    @property
    def display_name(self) -> str:
        return "WhatsApp"
    
    async def is_available(self) -> bool:
        """Verifica se WhatsApp Business API está acessível."""
        # GET https://graph.facebook.com/v18.0/{phone_number_id}
    
    async def send(
        self, 
        recipient: ResolvedRecipient, 
        content: RenderedContent, 
        metadata: Dict
    ) -> DispatchResult:
        """
        Envia mensagem via WhatsApp Business API.
        
        Lógica:
        1. Se content.template_name → enviar como Template Message
        2. Se sessão ativa (< 24h desde última mensagem do paciente) → session message
        3. Se template_name não mapeado → fallback para texto simples
        
        Meta Cloud API:
        POST https://graph.facebook.com/v18.0/{phone_number_id}/messages
        Authorization: Bearer {access_token}
        Content-Type: application/json
        Body:
        {
            "messaging_product": "whatsapp",
            "to": recipient.phone,
            "type": "template",
            "template": {
                "name": "teleconsulta_convite",
                "language": { "code": "pt_BR" },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            { "type": "text", "text": "Maria Santos" },
                            { "type": "text", "text": "Dr. João" },
                            { "type": "text", "text": "20/02/2026 14:00" }
                        ]
                    }
                ]
            }
        }
        """
    
    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        """WhatsApp envia status via webhook. Consultar do banco."""
    
    async def get_health(self) -> ChannelHealth:
        """Testa Graph API."""
    
    async def supports_read_receipt(self) -> bool:
        return True  # WhatsApp envia read, delivered via webhook
    
    async def supports_rich_content(self) -> bool:
        return True  # Suporta botões, listas, mídia


class WhatsAppConfig(BaseModel):
    """Configuração WhatsApp Business API."""
    
    # Meta Cloud API
    graph_api_version: str = "v18.0"
    graph_api_url: str = "https://graph.facebook.com"
    phone_number_id: str               # ID do número de telefone no Meta
    business_account_id: str           # WABA ID
    access_token: str                  # Token de acesso permanente
    
    # Webhook (para receber status e mensagens)
    webhook_verify_token: str          # Token para verificação do webhook
    
    # Rate Limiting
    max_messages_per_second: int = 80  # WhatsApp Business tier limit
    
    # Templates
    default_language: str = "pt_BR"
```

### 4.3 Templates WhatsApp (pré-aprovados)

Templates precisam ser submetidos e aprovados pela Meta antes de uso. Cada template tem um nome, idioma, e placeholders:

```python
WHATSAPP_TEMPLATES = {
    # Template 1: Alerta Clínico
    "alerta_clinico": {
        "meta_template_name": "alerta_clinico_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "components": [
            {
                "type": "HEADER",
                "format": "TEXT",
                "text": "🚨 Alerta IntelliCare"
            },
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}},\n\n"
                    "Alerta para o paciente {{2}}:\n"
                    "⚠️ {{3}}\n"
                    "Severidade: {{4}}\n\n"
                    "Por favor, verifique o caso com urgência."
                ),
                "example": {
                    "body_text": [
                        ["Dr. João", "Maria Santos", "eGFR < 30 ml/min", "CRÍTICA"]
                    ]
                }
            },
            {
                "type": "FOOTER",
                "text": "IntelliCare - Plataforma de Saúde Inteligente"
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "URL", "text": "Ver no Portal", "url": "https://portal.gsi.srv.br/alert/{{1}}"},
                    {"type": "QUICK_REPLY", "text": "Confirmar Leitura"}
                ]
            }
        ]
    },
    
    # Template 2: Convite Teleconsulta (para paciente)
    "teleconsulta_convite": {
        "meta_template_name": "teleconsulta_convite_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "components": [
            {
                "type": "HEADER",
                "format": "TEXT",
                "text": "📹 Teleconsulta Agendada"
            },
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}}!\n\n"
                    "Sua teleconsulta foi agendada:\n"
                    "👨‍⚕️ Profissional: {{2}}\n"
                    "📅 Data: {{3}}\n"
                    "🕐 Horário: {{4}}\n\n"
                    "Clique no botão abaixo para entrar na sala no horário marcado.\n\n"
                    "💡 Dicas:\n"
                    "• Use Wi-Fi ou 4G\n"
                    "• Fique em local silencioso\n"
                    "• Permita câmera e microfone"
                ),
                "example": {
                    "body_text": [
                        ["Maria Santos", "Dr. João Silva", "20/02/2026", "14:00"]
                    ]
                }
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "URL", "text": "Entrar na Sala", "url": "https://meet.gsi.srv.br/{{1}}"}
                ]
            }
        ]
    },
    
    # Template 3: Lembrete de Medicação
    "lembrete_medicacao": {
        "meta_template_name": "lembrete_medicacao_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}}! 💊\n\n"
                    "Lembrete: está na hora de tomar:\n"
                    "• {{2}}\n\n"
                    "Horário: {{3}}\n\n"
                    "Cuide-se! A regularidade no tratamento faz toda a diferença."
                )
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "QUICK_REPLY", "text": "✅ Tomei"},
                    {"type": "QUICK_REPLY", "text": "⏰ Lembrar depois"}
                ]
            }
        ]
    },
    
    # Template 4: Lembrete de Consulta
    "lembrete_consulta": {
        "meta_template_name": "lembrete_consulta_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}}!\n\n"
                    "Lembrete: sua teleconsulta com {{2}} "
                    "é em {{3}} minutos ({{4}}).\n\n"
                    "🔗 Acesse pelo link no botão abaixo.\n\n"
                    "Certifique-se de estar em local com boa conexão."
                )
            },
            {
                "type": "BUTTONS",
                "buttons": [
                    {"type": "URL", "text": "Entrar na Sala", "url": "https://meet.gsi.srv.br/{{1}}"}
                ]
            }
        ]
    },
    
    # Template 5: Resultado de Exame
    "resultado_exame": {
        "meta_template_name": "resultado_exame_v1",
        "language": "pt_BR",
        "category": "UTILITY",
        "components": [
            {
                "type": "BODY",
                "text": (
                    "Olá {{1}}!\n\n"
                    "Seus resultados de exame foram analisados pelo seu médico.\n\n"
                    "Para ver os detalhes, acesse o portal do paciente "
                    "ou entre em contato com sua equipe de saúde.\n\n"
                    "Em caso de urgência, procure a unidade de saúde mais próxima."
                )
            }
        ]
    }
}
```

### 4.4 Webhook de Recebimento (WhatsApp → IntelliCare)

```python
class WhatsAppWebhookHandler:
    """Processa webhooks do WhatsApp Business API."""
    
    async def handle_webhook(self, payload: Dict) -> Dict:
        """
        Processa evento do WhatsApp.
        
        Tipos de evento:
        1. messages → Mensagem recebida do paciente
        2. statuses → Status de entrega (sent, delivered, read, failed)
        """
    
    async def handle_status_update(self, status: Dict) -> None:
        """
        Atualiza status de entrega no DeliveryResult.
        
        Mapeamento:
        - "sent" → DeliveryStatus.SENT
        - "delivered" → DeliveryStatus.DELIVERED  
        - "read" → DeliveryStatus.READ
        - "failed" → DeliveryStatus.FAILED (com reason)
        """
    
    async def handle_incoming_message(self, message: Dict) -> None:
        """
        Processa mensagem recebida do paciente.
        
        Possibilidades:
        - Quick Reply de um template → processar ação
          - "✅ Tomei" → registrar adesão medicamentosa
          - "⏰ Lembrar depois" → reagendar lembrete em 30 min
          - "Confirmar Leitura" → marcar alerta como lido
        - Texto livre → encaminhar para Dr. Nise (chatbot) ou para equipe no RC
        """
    
    async def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verificação do webhook pela Meta.
        GET /api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=xxx&hub.challenge=yyy
        Retorna challenge se token válido.
        """
```

### 4.5 API Endpoints WhatsApp

```yaml
# ── Webhook Meta ──
GET /api/v1/webhooks/whatsapp
  Description: Verificação de webhook pela Meta
  Auth: verify_token
  Query: hub.mode, hub.verify_token, hub.challenge
  Response 200: challenge (text/plain)

POST /api/v1/webhooks/whatsapp
  Description: Recebe eventos do WhatsApp
  Auth: Signature HMAC-SHA256 (X-Hub-Signature-256)
  Body: Webhook payload
  Response 200: "ok"

# ── Envio direto (para testes/admin) ──
POST /api/v1/whatsapp/send
  Description: Envia mensagem WhatsApp
  Auth: Keycloak (admin, system)
  Body:
    to: str                    # Número (+55...)
    template_name: str         # Nome do template
    template_params: List[str] # Parâmetros do template
    language: str = "pt_BR"
  Response 200: { message_id: str, status: str }

# ── Templates ──
GET /api/v1/whatsapp/templates
  Description: Lista templates aprovados
  Auth: Keycloak (admin)
  Response 200: List[{ name, status, language, category }]
```

### 4.6 Testes WhatsApp

```
test_whatsapp/
├── test_dispatcher.py
│   ├── test_send_template_message
│   ├── test_send_session_message
│   ├── test_send_with_buttons
│   ├── test_invalid_phone_number
│   ├── test_rate_limit_respected
│   └── test_health_check
├── test_webhook.py
│   ├── test_verify_webhook_valid_token
│   ├── test_verify_webhook_invalid_token
│   ├── test_status_update_delivered
│   ├── test_status_update_read
│   ├── test_status_update_failed
│   ├── test_incoming_quick_reply_tomei
│   ├── test_incoming_quick_reply_lembrar
│   ├── test_incoming_text_forwarded
│   └── test_signature_validation
└── test_templates.py
    ├── test_alerta_clinico_params
    ├── test_teleconsulta_convite_params
    ├── test_lembrete_medicacao_params
    └── test_unknown_template_falls_back
```

---

## 5. EF-COM-032 — SMS

### 5.1 Descrição Funcional

Canal de fallback para quando WhatsApp não está disponível (paciente sem smartphone ou sem WhatsApp). SMS é usado para:

1. Notificações curtas e urgentes
2. Links de teleconsulta
3. Fallback quando WhatsApp falha (cascading do D1)

### 5.2 SMSDispatcher

```python
class SMSDispatcher(IChannelDispatcher):
    """Dispatcher para SMS via gateway (Twilio/Zenvia/Amazon SNS)."""
    
    def __init__(self, config: SMSConfig):
        self._config = config
        self._provider = self._create_provider(config)
    
    @property
    def channel_name(self) -> str:
        return "sms"
    
    @property
    def display_name(self) -> str:
        return "SMS"
    
    async def is_available(self) -> bool:
        """Testa conectividade com o gateway."""
    
    async def send(
        self, 
        recipient: ResolvedRecipient, 
        content: RenderedContent, 
        metadata: Dict
    ) -> DispatchResult:
        """
        Envia SMS.
        
        Lógica:
        1. Truncar mensagem para 160 chars (ou concatenar se permitido)
        2. Formatar número (E.164: +55DDDXXXXXXXX)
        3. Enviar via provider
        4. Se provider = Twilio:
           POST https://api.twilio.com/2010-04-01/Accounts/{SID}/Messages.json
           Body: { To: "+5511999...", From: "+5511XXX...", Body: "..." }
        5. Se provider = Zenvia:
           POST https://api.zenvia.com/v2/channels/sms/messages
           Body: { from: "intellicare", to: "+5511999...", contents: [{ type: "text", text: "..." }] }
        """
    
    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        """Consulta status via API do provider."""
    
    async def get_health(self) -> ChannelHealth:
        """Testa API do provider."""
    
    async def supports_read_receipt(self) -> bool:
        return False  # SMS padrão não tem read receipt
    
    async def supports_rich_content(self) -> bool:
        return False  # Texto puro


class SMSConfig(BaseModel):
    """Configuração de SMS."""
    
    provider: str = "twilio"           # "twilio" | "zenvia" | "sns"
    
    # Twilio
    twilio_account_sid: Optional[str]
    twilio_auth_token: Optional[str]
    twilio_from_number: Optional[str]  # Número remetente
    
    # Zenvia
    zenvia_api_token: Optional[str]
    zenvia_from: Optional[str]
    
    # Amazon SNS
    aws_region: Optional[str]
    aws_access_key: Optional[str]
    aws_secret_key: Optional[str]
    
    # Geral
    max_message_length: int = 160
    allow_concatenation: bool = True   # Permitir SMS > 160 chars
    max_concat_segments: int = 3       # Máximo de segmentos (3 x 153 = 459 chars)


class SMSProviderFactory:
    """Factory para criar provider de SMS."""
    
    providers = {
        "twilio": TwilioSMSProvider,
        "zenvia": ZenviaSMSProvider,
        "sns": AmazonSNSSMSProvider,
    }
    
    @classmethod
    def create(cls, config: SMSConfig) -> SMSProvider:
        provider_cls = cls.providers.get(config.provider)
        if not provider_cls:
            raise ValueError(f"SMS provider desconhecido: {config.provider}")
        return provider_cls(config)


class SMSProvider(ABC):
    """Interface de SMS provider."""
    
    @abstractmethod
    async def send(self, to: str, body: str) -> Dict:
        """Envia SMS. Retorna { message_id, status }."""
    
    @abstractmethod
    async def get_status(self, message_id: str) -> str:
        """Consulta status de entrega."""
    
    @abstractmethod
    async def check_health(self) -> bool:
        """Verifica se o provider está acessível."""
```

### 5.3 API Endpoints SMS

```yaml
POST /api/v1/sms/send
  Description: Envia SMS (para testes/admin)
  Auth: Keycloak (admin, system)
  Body:
    to: str                    # Número (+55...)
    body: str                  # Texto (max 160 chars, ou concatenado)
  Response 200: { message_id: str, status: str, segments: int }

GET /api/v1/sms/status/{message_id}
  Description: Status de entrega do SMS
  Auth: Keycloak (admin)
  Response 200: { message_id: str, status: str, delivered_at: Optional[str] }

# ── Webhook do provider ──
POST /api/v1/webhooks/sms
  Description: Recebe status updates do provider de SMS
  Auth: Provider-specific
  Response 200: "ok"
```

### 5.4 Testes SMS

```
test_sms/
├── test_dispatcher.py
│   ├── test_send_short_message
│   ├── test_send_long_message_concatenated
│   ├── test_truncate_if_no_concat
│   ├── test_format_phone_e164
│   ├── test_invalid_phone_rejected
│   └── test_health_check
├── test_providers/
│   ├── test_twilio_provider.py
│   │   ├── test_send_via_twilio
│   │   ├── test_twilio_status_callback
│   │   └── test_twilio_auth
│   ├── test_zenvia_provider.py
│   │   └── test_send_via_zenvia
│   └── test_sns_provider.py
│       └── test_send_via_sns
└── test_webhook.py
    ├── test_twilio_status_webhook
    └── test_zenvia_status_webhook
```

---

## 6. EF-COM-033 — Email

### 6.1 Descrição Funcional

Canal para comunicações formais e detalhadas:

1. **Relatórios** (resultados de exames, resumos)
2. **Confirmações** (agendamento, teleconsulta)
3. **Newsletters** (educação em saúde)
4. **Escalações** (para coordenadores/gestores)

### 6.2 EmailDispatcher

```python
class EmailDispatcher(IChannelDispatcher):
    """Dispatcher para envio de email via SMTP."""
    
    def __init__(self, config: EmailConfig):
        self._config = config
        self._template_engine = EmailTemplateEngine(config.template_dir)
    
    @property
    def channel_name(self) -> str:
        return "email"
    
    @property
    def display_name(self) -> str:
        return "Email"
    
    async def is_available(self) -> bool:
        """Testa conexão SMTP."""
    
    async def send(
        self, 
        recipient: ResolvedRecipient, 
        content: RenderedContent, 
        metadata: Dict
    ) -> DispatchResult:
        """
        Envia email.
        
        Lógica:
        1. Se content.template_name existe → renderizar HTML template
        2. Montar email com aiosmtplib:
           - From: intellicare@gsi.srv.br
           - To: recipient.email
           - Subject: content.subject ou gerar do template
           - Body: HTML renderizado + plaintext fallback
           - Headers: Reply-To, X-IntelliCare-Alert-Id, etc.
        3. Enviar via SMTP (TLS)
        4. Registrar Message-ID para tracking
        """
    
    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        """Email não tem delivery tracking nativo. Usa pixel tracking se habilitado."""
        return DeliveryStatus.SENT
    
    async def get_health(self) -> ChannelHealth:
        """Testa conexão SMTP."""
    
    async def supports_read_receipt(self) -> bool:
        return False  # Sem read receipt confiável
    
    async def supports_rich_content(self) -> bool:
        return True  # HTML completo


class EmailConfig(BaseModel):
    """Configuração de email."""
    
    # SMTP
    smtp_host: str = "smtp.gsi.srv.br"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_username: str = "intellicare@gsi.srv.br"
    smtp_password: str
    
    # Remetente
    from_email: str = "intellicare@gsi.srv.br"
    from_name: str = "IntelliCare - Plataforma de Saúde"
    reply_to: str = "noreply@gsi.srv.br"
    
    # Templates
    template_dir: str = "templates/email"
    
    # Pixel tracking
    enable_tracking_pixel: bool = False   # Implicações de privacidade
    
    # Rate limiting
    max_emails_per_minute: int = 60
```

### 6.3 Templates HTML de Email

```python
class EmailTemplateEngine:
    """Renderiza templates de email HTML com Jinja2."""
    
    def __init__(self, template_dir: str):
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=True
        )
    
    def render(self, template_name: str, context: Dict) -> EmailRendered:
        """
        Renderiza template HTML + plaintext.
        
        Retorna:
        EmailRendered(
            subject: str,
            html_body: str,       # HTML completo com inline CSS
            text_body: str,       # Versão plaintext
        )
        """

# Template base: templates/email/base.html
BASE_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; }
        .header { background-color: #1976D2; color: white; padding: 20px; text-align: center; }
        .header img { height: 40px; }
        .header h1 { font-size: 18px; margin: 10px 0 0; }
        .content { padding: 30px; color: #333333; line-height: 1.6; }
        .alert-critical { border-left: 4px solid #D32F2F; padding-left: 16px; }
        .alert-high { border-left: 4px solid #F57C00; padding-left: 16px; }
        .alert-medium { border-left: 4px solid #FDD835; padding-left: 16px; }
        .button { display: inline-block; padding: 12px 24px; background-color: #1976D2; 
                   color: white; text-decoration: none; border-radius: 4px; margin: 16px 0; }
        .footer { background-color: #f5f5f5; padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .metrics-table { width: 100%; border-collapse: collapse; margin: 16px 0; }
        .metrics-table th, .metrics-table td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }
        .metrics-table th { background-color: #f5f5f5; font-weight: 600; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }
        .badge-critical { background: #FFEBEE; color: #D32F2F; }
        .badge-high { background: #FFF3E0; color: #E65100; }
        .badge-normal { background: #E8F5E9; color: #2E7D32; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>IntelliCare</h1>
            <p style="margin:0;font-size:12px;">Plataforma de Saúde Inteligente</p>
        </div>
        <div class="content">
            {% block content %}{% endblock %}
        </div>
        <div class="footer">
            <p>IntelliCare &copy; 2026 — Plataforma de Saúde Inteligente</p>
            <p>Este email foi gerado automaticamente. Não responda diretamente.</p>
            {% if unsubscribe_url %}
            <p><a href="{{ unsubscribe_url }}">Gerenciar preferências de notificação</a></p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# Exemplo: templates/email/clinical_alert.html
CLINICAL_ALERT_EMAIL = """
{% extends "base.html" %}

{% block content %}
<div class="alert-{{ severity_class }}">
    <h2>🚨 Alerta Clínico — {{ severity }}</h2>
    <p><strong>Paciente:</strong> {{ patient_name }} ({{ patient_id }})</p>
    <p><strong>Alerta:</strong> {{ alert_description }}</p>
    <p><strong>Valor:</strong> {{ alert_value }}</p>
    <p><strong>Data/Hora:</strong> {{ alert_timestamp }}</p>
</div>

<a href="{{ portal_url }}" class="button">Ver no Portal</a>

{% if lab_results %}
<h3>Últimos Exames</h3>
<table class="metrics-table">
    <tr>
        <th>Exame</th>
        <th>Resultado</th>
        <th>Referência</th>
        <th>Status</th>
    </tr>
    {% for result in lab_results %}
    <tr>
        <td>{{ result.name }}</td>
        <td>{{ result.value }}</td>
        <td>{{ result.reference }}</td>
        <td><span class="badge badge-{{ result.status_class }}">{{ result.status }}</span></td>
    </tr>
    {% endfor %}
</table>
{% endif %}

<p>Por favor, verifique o caso e tome as providências necessárias.</p>
{% endblock %}
"""

# templates/email/teleconsult_confirmation.html
# templates/email/daily_report.html
# templates/email/quality_report.html
# templates/email/escalation.html
```

### 6.4 API Endpoints Email

```yaml
POST /api/v1/email/send
  Description: Envia email (para testes/admin)
  Auth: Keycloak (admin, system)
  Body:
    to: str                    # Email do destinatário
    subject: str
    template_name: Optional[str]  # Se usar template
    template_params: Optional[Dict]
    html_body: Optional[str]      # Se HTML direto
    text_body: Optional[str]      # Plaintext fallback
  Response 200: { message_id: str, status: str }

GET /api/v1/email/templates
  Description: Lista templates de email disponíveis
  Auth: Keycloak (admin)
  Response 200: List[{ name, subject_template, description }]

POST /api/v1/email/test
  Description: Envia email de teste
  Auth: Keycloak (admin)
  Body: { to: str }
  Response 200: { sent: true }
```

### 6.5 Testes Email

```
test_email/
├── test_dispatcher.py
│   ├── test_send_html_email
│   ├── test_send_with_template
│   ├── test_send_with_plaintext_fallback
│   ├── test_missing_smtp_config_unavailable
│   ├── test_rate_limit_respected
│   └── test_health_check_smtp_connection
├── test_template_engine.py
│   ├── test_render_clinical_alert
│   ├── test_render_teleconsult_confirmation
│   ├── test_render_daily_report
│   ├── test_render_with_lab_results_table
│   ├── test_unsubscribe_link_present
│   └── test_inline_css
└── test_api.py
    ├── test_send_email_endpoint
    ├── test_list_templates
    └── test_send_test_email
```

---

## 7. SCHEMA SQL (Compartilhado)

```sql
-- Migration: 2026_02_15_0004_create_external_channels_tables.py
-- Schema: comunicacao_operacional

-- Push subscriptions
CREATE TABLE comunicacao_operacional.push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(200) NOT NULL,
    subscription_type VARCHAR(20) NOT NULL,    -- "web" | "fcm"
    
    -- VAPID
    endpoint TEXT,
    p256dh_key TEXT,
    auth_key TEXT,
    
    -- FCM
    fcm_token VARCHAR(500),
    
    -- Metadata
    device_name VARCHAR(200),
    user_agent TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    last_used_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_push_user ON comunicacao_operacional.push_subscriptions(user_id);
CREATE INDEX idx_push_active ON comunicacao_operacional.push_subscriptions(active);

-- WhatsApp sessions (janela de 24h)
CREATE TABLE comunicacao_operacional.whatsapp_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(50) NOT NULL,
    patient_id VARCHAR(200),
    
    -- Janela de sessão
    session_started_at TIMESTAMPTZ NOT NULL,       -- Quando paciente enviou última msg
    session_expires_at TIMESTAMPTZ NOT NULL,        -- +24h
    active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Contadores
    messages_sent INT NOT NULL DEFAULT 0,
    messages_received INT NOT NULL DEFAULT 0,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_wa_session_phone ON comunicacao_operacional.whatsapp_sessions(phone_number);
CREATE INDEX idx_wa_session_active ON comunicacao_operacional.whatsapp_sessions(active, session_expires_at);

-- Mensagens de canais externos (log unificado)
CREATE TABLE comunicacao_operacional.external_message_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(20) NOT NULL,                  -- "push" | "whatsapp" | "sms" | "email"
    direction VARCHAR(10) NOT NULL,                -- "outbound" | "inbound"
    
    -- Destinatário
    recipient_id VARCHAR(200),                     -- user_id ou patient_id
    recipient_address VARCHAR(300),                -- phone, email, etc.
    
    -- Conteúdo
    template_name VARCHAR(200),
    message_summary VARCHAR(500),                   -- Truncado para log (sem PII detalhado)
    
    -- Provider
    provider_message_id VARCHAR(300),              -- ID do provider (Twilio SID, Meta msg ID, etc.)
    provider_status VARCHAR(50),                    -- Status do provider
    
    -- Status IntelliCare
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- "pending" | "sent" | "delivered" | "read" | "failed"
    error_message TEXT,
    
    -- Rastreamento
    delivery_result_id UUID,                        -- FK para delivery_results (D1)
    
    -- Timestamps
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ext_msg_channel ON comunicacao_operacional.external_message_log(channel);
CREATE INDEX idx_ext_msg_recipient ON comunicacao_operacional.external_message_log(recipient_id);
CREATE INDEX idx_ext_msg_status ON comunicacao_operacional.external_message_log(status);
CREATE INDEX idx_ext_msg_provider ON comunicacao_operacional.external_message_log(provider_message_id);
CREATE INDEX idx_ext_msg_delivery ON comunicacao_operacional.external_message_log(delivery_result_id);
CREATE INDEX idx_ext_msg_created ON comunicacao_operacional.external_message_log(created_at);

-- Configurações de canal por tenant/unidade (para multi-tenancy futuro)
CREATE TABLE comunicacao_operacional.channel_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(20) NOT NULL,                  -- "push" | "whatsapp" | "sms" | "email"
    config_key VARCHAR(200) NOT NULL,
    config_value TEXT NOT NULL,
    encrypted BOOLEAN NOT NULL DEFAULT FALSE,      -- Se valor está criptografado
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(channel, config_key)
);
```

---

## 8. ESTRUTURA DE CÓDIGO

```
comunicacao/
├── channels/
│   ├── __init__.py
│   ├── push/
│   │   ├── __init__.py
│   │   ├── dispatcher.py             # PushDispatcher
│   │   ├── vapid_service.py          # VAPIDPushService
│   │   ├── fcm_service.py            # FCMPushService
│   │   ├── config.py                 # PushConfig, VAPIDConfig, FCMConfig
│   │   └── models.py                 # PushSubscription, PushPayload
│   ├── whatsapp/
│   │   ├── __init__.py
│   │   ├── dispatcher.py             # WhatsAppDispatcher
│   │   ├── client.py                 # WhatsAppClientAPI (Meta Graph API)
│   │   ├── webhook_handler.py        # WhatsAppWebhookHandler
│   │   ├── config.py                 # WhatsAppConfig
│   │   ├── templates.py              # WHATSAPP_TEMPLATES
│   │   └── models.py                 # WhatsAppMessage, WhatsAppSession
│   ├── sms/
│   │   ├── __init__.py
│   │   ├── dispatcher.py             # SMSDispatcher
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # SMSProvider ABC
│   │   │   ├── twilio.py             # TwilioSMSProvider
│   │   │   ├── zenvia.py             # ZenviaSMSProvider
│   │   │   └── sns.py                # AmazonSNSSMSProvider
│   │   ├── config.py                 # SMSConfig
│   │   └── models.py
│   └── email/
│       ├── __init__.py
│       ├── dispatcher.py             # EmailDispatcher
│       ├── template_engine.py        # EmailTemplateEngine
│       ├── config.py                 # EmailConfig
│       └── models.py
├── templates/
│   └── email/
│       ├── base.html                 # Template base
│       ├── clinical_alert.html
│       ├── teleconsult_confirmation.html
│       ├── daily_report.html
│       ├── quality_report.html
│       └── escalation.html
├── api/
│   ├── push_routes.py
│   ├── whatsapp_routes.py
│   ├── sms_routes.py
│   ├── email_routes.py
│   └── webhook_routes.py
└── tests/
    ├── test_push/
    ├── test_whatsapp/
    ├── test_sms/
    └── test_email/
```

---

## 9. CONFIGURAÇÃO (Variáveis de Ambiente)

```bash
# ── Push ──
VAPID_PRIVATE_KEY=<base64url_encoded>
VAPID_PUBLIC_KEY=<base64url_encoded>
VAPID_SUBJECT=mailto:intellicare@gsi.srv.br

FCM_ENABLED=false
FCM_PROJECT_ID=<firebase_project_id>
FCM_SERVICE_ACCOUNT_KEY=/config/fcm-service-account.json

# ── WhatsApp ──
WHATSAPP_ENABLED=true
WHATSAPP_GRAPH_API_VERSION=v18.0
WHATSAPP_PHONE_NUMBER_ID=<meta_phone_number_id>
WHATSAPP_BUSINESS_ACCOUNT_ID=<waba_id>
WHATSAPP_ACCESS_TOKEN=<permanent_access_token>
WHATSAPP_WEBHOOK_VERIFY_TOKEN=<random_token>

# ── SMS ──
SMS_ENABLED=true
SMS_PROVIDER=twilio                    # twilio | zenvia | sns

TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_FROM_NUMBER=+55XXXXXXXXXXX

# Ou Zenvia:
# ZENVIA_API_TOKEN=<token>
# ZENVIA_FROM=intellicare

# ── Email ──
EMAIL_ENABLED=true
SMTP_HOST=smtp.gsi.srv.br
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=intellicare@gsi.srv.br
SMTP_PASSWORD=<password>
EMAIL_FROM=intellicare@gsi.srv.br
EMAIL_FROM_NAME=IntelliCare - Plataforma de Saúde
EMAIL_REPLY_TO=noreply@gsi.srv.br
EMAIL_TEMPLATE_DIR=templates/email
```

---

## 10. PRIORIDADE DE IMPLEMENTAÇÃO

```
Sprint S4:
  1. WhatsApp (canal primário para pacientes)
  2. Push (canal primário para profissionais fora do RC)

Sprint S5:
  3. SMS (fallback do WhatsApp)
  4. Email (comunicação formal)
```

---

## 11. ENTREGÁVEIS DO DEV

1. **Especificação Técnica**: Diagramas de sequência para cada canal
2. **Plano de Implementação**: WhatsApp → Push → SMS → Email
3. **Código**: 4 dispatchers com testes ≥ 80%
4. **Migrations**: Alembic para todas as tabelas
5. **Templates de Email**: HTML responsive para os 5 tipos
6. **Templates WhatsApp**: Payload JSON pronto para submissão à Meta
7. **Script de configuração**: Geração de chaves VAPID, setup de webhooks
8. **Documentação**: README + guia de configuração de cada provider

**Prazo estimado**: 2 sprints (S4 + S5)
