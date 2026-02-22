# Domínio 2 — Integração Rocket.Chat
## Especificação Funcional Detalhada

**Identificadores**: EF-COM-010, EF-COM-011, EF-COM-012  
**Prioridade Global**: CRÍTICA  
**Sprint**: S2–S3  
**Dependências**: D1 (interface IChannelDispatcher, DispatcherManager)  
**Dependentes**: D3 (Teleconsulta usa canais RC), D7 (Dashboard)

---

## 1. OBJETIVO

Integrar o Rocket.Chat como plataforma de comunicação corporativa da equipe de saúde, incluindo: envio automatizado de mensagens, organização de canais por equipe/paciente, sincronização de usuários via Keycloak, e bot assistente `@intellicare` com comandos clínicos.

**Estado Atual**: Rocket.Chat v7.13.2 operacional em `https://rocket.gsi.srv.br` com Keycloak SSO ativo. Nenhuma integração programática com o IntelliCare ainda implementada.

---

## 2. CONTEXTO

```
┌────────────────────────────────────────────────────────┐
│                  ROCKET.CHAT (rocket.gsi.srv.br)       │
│                                                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ #alertas    │  │ #equipe-ubs1 │  │ #caso-P001   │  │
│  │  clínicos   │  │              │  │ (privado)    │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
│        ▲                 ▲                  ▲          │
│        │                 │                  │          │
│  ┌─────┴─────────────────┴──────────────────┴───────┐  │
│  │            @intellicare (Bot)                     │  │
│  └──────────────────────────────────────────────────┘  │
│                          ▲                             │
└──────────────────────────┼─────────────────────────────┘
                           │ REST API v1
┌──────────────────────────┼─────────────────────────────┐
│              intellicare-comunicacao                    │
│                          │                             │
│  ┌───────────────────────┴──────────────────────────┐  │
│  │           RocketChatDispatcher                    │  │
│  │ implements IChannelDispatcher                     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │         RocketChatUserSync                        │  │
│  │ Keycloak Event → Create/Update RC User           │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │         IntelliCareBot                            │  │
│  │ Webhook handler para comandos do @intellicare    │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

---

## 3. EF-COM-010 — Integração API Rocket.Chat

### 3.1 Descrição Funcional

O `RocketChatDispatcher` deve implementar `IChannelDispatcher` do Domínio 1 e fornecer acesso completo à API REST do Rocket.Chat v7.x para:

1. **Enviar mensagens** para canais públicos, grupos privados e DMs
2. **Criar canais** automaticamente (por equipe, paciente, tema)
3. **Gerenciar membros** de canais
4. **Enviar conteúdo rico** (attachments, botões, formatação Markdown)
5. **Receber eventos** via Webhooks
6. **Health check** contínuo

### 3.2 RocketChatDispatcher

```python
class RocketChatDispatcher(IChannelDispatcher):
    """Dispatcher para Rocket.Chat API v1."""
    
    def __init__(self, config: RocketChatConfig):
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_token: Optional[str] = None
        self._user_id: Optional[str] = None
    
    @property
    def channel_name(self) -> str:
        return "rocketchat"
    
    @property
    def display_name(self) -> str:
        return "Rocket.Chat"
    
    async def is_available(self) -> bool:
        """Verifica se RC está respondendo e bot está autenticado."""
    
    async def send(
        self, 
        recipient: ResolvedRecipient, 
        content: RenderedContent, 
        metadata: Dict
    ) -> DispatchResult:
        """
        Envia mensagem via RC API.
        
        Lógica:
        1. Se recipient tem channel_specific_id (RC room_id) → enviar para room
        2. Se recipient é profissional → enviar DM ou para canal da equipe
        3. Se recipient é paciente → enviar para #caso-{patient_id}
        4. Formatar como markdown com attachments se presente
        """
    
    async def check_delivery_status(self, channel_message_id: str) -> DeliveryStatus:
        """Consulta se mensagem foi lida via RC API."""
    
    async def get_health(self) -> ChannelHealth:
        """Retorna saúde com latência e versão do RC."""
    
    async def supports_read_receipt(self) -> bool:
        return True  # RC suporta read receipts
    
    async def supports_rich_content(self) -> bool:
        return True  # RC suporta attachments, botões
```

### 3.3 RocketChatConfig

```python
class RocketChatConfig(BaseModel):
    """Configuração do Rocket.Chat."""
    
    url: str = "https://rocket.gsi.srv.br"
    bot_username: str = "intellicare-bot"
    bot_password: str                     # Senha do bot
    admin_user_id: Optional[str]          # Para operações admin
    admin_auth_token: Optional[str]       # Para operações admin
    
    # Timeouts
    connect_timeout: int = 10             # segundos
    request_timeout: int = 30             # segundos
    
    # Rate limiting
    max_requests_per_second: int = 10
    
    # Canais padrão
    default_alert_channel: str = "alertas-clinicos"
    default_team_channel_prefix: str = "equipe-"
    default_case_channel_prefix: str = "caso-"
    
    # Webhook
    webhook_token: Optional[str]          # Token para validar webhooks incoming
