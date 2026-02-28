# Modelos de Dados - Canais Externos (D4)

## Visão Geral

Este documento descreve os modelos de dados (Pydantic e SQLAlchemy) utilizados pelos canais externos.

---

## 1. Modelos Compartilhados

### 1.1. ExternalMessageLog

**Descrição**: Log unificado de todas as mensagens externas.

**Tabela**: `comunicacao_operacional.external_message_log`

**Colunas**:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | ID único |
| channel | VARCHAR(50) | Canal (push, whatsapp, sms, email) |
| direction | VARCHAR(20) | Direção (outbound, inbound) |
| intent_id | VARCHAR(255) | ID do intent (D1) |
| correlation_id | VARCHAR(255) | ID de correlação |
| recipient_id | VARCHAR(255) | ID do destinatário |
| recipient_type | VARCHAR(50) | Tipo (user_id, phone, email, device_id) |
| provider | VARCHAR(50) | Provider (vapid, fcm, twilio, zenvia, smtp) |
| provider_message_id | VARCHAR(255) | ID na API externa |
| status | VARCHAR(50) | Status (pending, sent, delivered, read, failed) |
| message_content | JSONB | Conteúdo da mensagem |
| sent_at | TIMESTAMP | Data/hora de envio |
| delivered_at | TIMESTAMP | Data/hora de entrega |
| read_at | TIMESTAMP | Data/hora de leitura |
| failed_at | TIMESTAMP | Data/hora de falha |
| error_code | VARCHAR(100) | Código de erro |
| error_message | TEXT | Mensagem de erro |
| extra_metadata | JSONB | Metadados adicionais |

**Índices**:
- `idx_external_message_log_channel` (channel)
- `idx_external_message_log_intent_id` (intent_id)
- `idx_external_message_log_recipient_id` (recipient_id)
- `idx_external_message_log_status` (status)
- `idx_external_message_log_sent_at` (sent_at)
- `idx_external_message_log_provider_message_id` (provider_message_id)

**Modelo Pydantic**:
```python
class ExternalMessageLog(BaseModel):
    id: UUID
    channel: str
    direction: str
    intent_id: str | None
    correlation_id: str | None
    recipient_id: str
    recipient_type: str
    provider: str | None
    provider_message_id: str | None
    status: ExternalMessageStatus
    message_content: dict
    sent_at: datetime | None
    delivered_at: datetime | None
    read_at: datetime | None
    failed_at: datetime | None
    error_code: str | None
    error_message: str | None
    extra_metadata: dict | None
```

---

### 1.2. PushSubscription

**Descrição**: Inscrições de push notifications por usuário/dispositivo.

**Tabela**: `comunicacao_operacional.push_subscriptions`

**Colunas**:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | ID único |
| user_id | VARCHAR(255) | ID do usuário |
| device_id | VARCHAR(255) | ID do dispositivo |
| provider | VARCHAR(50) | Provider (vapid, fcm) |
| subscription_data | JSONB | Dados da inscrição (endpoint, keys) |
| fcm_token | VARCHAR(255) | Token FCM (se aplicável) |
| user_agent | TEXT | User agent do navegador |
| ip_address | VARCHAR(45) | IP do dispositivo |
| active | BOOLEAN | Ativo/inativo |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Data de atualização |

**Índices**:
- `idx_push_subscriptions_user_id` (user_id)
- `idx_push_subscriptions_device_id` (device_id)

**Modelo Pydantic**:
```python
class PushSubscription(BaseModel):
    id: UUID
    user_id: str
    device_id: str
    provider: str
    subscription_data: dict
    fcm_token: str | None
    user_agent: str | None
    ip_address: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
```

---

### 1.3. WhatsAppSession

**Descrição**: Janelas de 24h do WhatsApp para mensagens de texto.

**Tabela**: `comunicacao_operacional.whatsapp_sessions`

**Colunas**:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | ID único |
| phone_number | VARCHAR(20) | Número de telefone |
| session_start | TIMESTAMP | Início da janela |
| session_end | TIMESTAMP | Fim da janela |
| last_message_at | TIMESTAMP | Última mensagem |
| last_message_id | VARCHAR(255) | ID da última mensagem |
| message_count | INTEGER | Contador de mensagens |
| active | BOOLEAN | Sessão ativa |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Data de atualização |

**Índices**:
- `idx_whatsapp_sessions_phone_number` (phone_number)
- `idx_whatsapp_sessions_active` (active)

