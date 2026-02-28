# Integração D3 (Jitsi) ↔ D1 (Routing Engine)

## 📋 Visão Geral

O **D3 - Teleconsulta/Video** integra-se com o **D1 - Engine de Roteamento** através do **JitsiDispatcher**, que implementa o protocolo `ChannelDispatcher`.

---

## 🔌 Arquitetura de Integração

```
┌─────────────────────────────────────────────────────────────┐
│                    D1 - Routing Engine                      │
│                                                             │
│  ┌──────────────┐      ┌──────────────────┐               │
│  │ RoutingEngine│─────▶│DispatcherManager │               │
│  └──────────────┘      └────────┬─────────┘               │
│                                  │                          │
│                                  │ get_dispatcher("jitsi") │
│                                  ▼                          │
│                        ┌──────────────────┐                │
│                        │ JitsiDispatcher  │◀───────────────┼─── D3
│                        └──────────────────┘                │
│                                  │                          │
└──────────────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │   RoomService    │
                        └──────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │   JitsiClient    │
                        └──────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │  Jitsi Meet API  │
                        └──────────────────┘
```

---

## 🎯 Protocolo ChannelDispatcher

O `JitsiDispatcher` implementa todos os 7 métodos obrigatórios do protocolo:

### 1. `send(message: ChannelMessage) -> DispatchResult`

**Responsabilidade**: Enviar convite de teleconsulta

**Fluxo**:
1. Extrai metadados da mensagem (`room_type`, `scheduled_start`, etc.)
2. Cria sala Jitsi (ou usa existente se `room_id` fornecido)
3. Adiciona participante com token JWT
4. Retorna URL + token no `metadata`

**Exemplo**:
```python
message = ChannelMessage(
    intent_id="intent-123",
    correlation_id="corr-456",
    channel="jitsi",
    recipient=ResolvedRecipient(
        recipient_id="patient-789",
        recipient_type="patient",
        metadata={"name": "João Silva"},
    ),
    content=RenderedContent(
        format="markdown",
        body="Convite para teleconsulta",
        title="Teleconsulta - Dr. Maria",
    ),
    metadata={
        "room_type": "teleconsulta",
        "scheduled_start": "2026-02-20T10:00:00Z",
        "scheduled_end": "2026-02-20T11:00:00Z",
        "patient_id": "patient-789",
        "role": "participant",
    },
)

result = await jitsi_dispatcher.send(message)

# result.metadata contém:
# {
#     "room_id": "uuid-da-sala",
#     "room_name": "intellicare-teleconsulta-abc123",
#     "room_url": "https://meet.gsi.srv.br/intellicare-teleconsulta-abc123?jwt=...",
#     "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#     "token_expires_at": "2026-02-20T11:00:00Z",
#     "participant_id": "uuid-do-participante",
# }
```

### 2. `get_status(channel_message_id: str) -> DeliveryStatus`

**Responsabilidade**: Consultar status de entrega (participante)

**Mapeamento**:
- `SENT`: Convite enviado, participante não entrou ainda
- `READ`: Participante entrou na sala (joined_at preenchido)
- `DELIVERED`: Participante já saiu da sala (left_at preenchido)
- `UNKNOWN`: Participante não encontrado

### 3. `cancel(channel_message_id: str) -> bool`

**Responsabilidade**: Cancelar convite (remover participante)

**Retorna**: `True` se participante removido, `False` se não encontrado

### 4. `health_check() -> ChannelHealth`

**Responsabilidade**: Verificar saúde do canal Jitsi

**Validações**:
- Configuração válida (`JITSI_BASE_URL`, `JITSI_APP_ID`, `JITSI_APP_SECRET`)
- (Opcional) Ping no servidor Jitsi

### 5. `test_send(recipient: ResolvedRecipient) -> DispatchResult`

**Responsabilidade**: Enviar mensagem de teste

**Uso**: Diagnóstico e validação de configuração

### 6. `get_capabilities() -> ChannelCapabilities`

**Responsabilidade**: Retornar capacidades do canal

**Capacidades Jitsi**:
- `supports_read_receipt`: ✅ True (sabemos se participante entrou)
- `supports_rich_content`: ✅ True (vídeo, áudio, chat, screen sharing)
- `supports_attachments`: ❌ False (não enviamos anexos no convite)
- `supports_interactive`: ✅ True (Jitsi é altamente interativo)

### 7. `validate_recipient(recipient: ResolvedRecipient) -> RecipientValidation`

**Responsabilidade**: Validar destinatário