```

### 3.4 Serviço de Gerenciamento de Canais

```python
class RocketChatChannelService:
    """Gerencia canais no Rocket.Chat de acordo com a organização do IntelliCare."""
    
    async def ensure_default_channels(self) -> Dict[str, str]:
        """
        Cria canais padrão se não existirem:
        - #geral                    → Canal geral
        - #alertas-clinicos         → Todos os alertas
        - #teleconsultas            → Links e agendamentos
        - #educacao-saude           → Materiais educativos
        - #qualidade                → Discussões de indicadores
        
        Retorna: { "alertas-clinicos": "room_id_xxx", ... }
        """
    
    async def create_team_channel(
        self, 
        team_id: str, 
        team_name: str,
        unit_name: str,
        member_ids: List[str]
    ) -> str:
        """
        Cria canal de equipe: #equipe-{team_id}
        Adiciona todos os membros.
        Pina mensagem de boas-vindas com informações da equipe.
        Retorna: room_id
        """
    
    async def create_case_channel(
        self, 
        patient_id: str, 
        patient_name: str,
        team_member_ids: List[str]
    ) -> str:
        """
        Cria grupo privado para discussão de caso: #caso-{patient_id}
        Adiciona profissionais da equipe de cuidado.
        Pina resumo clínico do paciente (via Wanda).
        Retorna: room_id
        """
    
    async def get_channel_id(self, channel_name: str) -> Optional[str]:
        """Busca room_id por nome do canal."""
    
    async def add_member(self, room_id: str, user_id: str) -> bool:
        """Adiciona membro a um canal."""
    
    async def remove_member(self, room_id: str, user_id: str) -> bool:
        """Remove membro de um canal."""
    
    async def post_pinned_message(self, room_id: str, text: str) -> str:
        """Envia e pina mensagem em um canal."""
    
    async def list_team_channels(self) -> List[Dict]:
        """Lista todos os canais de equipe."""
    
    async def list_case_channels(self) -> List[Dict]:
        """Lista todos os canais de caso."""
```

### 3.5 Organização de Canais

```
Rocket.Chat
├── #geral                          ← Todos os profissionais
│   └── Propósito: Avisos gerais, comunicados institucionais
│
├── #alertas-clinicos               ← Médicos, enfermeiros, coordenadores
│   └── Propósito: Feed de alertas clínicos (formatados por template)
│   └── Filtrado: Mensagens com emoji por severidade (🚨 CRITICAL, ⚠️ HIGH, ℹ️ MEDIUM)
│
├── #teleconsultas                  ← Profissionais que fazem teleconsulta
│   └── Propósito: Agendamentos, links, lembretes
│
├── #educacao-saude                 ← Todos
│   └── Propósito: Materiais educativos, artigos, protocolos
│
├── #qualidade                      ← Coordenadores, gestores
│   └── Propósito: Indicadores Donabedian, discussões de melhoria
│
├── #equipe-ubs-centro              ← Membros da equipe UBS Centro
│   └── Propósito: Comunicação interna da equipe
│
├── #equipe-ubs-norte               ← Membros da equipe UBS Norte
│   └── ...
│
├── caso-P001 (grupo privado)       ← Equipe que cuida do paciente P001
│   └── Propósito: Discussão multidisciplinar, alertas do paciente
│   └── Pinned: Resumo clínico atualizado
│
└── caso-P002 (grupo privado)       ← Equipe do paciente P002
    └── ...
```

### 3.6 Mapeamento de Eventos → Canais

| Evento | Canal RC | Formato |
|---|---|---|
| `alert.created` (CRITICAL) | `#alertas-clinicos` + DM ao médico + `#caso-{pid}` | Template `clinical_alert_generic` |
| `alert.created` (HIGH) | `#alertas-clinicos` + `#caso-{pid}` | Template `clinical_alert_generic` |
| `alert.created` (MEDIUM/LOW) | `#alertas-clinicos` | Template `clinical_alert_generic` |
| `lab.interpreted` | `#caso-{pid}` + DM ao médico | Template `lab_result_notification` |
| `care_plan.updated` | `#caso-{pid}` + `#equipe-{tid}` | Template `care_plan_update` |
| `quality.threshold` | `#qualidade` | Template `quality_alert` |
| `teleconsult.scheduled` | `#teleconsultas` + DM ao profissional | Template `teleconsult_invite` |
| `patient.reclassified` | `#caso-{pid}` + `#equipe-{tid}` | Template `patient_reclassification` |

### 3.7 Webhook de Recebimento (Incoming)

O Rocket.Chat pode enviar webhooks para o IntelliCare quando eventos ocorrem:

```python
class RocketChatWebhookHandler:
    """Processa webhooks do Rocket.Chat."""
    
    async def handle_message(self, payload: Dict) -> Dict:
        """
        Chamado quando uma mensagem é enviada em canal monitorado.
        
        Ações possíveis:
        1. Se mensagem começa com "/" → processar como comando do bot
        2. Se é reação em alerta → marcar como 'read' no DeliveryResult
        3. Log para auditoria
        """
    
    async def handle_user_activity(self, payload: Dict) -> None:
        """
        Chamado quando usuário fica online/offline.
        Útil para: saber se profissional está disponível para alertas.
        """
```