**Modelo Pydantic**:
```python
class WhatsAppSession(BaseModel):
    id: UUID
    phone_number: str
    session_start: datetime
    session_end: datetime
    last_message_at: datetime
    last_message_id: str | None
    message_count: int
    active: bool
    created_at: datetime
    updated_at: datetime
```

---

### 1.4. ChannelConfig

**Descrição**: Configuração por canal/tenant.

**Tabela**: `comunicacao_operacional.channel_configs`

**Colunas**:
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | ID único |
| channel | VARCHAR(50) | Canal (push, whatsapp, sms, email) |
| tenant_id | VARCHAR(255) | ID do tenant (opcional) |
| config_data | JSONB | Dados de configuração |
| enabled | BOOLEAN | Habilitado/desabilitado |
| created_at | TIMESTAMP | Data de criação |
| updated_at | TIMESTAMP | Data de atualização |

**Constraints**:
- UNIQUE (channel, tenant_id)

**Modelo Pydantic**:
```python
class ChannelConfig(BaseModel):
    id: UUID
    channel: str
    tenant_id: str | None
    config_data: dict
    enabled: bool
    created_at: datetime
    updated_at: datetime
```

---

## 2. Modelos de Push Notifications

### 2.1. PushMessage

```python
class PushMessage(BaseModel):
    title: str
    body: str
    data: dict[str, Any] | None = None
    icon: str | None = None
    badge: str | None = None
    image: str | None = None
    tag: str | None = None
    requireInteraction: bool = False
    silent: bool = False
    timestamp: int | None = None
```

### 2.2. PushSendRequest

```python
class PushSendRequest(BaseModel):
    user_id: str
    title: str
    body: str
    data: dict[str, Any] | None = None
    provider: str | None = None  # "vapid" ou "fcm"
    device_id: str | None = None  # Opcional, envia para todos se None
```

### 2.3. PushSendResponse

```python
class PushSendResponse(BaseModel):
    message_id: str
    status: str  # "sent" ou "failed"
    provider: str
    recipients_count: int
    errors: list[str] = []
```

---

## 3. Modelos de WhatsApp

### 3.1. WhatsAppMessage

```python
class WhatsAppMessage(BaseModel):
    to: str  # Número no formato internacional (+5511999999999)
    type: str  # "text" ou "template"
    text: str | None = None  # Para mensagens de texto
    template_name: str | None = None  # Para templates
    template_params: dict[str, str] | None = None
```

### 3.2. WhatsAppTemplateInfo

```python
class WhatsAppTemplateInfo(BaseModel):
    name: str
    language: str
    status: str  # "approved", "pending", "rejected"
    category: str  # "MARKETING", "UTILITY", "AUTHENTICATION"
    params: list[str]  # Lista de parâmetros
```

---

## 4. Modelos de SMS

### 4.1. SMSMessage

```python
class SMSMessage(BaseModel):
    to: str  # Número no formato internacional (+5511999999999)
    text: str  # Máximo 160 caracteres
    from_number: str | None = None
```

### 4.2. SMSSendRequest

```python
class SMSSendRequest(BaseModel):
    to: str
    text: str
    provider: str | None = None  # "twilio", "zenvia", "sns"
```

### 4.3. SMSStatusUpdate

```python
class SMSStatusUpdate(BaseModel):
    message_id: str
    status: str  # "queued", "sent", "delivered", "failed"
    error_code: str | None = None
    error_message: str | None = None
    timestamp: datetime
```

---

## 5. Modelos de Email

### 5.1. EmailMessage

```python
class EmailMessage(BaseModel):
    to: list[str]
    subject: str
    body_html: str | None = None
    body_text: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    attachments: list[EmailAttachment] | None = None
```

### 5.2. EmailAttachment

```python
class EmailAttachment(BaseModel):
    filename: str
    content: bytes
    content_type: str
    content_id: str | None = None  # Para inline images
```

### 5.3. EmailSendRequest

```python
class EmailSendRequest(BaseModel):
    to: list[str]
    subject: str
    body_html: str | None = None
    body_text: str | None = None
    template_name: str | None = None
    template_data: dict[str, Any] | None = None
    attachments: list[EmailAttachment] | None = None
```

---

## 6. Enums

### 6.1. ExternalMessageStatus

```python
class ExternalMessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
```

### 6.2. ExternalMessageDirection

```python
class ExternalMessageDirection(str, Enum):
    OUTBOUND = "outbound"
    INBOUND = "inbound"
```

---

## Próximos Passos

1. Revisar modelos conforme necessidades
2. Adicionar validações customizadas
3. Criar migrations para novas colunas
4. Documentar relacionamentos entre modelos