**Nota**: Para Jitsi, qualquer `recipient_id` é válido (não precisamos de email, telefone, etc.)

---

## 🔧 Registro no DispatcherManager

O `JitsiDispatcher` é registrado automaticamente no startup da aplicação:

```python
# comunicacao/api/app.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ...
    dispatcher_manager = DispatcherManager()
    
    # Registrar JitsiDispatcher
    from comunicacao.jitsi import JitsiConfig, JitsiDispatcher
    
    jitsi_config = JitsiConfig.from_env()
    async with get_db_session() as db:
        jitsi_dispatcher = JitsiDispatcher(db=db, config=jitsi_config)
        dispatcher_manager.register(jitsi_dispatcher)
    
    # ...
```

---

## 📝 Uso via Routing Engine

### Exemplo 1: Enviar Convite de Teleconsulta

```python
from comunicacao.routing.models import CommunicationIntentCreate, Priority

intent = CommunicationIntentCreate(
    recipient_id="patient-123",
    recipient_type="patient",
    priority=Priority.MEDIUM,
    template_id="teleconsult_invite",
    params={
        "doctor_name": "Dr. Maria Silva",
        "specialty": "Cardiologia",
        "scheduled_start": "2026-02-20T10:00:00Z",
        "scheduled_end": "2026-02-20T11:00:00Z",
    },
    metadata={
        "room_type": "teleconsulta",
        "patient_id": "patient-123",
    },
)

# Routing Engine automaticamente:
# 1. Renderiza template "teleconsult_invite" para canal "jitsi"
# 2. Chama JitsiDispatcher.send()
# 3. Cria sala Jitsi
# 4. Adiciona participante
# 5. Retorna URL + token

result = await routing_engine.send_intent(intent)
```

### Exemplo 2: Template de Convite

```yaml
# Template: teleconsult_invite

channel_variants:
  jitsi:
    format: "markdown"
    title: "Teleconsulta - {{ doctor_name }}"
    body: |
      Olá!
      
      Você tem uma teleconsulta agendada:
      
      **Médico**: {{ doctor_name }}
      **Especialidade**: {{ specialty }}
      **Data/Hora**: {{ scheduled_start | format_datetime }}
      
      Clique no link abaixo para entrar na sala:
      {{ room_url }}
```

---

## 🔄 Fluxo Completo

```
1. Wanda cria intent de teleconsulta
   ↓
2. RoutingEngine recebe intent
   ↓
3. RuleMatcher seleciona regra (canal: jitsi)
   ↓
4. TemplateRenderer renderiza template
   ↓
5. DispatcherManager.dispatch("jitsi", ...)
   ↓
6. JitsiDispatcher.send()
   ├─ RoomService.create_room()
   ├─ RoomService.add_participant()
   └─ JitsiClient.generate_jwt_token()
   ↓
7. DispatchResult com room_url + jwt_token
   ↓
8. RoutingEngine persiste DeliveryResult
   ↓
9. Paciente recebe URL via email/SMS/push
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# Jitsi Configuration
JITSI_BASE_URL=https://meet.gsi.srv.br
JITSI_APP_ID=intellicare
JITSI_APP_SECRET=your-secret-here
JITSI_DEFAULT_ROOM_DURATION=60
JITSI_MAX_PARTICIPANTS=10
JITSI_ENABLE_RECORDING=true
JITSI_ENABLE_LOBBY=true
JITSI_ENABLE_CHAT=true
JITSI_ENABLE_SCREEN_SHARING=true
JITSI_MODERATOR_PASSWORD=optional-password
```

---

## 📊 Métricas

O `JitsiDispatcher` automaticamente registra métricas via `CommunicationMetrics`:

- `communication_messages_sent_total{channel="jitsi"}`: Total de convites enviados
- `communication_messages_failed_total{channel="jitsi"}`: Total de falhas
- `communication_dispatch_duration_seconds{channel="jitsi"}`: Latência de envio

---

## 🧪 Testes

### Teste de Health Check

```bash
curl http://localhost:8005/api/v1/channels/jitsi/health
```

### Teste de Envio

```bash
curl -X POST http://localhost:8005/api/v1/channels/jitsi/test \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": "test-user",
    "recipient_type": "patient"
  }'
```

---

## 🔗 Referências

- **D1 - Engine de Roteamento**: `docs/01_engine_roteamento/`
- **Jitsi JWT Tokens**: https://github.com/jitsi/lib-jitsi-meet/blob/master/doc/tokens.md
- **ChannelDispatcher Protocol**: `comunicacao/dispatchers/base.py`