**Endpoint de Webhook**:
```yaml
POST /api/v1/webhooks/rocketchat
  Description: Recebe eventos do Rocket.Chat
  Auth: Token compartilhado (webhook_token)
  Body: RC webhook payload
  Response 200: { status: "ok" }
```

### 3.8 API Endpoints

```yaml
# ── Mensagens ──
POST /api/v1/rocketchat/message
  Description: Envia mensagem para canal ou DM no RC
  Auth: Keycloak (admin, system)
  Body:
    channel: str               # Nome do canal ou @username para DM
    text: str                  # Texto em Markdown
    alias: Optional[str]       # Nome do remetente (default: bot)
    emoji: Optional[str]       # Avatar emoji
    attachments: Optional[List] # Attachments RC format
  Response 200: { message_id: str, channel_id: str, ts: str }

# ── Canais ──
POST /api/v1/rocketchat/channel
  Description: Cria canal no RC
  Auth: Keycloak (admin)
  Body:
    name: str                  # Nome do canal (sem #)
    type: str                  # "channel" (público) ou "group" (privado)
    members: Optional[List[str]] # Usernames iniciais
    topic: Optional[str]
    description: Optional[str]
  Response 201: { channel_id: str, name: str }

GET /api/v1/rocketchat/channels
  Description: Lista canais IntelliCare
  Auth: Keycloak
  Query: type (team|case|default|all), page, page_size
  Response 200: { items: List, total: int }

POST /api/v1/rocketchat/channel/{channel_id}/invite
  Description: Adiciona membro ao canal
  Auth: Keycloak (admin, care_coordinator)
  Body: { user_id: str }
  Response 200: { success: true }

DELETE /api/v1/rocketchat/channel/{channel_id}/member/{user_id}
  Description: Remove membro do canal
  Auth: Keycloak (admin, care_coordinator)
  Response 200: { success: true }

# ── Equipes ──
POST /api/v1/rocketchat/team-channel
  Description: Cria canal de equipe com membros
  Auth: Keycloak (admin)
  Body:
    team_id: str
    team_name: str
    unit_name: str
    member_usernames: List[str]
  Response 201: { channel_id: str, name: str }

# ── Casos ──
POST /api/v1/rocketchat/case-channel
  Description: Cria canal de caso (grupo privado)
  Auth: Keycloak (admin, doctor, care_coordinator)
  Body:
    patient_id: str
    patient_name: str
    team_member_usernames: List[str]
  Response 201: { channel_id: str, name: str }

# ── Setup ──
POST /api/v1/rocketchat/setup-defaults
  Description: Cria todos os canais padrão se não existirem
  Auth: Keycloak (admin)
  Response 200: { channels_created: List[str], already_existed: List[str] }

# ── Webhook ──
POST /api/v1/webhooks/rocketchat
  Description: Recebe webhooks do RC
  Auth: Token
  Response 200: { status: "ok" }
```

### 3.9 Testes Esperados

```
test_rocketchat/
├── test_dispatcher.py
│   ├── test_send_to_channel
│   ├── test_send_dm_to_user
│   ├── test_send_with_attachments
│   ├── test_send_to_nonexistent_channel_fails
│   ├── test_health_check_healthy
│   ├── test_health_check_unavailable
│   ├── test_read_receipt_detection
│   └── test_rate_limiting_respected
├── test_channel_service.py
│   ├── test_create_default_channels
│   ├── test_create_team_channel
│   ├── test_create_case_channel
│   ├── test_add_member
│   ├── test_remove_member
│   ├── test_pin_message
│   ├── test_duplicate_channel_returns_existing
│   └── test_list_channels_by_type
├── test_webhook_handler.py
│   ├── test_command_forwarded_to_bot
│   ├── test_reaction_updates_delivery
│   ├── test_invalid_token_rejected
│   └── test_unknown_event_logged
└── test_api.py
    ├── test_send_message_endpoint
    ├── test_create_channel_endpoint
    ├── test_setup_defaults_idempotent
    └── test_auth_required
```

---

## 4. EF-COM-011 — Sincronização de Usuários Keycloak → Rocket.Chat

### 4.1 Descrição Funcional

Quando um profissional de saúde é criado/atualizado/desativado no Keycloak, o Rocket.Chat deve refletir essas mudanças automaticamente. A sincronização garante que:

1. Todo profissional do Keycloak tem uma conta no RC
2. As roles do Keycloak determinam os canais RC
3. Desativação no Keycloak desativa no RC
4. Dados atualizados (nome, email) se propagam

### 4.2 Estratégia de Sincronização

```
Estratégia: Dual — Event-Driven + Polling de Segurança

1. EVENT-DRIVEN (primário):
   Keycloak Event Listener → HTTP Webhook → IntelliCare API

   Keycloak publica eventos quando:
   - Usuário criado (REGISTER)
   - Usuário atualizado (UPDATE_PROFILE)
   - Usuário deletado (DELETE_ACCOUNT)
   - Login bem-sucedido (LOGIN)
   - Role atribuída/removida (GRANT_ROLE / REVOKE_ROLE)

2. POLLING (segurança — roda a cada 6 horas):
   Consulta TODOS os usuários do Keycloak → compara com RC → reconcilia diferenças
   Garante consistência mesmo se webhook falhar
```

### 4.3 Modelo de Dados — UserSync

```python
class UserSyncRecord(BaseModel):
    """Registro de sincronização de cada usuário."""
    
    id: UUID = Field(default_factory=uuid4)
    keycloak_user_id: str                 # UUID do Keycloak
    rocketchat_user_id: Optional[str]     # ID do RC (depois de criado)
    username: str                         # username do Keycloak
    email: str
    full_name: str
    roles: List[str]                      # Roles do Keycloak
    team_id: Optional[str]               # Equipe/unidade
    
    # Status de sync
    sync_status: str                      # "synced" | "pending" | "error" | "disabled"
    last_synced_at: Optional[datetime]
    last_error: Optional[str]
    
    # RC state
    rc_channels: List[str]                # Canais RC em que está
    rc_active: bool                       # Conta RC ativa?
    
    created_at: datetime
    updated_at: datetime
```

### 4.4 Mapeamento Roles → Canais

```python
ROLE_CHANNEL_MAP = {
    "admin": {
        "join": ["geral", "alertas-clinicos", "teleconsultas", "educacao-saude", "qualidade"],
        "join_pattern": ["equipe-*"],  # Todos os canais de equipe
        "rc_roles": ["admin"]
    },
    "doctor": {
        "join": ["geral", "alertas-clinicos", "teleconsultas"],
        "join_team": True,             # Adicionar ao canal da sua equipe
        "rc_roles": ["user"]
    },
    "nurse": {
        "join": ["geral", "alertas-clinicos"],
        "join_team": True,
        "rc_roles": ["user"]
    },
    "care_coordinator": {
        "join": ["geral", "alertas-clinicos", "teleconsultas", "qualidade"],
        "join_pattern": ["equipe-*"],
        "rc_roles": ["user", "moderator"]
    },
    "nutritionist": {
        "join": ["geral", "educacao-saude"],
        "join_team": True,
        "rc_roles": ["user"]
    },
    "hospital_admin": {
        "join": ["geral", "qualidade"],
        "rc_roles": ["user"]
    },
    "patient": {
        "join": [],                     # Sem canais públicos
        "join_case": True,              # Apenas #caso-{seu_id}
        "rc_roles": ["user"]
    }
}
```

### 4.5 Fluxo de Sincronização

```
=== EVENTO: Novo Usuário no Keycloak ===

Keycloak Event: REGISTER
    │
    ▼
POST /api/v1/sync/keycloak-event
    │
    ▼
UserSyncService.handle_user_created(event):
    │
    ├── 1. Buscar dados completos do usuário no Keycloak Admin API
    │      GET /admin/realms/bemcuidar/users/{user_id}
    │      → { username, email, firstName, lastName, attributes, realmRoles }
    │
    ├── 2. Criar conta no Rocket.Chat
    │      POST /api/v1/users.create {
    │          username: kc_user.username,
    │          email: kc_user.email,
    │          name: f"{firstName} {lastName}",
    │          password: random_strong_password,  # Não usado (SSO via Keycloak)
    │          roles: ROLE_CHANNEL_MAP[role].rc_roles,
    │          joinDefaultChannels: false,         # Controlar manualmente
    │          verified: true                      # Já verificado no KC
    │      }
    │
    ├── 3. Adicionar aos canais corretos (baseado nas roles)
    │      Para cada canal em ROLE_CHANNEL_MAP[roles]:
    │          POST /api/v1/channels.invite { roomId, userId }
    │
    ├── 4. Se join_team=True:
    │      Determinar equipe do profissional (team_id do Keycloak attributes)
    │      Adicionar ao canal #equipe-{team_id}
    │
    ├── 5. Se patient + join_case=True:
    │      Criar #caso-{patient_id} se não existir
    │      Adicionar paciente e equipe de cuidado
    │
    ├── 6. Salvar UserSyncRecord (sync_status: "synced")
    │
    └── 7. Publicar evento: user.synced → Redis Stream


=== EVENTO: Role Alterada no Keycloak ===

Keycloak Event: GRANT_ROLE / REVOKE_ROLE
    │
    ▼
UserSyncService.handle_role_changed(event):
    │
    ├── 1. Buscar canais atuais (UserSyncRecord.rc_channels)
    ├── 2. Calcular canais esperados (novas roles → ROLE_CHANNEL_MAP)
    ├── 3. Diff: canais_a_adicionar = esperados - atuais
    ├── 4. Diff: canais_a_remover = atuais - esperados
    ├── 5. Executar adições e remoções
    └── 6. Atualizar UserSyncRecord


=== EVENTO: Usuário Desativado no Keycloak ===

Keycloak Event: DELETE_ACCOUNT ou account disabled
    │
    ▼
UserSyncService.handle_user_disabled(event):
    │
    ├── 1. Desativar conta no RC: POST /api/v1/users.setActiveStatus { active: false }
    ├── 2. Remover de todos os canais (opcional, configurável)
    └── 3. Atualizar UserSyncRecord (sync_status: "disabled")


=== POLLING DE RECONCILIAÇÃO (a cada 6 horas) ===

UserSyncService.reconcile():
    │
    ├── 1. Buscar TODOS os usuários do Keycloak
    │      GET /admin/realms/bemcuidar/users?max=1000
    │
    ├── 2. Buscar TODOS os UserSyncRecords do DB
    │
    ├── 3. Para cada usuário KC:
    │      ├── Se não tem SyncRecord → criar conta RC (como REGISTER)
    │      ├── Se SyncRecord existe mas dados divergem → atualizar RC
    │      └── Se SyncRecord existe e tudo ok → skip
    │
    ├── 4. Para cada SyncRecord sem correspondência no KC:
    │      └── Desativar conta RC
    │
    └── 5. Log de reconciliação: {total_kc, total_rc, synced, created, updated, disabled}
```

### 4.6 API Endpoints

```yaml
# ── Webhook do Keycloak ──
POST /api/v1/sync/keycloak-event
  Description: Recebe eventos do Keycloak Event Listener
  Auth: Token compartilhado (configurado no KC event listener)
  Body: Keycloak event payload
  Response 200: { processed: true }

# ── Sincronização Manual ──
POST /api/v1/sync/reconcile
  Description: Força reconciliação completa KC ↔ RC
  Auth: Keycloak (admin)
  Response 200: { total_kc: int, synced: int, created: int, updated: int, disabled: int }

POST /api/v1/sync/user/{keycloak_user_id}
  Description: Força sync de um usuário específico
  Auth: Keycloak (admin)
  Response 200: UserSyncRecord

# ── Status ──
GET /api/v1/sync/status
  Description: Status geral da sincronização
  Auth: Keycloak (admin)
  Response 200: {
    last_reconciliation: datetime,
    total_synced: int,
    total_pending: int,
    total_errors: int,
    errors: List[{ user_id, error }]
  }

GET /api/v1/sync/users
  Description: Lista registros de sincronização
  Auth: Keycloak (admin)
  Query: status (synced|pending|error|disabled), page, page_size
  Response 200: { items: List[UserSyncRecord], total: int }
```

### 4.7 Testes Esperados

```
test_user_sync/
├── test_sync_service.py
│   ├── test_new_user_creates_rc_account
│   ├── test_new_user_joins_correct_channels
│   ├── test_doctor_joins_team_channel
│   ├── test_patient_joins_only_case_channel
│   ├── test_admin_joins_all_team_channels
│   ├── test_role_change_updates_channels
│   ├── test_role_revoked_removes_from_channel
│   ├── test_user_disabled_deactivates_rc
│   └── test_duplicate_sync_is_idempotent
├── test_reconciliation.py
│   ├── test_reconcile_creates_missing_users
│   ├── test_reconcile_updates_changed_users
│   ├── test_reconcile_disables_removed_users
│   └── test_reconcile_handles_large_sets
└── test_keycloak_webhook.py
    ├── test_register_event_processed
    ├── test_grant_role_event_processed
    ├── test_invalid_token_rejected
    └── test_unknown_event_type_logged
```

---

## 5. EF-COM-012 — Bot IntelliCare no Rocket.Chat

### 5.1 Descrição Funcional

Um bot `@intellicare` presente em todos os canais do IntelliCare, agindo como assistente da equipe de saúde. O bot responde a comandos slash (/) e pode ser mencionado diretamente para perguntas.

### 5.2 Comandos do Bot

#### 5.2.1 Comandos Clínicos

```
/paciente {id_ou_nome}
├── Descrição: Exibe resumo clínico do paciente
├── Backend: GET Wanda /api/v1/aggregate/patient/{id}
├── Roles: doctor, nurse, care_coordinator
├── Resposta:
│   📋 **Resumo Clínico — Maria Santos** (P001)
│   
│   **Condições Ativas**: DM2 (Est. 3), HAS (Est. 2), DRC (Est. 3a)
│   **Risco Cardiovascular**: ALTO (Framingham: 18.5%)
│   **Último eGFR**: 42.3 ml/min (↓ 15% em 90d) ⚠️
│   **HbA1c**: 8.2% (acima da meta: 7.0%)
│   **PA**: 148/92 mmHg (acima da meta: 130/80)
│   **Alertas Abertos**: 3 (1 CRITICAL, 2 HIGH)
│   **Plano de Cuidado**: Ativo (14 tarefas, 8 concluídas)
│   **Próxima Consulta**: 20/02/2026 14:00
│   
│   [Ver no Portal](https://portal.gsi.srv.br/patient/P001)

/alertas {hoje|semana|mes} [severidade]
├── Descrição: Lista alertas clínicos recentes
├── Backend: GET Oswaldo /api/v1/alerts
├── Roles: doctor, nurse, care_coordinator
├── Resposta:
│   📊 **Alertas — Hoje** (12 total)
│   
│   🚨 **CRITICAL** (2)
│   • P001 Maria Santos — eGFR < 30 (28.5) — 10:32
│   • P047 João Pereira — Glicemia > 400 (423) — 14:15
│   
│   ⚠️ **HIGH** (4)
│   • P012 Ana Costa — PA > 180/120 — 08:45
│   • ...
│   
│   ℹ️ **MEDIUM** (6)
│   • ...

/exames {patient_id}
├── Descrição: Últimos resultados laboratoriais interpretados
├── Backend: GET Florence /api/v1/lab-results/patient/{id}/latest
├── Roles: doctor, nurse
├── Resposta:
│   🔬 **Exames — Maria Santos** (P001) — 10/02/2026
│   
│   | Exame | Resultado | Referência | Status |
│   |-------|-----------|------------|--------|
│   | eGFR | 28.5 | > 60 | 🔴 Crítico |
│   | Creatinina | 2.1 | 0.7-1.2 | 🔴 Alto |
│   | HbA1c | 8.2% | < 7.0% | 🟡 Elevado |
│   | Colesterol | 195 | < 200 | 🟢 Normal |
│   
│   **Interpretação Florence**: Padrão nefrotóxico detectado.
│   Correlação HbA1c elevada + eGFR em queda sugere progressão de nefropatia diabética.

/plano {patient_id}
├── Descrição: Plano de cuidado ativo
├── Backend: GET Geralda /api/v1/care-plans/patient/{id}/active
├── Roles: doctor, nurse, care_coordinator, nutritionist

/indicadores [pilar]
├── Descrição: Indicadores de qualidade
├── Backend: GET Donabedian /api/v1/pilares/summary
├── Roles: care_coordinator, hospital_admin, admin

/teleconsulta {patient_id}
├── Descrição: Criar sala Jitsi e enviar convite
├── Backend: POST Comunicação /api/v1/teleconsult/schedule
├── Roles: doctor, nurse
├── Fluxo:
│   1. Cria sala Jitsi com JWT
│   2. Envia convite ao paciente (WhatsApp/SMS)
│   3. Envia link no canal atual
│   4. Resposta:
│      📹 **Teleconsulta Criada**
│      Paciente: Maria Santos
│      Link: https://meet.gsi.srv.br/intellicare-abc123
│      [Entrar na Sala](https://meet.gsi.srv.br/intellicare-abc123)
│      
│      ✉️ Convite enviado ao paciente via WhatsApp

/escalar {alerta_id}
├── Descrição: Escalar alerta para coordenador
├── Backend: POST Comunicação /api/v1/routing/send (ESCALATION)
├── Roles: doctor, nurse

/drnise {pergunta}
├── Descrição: Perguntar ao chatbot Dr. Nise
├── Backend: POST Nise/Flowise /api/v1/chat
├── Roles: Todos
├── Resposta:
│   🤖 **Dr. Nise responde**:
│   
│   A diabetes tipo 2 (DM2) é uma condição crônica...
│   [resposta do LLM via Flowise/Ollama]

/ajuda
├── Descrição: Lista todos os comandos disponíveis
├── Roles: Todos
├── Resposta (filtrada por role do usuário)
```

### 5.3 Arquitetura do Bot

```python
class IntelliCareBot:
    """Bot @intellicare no Rocket.Chat."""
    
    def __init__(
        self,
        rc_client: RocketChatDispatcher,
        module_clients: Dict[str, ModuleClient],  # Clientes HTTP para cada módulo
        auth_service: AuthService                   # Para verificar roles
    ):
        self._rc = rc_client
        self._modules = module_clients
        self._auth = auth_service
        self._commands: Dict[str, BotCommand] = {}
        self._register_commands()
    
    def _register_commands(self):
        """Registra todos os comandos disponíveis."""
        self._commands = {
            "/paciente": PatientSummaryCommand(self._modules["wanda"]),
            "/alertas": AlertListCommand(self._modules["oswaldo"]),
            "/exames": LabResultsCommand(self._modules["florence"]),
            "/plano": CarePlanCommand(self._modules["geralda"]),
            "/indicadores": QualityIndicatorsCommand(self._modules["donabedian"]),
            "/teleconsulta": TeleconsultCommand(self._modules["comunicacao"]),
            "/escalar": EscalateCommand(self._modules["comunicacao"]),
            "/drnise": DrNiseCommand(self._modules["nise"]),
            "/ajuda": HelpCommand(self._commands),
        }
    
    async def handle_message(self, message: RCMessage) -> Optional[str]:
        """
        Processa mensagem recebida via webhook.
        
        1. Verificar se é comando (começa com /)
        2. Extrair comando e argumentos
        3. Verificar role do remetente
        4. Executar comando
        5. Retornar resposta formatada
        """
    
class BotCommand(ABC):
    """Interface para comandos do bot."""
    
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    @abstractmethod
    def description(self) -> str: ...
    
    @property
    @abstractmethod
    def usage(self) -> str: ...
    
    @property
    @abstractmethod
    def required_roles(self) -> List[str]: ...
    
    @abstractmethod
    async def execute(self, args: List[str], context: CommandContext) -> str: ...

class CommandContext(BaseModel):
    """Contexto de execução de um comando."""
    user_id: str
    username: str
    roles: List[str]
    room_id: str
    room_name: str
```

### 5.4 Segurança RBAC

O bot **DEVE** verificar as roles do Keycloak do usuário antes de executar qualquer comando clínico:

```python
async def handle_message(self, message: RCMessage) -> Optional[str]:
    # 1. Identificar o comando
    command_name, args = self._parse_command(message.text)
    
    # 2. Buscar comando registrado
    command = self._commands.get(command_name)
    if not command:
        return f"❓ Comando desconhecido: `{command_name}`. Use `/ajuda` para ver comandos disponíveis."
    
    # 3. Verificar roles
    user_roles = await self._auth.get_user_roles(message.user_id)
    if not any(role in command.required_roles for role in user_roles):
        return f"🔒 Você não tem permissão para usar `{command_name}`. Roles necessárias: {command.required_roles}"
    
    # 4. Executar com timeout
    try:
        context = CommandContext(
            user_id=message.user_id,
            username=message.username,
            roles=user_roles,
            room_id=message.room_id,
            room_name=message.room_name
        )
        result = await asyncio.wait_for(command.execute(args, context), timeout=10.0)
        return result
    except asyncio.TimeoutError:
        return f"⏱️ O comando `{command_name}` demorou demais. Tente novamente."
    except Exception as e:
        logger.error(f"Bot command error: {command_name}", exc_info=e)
        return f"❌ Erro ao executar `{command_name}`. Tente novamente ou contate o administrador."
```

### 5.5 Testes Esperados

```
test_bot/
├── test_command_parsing.py
│   ├── test_parse_slash_command
│   ├── test_parse_with_arguments
│   ├── test_parse_unknown_command
│   └── test_parse_empty_message_ignored
├── test_rbac.py
│   ├── test_doctor_can_access_clinical_commands
│   ├── test_nurse_can_access_clinical_commands
│   ├── test_patient_cannot_access_clinical_commands
│   ├── test_patient_can_use_ajuda
│   └── test_admin_can_access_all
├── test_commands/
│   ├── test_paciente_command.py
│   │   ├── test_returns_summary
│   │   ├── test_patient_not_found
│   │   └── test_module_unavailable_graceful_error
│   ├── test_alertas_command.py
│   ├── test_exames_command.py
│   ├── test_teleconsulta_command.py
│   └── test_drnise_command.py
└── test_bot_integration.py
    ├── test_webhook_triggers_command
    ├── test_response_sent_to_correct_room
    └── test_command_timeout_handled
```

---

## 6. SCHEMA SQL

```sql
-- Migration: 2026_02_15_0002_create_rocketchat_tables.py
-- Schema: comunicacao_operacional

-- Mapeamento de canais RC → entidades IntelliCare
CREATE TABLE comunicacao_operacional.rc_channel_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_name VARCHAR(200) NOT NULL UNIQUE,
    channel_id VARCHAR(100) NOT NULL,     -- RC room_id
    channel_type VARCHAR(20) NOT NULL,    -- "default" | "team" | "case"
    entity_type VARCHAR(20),              -- "team" | "patient" | null
    entity_id VARCHAR(200),              -- team_id ou patient_id
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_rc_channel_entity ON comunicacao_operacional.rc_channel_mappings(entity_type, entity_id);

-- Registros de sincronização de usuários
CREATE TABLE comunicacao_operacional.user_sync_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_user_id VARCHAR(200) NOT NULL UNIQUE,
    rocketchat_user_id VARCHAR(100),
    username VARCHAR(200) NOT NULL,
    email VARCHAR(300) NOT NULL,
    full_name VARCHAR(300) NOT NULL,
    roles VARCHAR(50)[] NOT NULL DEFAULT '{}',
    team_id VARCHAR(200),
    sync_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    last_synced_at TIMESTAMPTZ,
    last_error TEXT,
    rc_channels VARCHAR(200)[] DEFAULT '{}',
    rc_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sync_status ON comunicacao_operacional.user_sync_records(sync_status);
CREATE INDEX idx_sync_kc_id ON comunicacao_operacional.user_sync_records(keycloak_user_id);

-- Log de comandos do bot (auditoria)
CREATE TABLE comunicacao_operacional.bot_command_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(200) NOT NULL,
    username VARCHAR(200) NOT NULL,
    command VARCHAR(50) NOT NULL,
    arguments TEXT,
    room_id VARCHAR(100),
    room_name VARCHAR(200),
    roles VARCHAR(50)[] NOT NULL DEFAULT '{}',
    response_status VARCHAR(20) NOT NULL,  -- "success" | "error" | "unauthorized" | "timeout"
    response_time_ms INT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bot_log_user ON comunicacao_operacional.bot_command_logs(user_id);
CREATE INDEX idx_bot_log_command ON comunicacao_operacional.bot_command_logs(command);
CREATE INDEX idx_bot_log_created ON comunicacao_operacional.bot_command_logs(created_at);
```

---

## 7. ESTRUTURA DE CÓDIGO

```
comunicacao/
├── rocketchat/
│   ├── __init__.py
│   ├── dispatcher.py             # RocketChatDispatcher (IChannelDispatcher)
│   ├── client.py                 # RocketChatClient (wrapper da API REST)
│   ├── config.py                 # RocketChatConfig
│   ├── channel_service.py        # RocketChatChannelService
│   ├── webhook_handler.py        # RocketChatWebhookHandler
│   └── models.py                 # RCMessage, RCChannel, etc.
├── sync/
│   ├── __init__.py
│   ├── user_sync_service.py      # UserSyncService (KC → RC)
│   ├── keycloak_client.py        # KeycloakAdminClient
│   ├── reconciliation.py         # ReconciliationJob
│   └── models.py                 # UserSyncRecord
├── bot/
│   ├── __init__.py
│   ├── intellicare_bot.py        # IntelliCareBot principal
│   ├── command_base.py           # BotCommand ABC, CommandContext
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── paciente.py           # PatientSummaryCommand
│   │   ├── alertas.py            # AlertListCommand
│   │   ├── exames.py             # LabResultsCommand
│   │   ├── plano.py              # CarePlanCommand
│   │   ├── indicadores.py        # QualityIndicatorsCommand
│   │   ├── teleconsulta.py       # TeleconsultCommand
│   │   ├── escalar.py            # EscalateCommand
│   │   ├── drnise.py             # DrNiseCommand
│   │   └── ajuda.py              # HelpCommand
│   └── module_clients.py         # HTTP clients para cada módulo
├── api/
│   ├── rocketchat_routes.py
│   ├── sync_routes.py
│   └── webhook_routes.py
└── tests/
    ├── test_rocketchat/
    ├── test_user_sync/
    └── test_bot/
```

---

## 8. CONFIGURAÇÃO (Variáveis de Ambiente)

```bash
# Rocket.Chat
ROCKETCHAT_URL=https://rocket.gsi.srv.br
ROCKETCHAT_BOT_USERNAME=intellicare-bot
ROCKETCHAT_BOT_PASSWORD=<criar_conta_bot>
ROCKETCHAT_ADMIN_USER_ID=69921c312277eacd60658bc4
ROCKETCHAT_ADMIN_AUTH_TOKEN=<token>
ROCKETCHAT_WEBHOOK_TOKEN=<gerar_token_seguro>

# Keycloak Admin (para sync)
KEYCLOAK_ADMIN_URL=https://keycloak.gsi.srv.br
KEYCLOAK_ADMIN_REALM=master
KEYCLOAK_ADMIN_USERNAME=egarabini@gmail.com
KEYCLOAK_ADMIN_PASSWORD=<secret>
KEYCLOAK_TARGET_REALM=bemcuidar

# Módulos (para bot)
WANDA_URL=http://localhost:8007
OSWALDO_URL=http://localhost:8001
FLORENCE_URL=http://localhost:8002
GERALDA_URL=http://localhost:8006
DONABEDIAN_URL=http://localhost:8003
NISE_URL=http://localhost:8000

# Sync
USER_SYNC_POLLING_INTERVAL_HOURS=6
USER_SYNC_ENABLED=true
```

---

## 9. PREREQUISITOS E SETUP

Antes de iniciar o desenvolvimento, o DEV precisa:

1. **Criar conta bot no Rocket.Chat**:
   ```
   POST /api/v1/users.create
   { username: "intellicare-bot", name: "IntelliCare", password: "<strong>", roles: ["bot"] }
   ```

2. **Configurar Webhook Outgoing no RC**:
   - Admin → Integrations → New Outgoing Webhook
   - Event: Message Sent
   - Channel: todas
   - URL: `https://<comunicacao_url>/api/v1/webhooks/rocketchat`
   - Token: `ROCKETCHAT_WEBHOOK_TOKEN`

3. **Configurar Keycloak Event Listener** (para sync automática):
   - Keycloak Admin → Realm Settings → Events → Event Listeners
   - Adicionar webhook listener apontando para `/api/v1/sync/keycloak-event`

---

## 10. ENTREGÁVEIS DO DEV

1. **Especificação Técnica**: Diagramas de sequência para cada fluxo
2. **Plano de Implementação**: Ordem: Dispatcher → ChannelService → Bot → Sync
3. **Código**: Tudo acima com testes ≥ 80%
4. **Migrations**: Alembic para tabelas de mapeamento, sync e log
5. **Setup Script**: Script para criar conta bot e configurar webhooks
6. **Documentação**: README do domínio + docstrings

**Prazo estimado**: 2 sprints (S2 + S3)
