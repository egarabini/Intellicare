# Domínio 1 — Engine de Roteamento Multi-Canal
## Especificação Funcional Detalhada

**Identificadores**: EF-COM-001, EF-COM-002, EF-COM-003  
**Prioridade Global**: CRÍTICA  
**Sprint**: S1–S2  
**Dependências**: Nenhuma (este é o domínio base)  
**Dependentes**: Todos os outros domínios (D2–D7)

---

## 1. OBJETIVO

Construir o coração do módulo de comunicação: um motor que recebe **intenções de comunicação** de qualquer módulo do IntelliCare e decide automaticamente **como**, **por onde** e **quando** entregar cada mensagem, com fallback, métricas e rastreabilidade.

**Analogia**: O motor de roteamento é como o sistema postal inteligente de um hospital — recebe a carta (intenção), verifica o destinatário (profissional ou paciente), consulta as preferências e urgência, escolhe o melhor meio (push, chat, WhatsApp, email), entrega, e confirma o recebimento.

---

## 2. CONTEXTO ARQUITETURAL

```
┌──────────────────────────────────────────────────────┐
│               MÓDULOS CLÍNICOS (Produtores)          │
│  Oswaldo │ Florence │ Geralda │ Donabedian │ Wanda   │
└────────────────────────┬─────────────────────────────┘
                         │ Redis Streams / API REST
                         ▼
┌──────────────────────────────────────────────────────┐
│              ENGINE DE ROTEAMENTO                     │
│                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │  Receiver    │→│ RoutingEngine │→│ Dispatcher  │  │
│  │  (API/Redis) │  │ (Regras)     │  │ Manager     │  │
│  └─────────────┘  └──────────────┘  └────────────┘  │
│         │               │                  │         │
│         │          ┌────┴────┐        ┌────┼────┐    │
│         │          │Preferenc│        │    │    │    │
│         │          │ias LGPD │        RC  Push Email │
│         │          └─────────┘        WA  SMS  Twake │
│         │                                  │         │
│         ▼                                  ▼         │
│  ┌─────────────┐                 ┌──────────────┐    │
│  │ Intent Store│                 │DeliveryResult │    │
│  │ (PostgreSQL)│                 │   Store       │    │
│  └─────────────┘                 └──────────────┘    │
└──────────────────────────────────────────────────────┘
```

---

## 3. EF-COM-001 — Motor de Roteamento de Mensagens

### 3.1 Descrição Funcional Detalhada

O Motor de Roteamento é o componente central que:

1. **Recebe** uma `CommunicationIntent` (via API REST ou Redis Streams consumer)
2. **Valida** a intenção (campos obrigatórios, destinatário existe, template existe)
3. **Consulta** preferências LGPD do destinatário (EF-COM-050)
4. **Resolve** o destinatário (mapeia `recipient_id` → dados de contato reais)
5. **Aplica** regras de roteamento (severidade → canais → ordem)
6. **Renderiza** o conteúdo (template + parâmetros → mensagem formatada por canal)
7. **Despacha** para o(s) Dispatcher(s) selecionados
8. **Monitora** timeout de entrega e aciona fallback se necessário
9. **Registra** cada tentativa como `DeliveryResult`

### 3.2 Modelo de Dados

#### 3.2.1 CommunicationIntent (Intenção de Comunicação)

```python
class CommunicationIntent(BaseModel):
    """Representa uma intenção de comunicação gerada por qualquer módulo."""
    
    id: UUID = Field(default_factory=uuid4)
    
    # Origem
    source_module: str                    # "intellicare-oswaldo", "intellicare-florence", etc.
    source_event_id: Optional[str]        # ID do evento original no módulo de origem
    
    # Destinatário
    recipient_type: RecipientType         # PROFESSIONAL | PATIENT | TEAM | COORDINATOR | BROADCAST
    recipient_id: str                     # ID do profissional/paciente/equipe no Keycloak ou sistema
    recipient_ids: Optional[List[str]]    # Para BROADCAST: lista de IDs
    
    # Classificação
    severity: Severity                    # CRITICAL | HIGH | MEDIUM | LOW
    category: MessageCategory             # CLINICAL_ALERT | REMINDER | EDUCATION | REPORT | 
                                          # TELECONSULT | CARE_PLAN | LAB_RESULT | ESCALATION |
                                          # TEAM_NOTIFICATION | QUALITY_REPORT
    
    # Conteúdo
    content_template_id: Optional[str]    # Referência ao template (ex: "clinical_alert_egfr_drop")
    content_params: Optional[Dict]        # Parâmetros para preencher o template
    content_raw: Optional[str]            # Conteúdo direto (se não usar template)
    
    # Controle de entrega
    preferred_channel: Optional[str]      # Canal preferido (opcional, pode ser nulo = automático)
    excluded_channels: List[str] = []     # Canais a NÃO usar (ex: paciente pediu sem SMS)
    require_ack: bool = False             # Exige confirmação de leitura?
    max_attempts: int = 3                 # Máximo de tentativas por canal
    
    # Agendamento
    scheduled_at: Optional[datetime]      # Nulo = imediato
    expires_at: Optional[datetime]        # Mensagem expira se não entregue a tempo
    
    # Rastreabilidade
    correlation_id: str                   # Para rastrear todo o fluxo end-to-end
    parent_intent_id: Optional[UUID]      # Se é escalonamento de outro intent
    
    # Metadados
    metadata: Optional[Dict]              # Dados extras (patient_name, etc. para contexto)
    
    # Controle interno
    status: IntentStatus = IntentStatus.PENDING  # PENDING | PROCESSING | COMPLETED | FAILED | EXPIRED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime]
```

#### 3.2.2 Enums

```python
class RecipientType(str, Enum):
    PROFESSIONAL = "professional"     # Médico, enfermeiro, nutricionista
    PATIENT = "patient"               # Paciente
    TEAM = "team"                     # Equipe de saúde (todos os membros)
    COORDINATOR = "coordinator"       # Coordenador de cuidado
    BROADCAST = "broadcast"           # Múltiplos destinatários

class Severity(str, Enum):
    CRITICAL = "critical"             # Risco de vida / deterioração aguda
    HIGH = "high"                     # Atenção urgente necessária
    MEDIUM = "medium"                 # Informação importante
    LOW = "low"                       # Informação de rotina

class MessageCategory(str, Enum):
    CLINICAL_ALERT = "clinical_alert"           # Alerta de Oswaldo/Florence
    MEDICATION_REMINDER = "medication_reminder"  # Lembrete de Geralda
    APPOINTMENT_REMINDER = "appointment_reminder"
    TELECONSULT = "teleconsult"                 # Convite/lembrete
    LAB_RESULT = "lab_result"                   # Resultado de Florence
    CARE_PLAN = "care_plan"                     # Atualização de Geralda
    QUALITY_REPORT = "quality_report"           # Relatório de Donabedian
    EDUCATION = "education"                     # Material educativo (Nise)
    TEAM_NOTIFICATION = "team_notification"     # Notificação interna
    ESCALATION = "escalation"                   # Escalonamento automático
    SYSTEM = "system"                           # Notificação de sistema

class IntentStatus(str, Enum):
    PENDING = "pending"               # Aguardando processamento
    SCHEDULED = "scheduled"           # Agendada para o futuro
    PROCESSING = "processing"         # Sendo processada pelo router
    DISPATCHED = "dispatched"         # Enviada para dispatcher(s)
    COMPLETED = "completed"           # Entregue com sucesso
    PARTIALLY_COMPLETED = "partially" # Alguns canais falharam
    FAILED = "failed"                 # Todos os canais falharam
    EXPIRED = "expired"               # Expirou antes da entrega
    CANCELLED = "cancelled"           # Cancelada manualmente
```

#### 3.2.3 DeliveryResult (Resultado de Cada Tentativa)

```python
class DeliveryResult(BaseModel):
    """Registra cada tentativa de entrega em cada canal."""
    
    id: UUID = Field(default_factory=uuid4)
    intent_id: UUID                       # FK → CommunicationIntent
    
    # Canal
    channel: str                          # "rocketchat" | "matrix" | "push" | "email" | "whatsapp" | "sms"
    attempt_number: int                   # 1, 2, 3...
    
    # Status de entrega
    status: DeliveryStatus                # QUEUED | SENDING | SENT | DELIVERED | READ | FAILED | EXPIRED
    
    # Referência no canal externo
    channel_message_id: Optional[str]     # ID da mensagem no RC, Jitsi, WhatsApp, etc.
    channel_room_id: Optional[str]        # ID do canal/sala/conversa
    
    # Erro (se falhou)
    error_code: Optional[str]             # Código de erro padronizado
    error_message: Optional[str]          # Descrição do erro
    
    # Timestamps
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime]           # Quando foi enviado ao canal
    delivered_at: Optional[datetime]      # Quando o canal confirmou entrega
    read_at: Optional[datetime]           # Quando o destinatário leu
    failed_at: Optional[datetime]         # Quando falhou
    
    # Métricas
    latency_send_ms: Optional[int]        # queued_at → sent_at
    latency_deliver_ms: Optional[int]     # sent_at → delivered_at
    latency_read_ms: Optional[int]        # delivered_at → read_at

class DeliveryStatus(str, Enum):
    QUEUED = "queued"                     # Na fila para envio
    SENDING = "sending"                   # Sendo enviado
    SENT = "sent"                         # Enviado ao canal (sem confirmação)
    DELIVERED = "delivered"               # Canal confirmou entrega
    READ = "read"                         # Destinatário leu
    FAILED = "failed"                     # Falha no envio
    EXPIRED = "expired"                   # Expirou sem entrega
    SKIPPED = "skipped"                   # Pulado (preferência do paciente)
```

### 3.3 Regras de Roteamento

As regras definem a cascata de canais para cada combinação de severidade × tipo de destinatário.

#### 3.3.1 Tabela de Roteamento Padrão

**Para PROFISSIONAIS (doctor, nurse, care_coordinator, nutritionist):**

| Severidade | Canal 1 (Primário) | Timeout | Canal 2 (Fallback) | Timeout | Canal 3 |
|---|---|---|---|---|---|
| CRITICAL | Push + Rocket.Chat (simultâneo) | 5 min | SMS | 10 min | Escalar → Coordenador |
| HIGH | Rocket.Chat | 15 min | Push + Email | 30 min | Escalar → Coordenador |
| MEDIUM | Rocket.Chat | 1 hora | Email | — | — |
| LOW | Email | — | — | — | — |

**Para PACIENTES:**

| Severidade | Canal 1 | Timeout | Canal 2 | Timeout | Canal 3 |
|---|---|---|---|---|---|
| CRITICAL | WhatsApp + SMS (simultâneo) | N/A | Push | — | Notificar equipe |
| HIGH | WhatsApp | 1 hora | SMS | — | — |
| MEDIUM | WhatsApp | — | Email | — | — |
| LOW | Email | — | — | — | — |
| EDUCATION | WhatsApp/Chatbot | — | Email | — | — |
| REMINDER | WhatsApp | 2h antes | SMS | 30min antes | Push |

**Para EQUIPES:**

| Severidade | Canal | Estratégia |
|---|---|---|
| Qualquer | Rocket.Chat (canal da equipe) | Broadcast para todos os membros |
| CRITICAL | Rocket.Chat + Push (todos) | Simultâneo |

#### 3.3.2 Modelo de Regra Configurável

```python
class RoutingRule(BaseModel):
    """Regra de roteamento configurável por instituição."""
    
    id: str                               # "rule_critical_professional"
    name: str                             # "Alertas Críticos para Profissionais"
    priority: int                         # Ordem de avaliação (1 = primeiro)
    active: bool = True
    
    # Condições (AND)
    conditions: RoutingConditions
    
    # Ação
    action: RoutingAction
    
    # Metadados
    institution_id: Optional[str]         # Se específica de uma instituição
    created_at: datetime
    updated_at: datetime

class RoutingConditions(BaseModel):
    """Condições para ativar uma regra."""
    severity: Optional[List[Severity]]            # Ex: [CRITICAL, HIGH]
    category: Optional[List[MessageCategory]]     # Ex: [CLINICAL_ALERT]
    recipient_type: Optional[List[RecipientType]] # Ex: [PROFESSIONAL]
    source_module: Optional[List[str]]            # Ex: ["intellicare-oswaldo"]
    time_range: Optional[TimeRange]               # Ex: horário comercial vs noturno

class RoutingAction(BaseModel):
    """Ação a executar quando a regra é ativada."""
    channels: List[ChannelStep]                   # Lista ordenada de canais
    require_ack: bool = False
    escalation: Optional[EscalationConfig]

class ChannelStep(BaseModel):
    """Um passo na cascata de canais."""
    channel: str                          # "rocketchat", "push", "email", etc.
    delay_seconds: int = 0                # 0 = imediato, >0 = esperar antes de enviar
    timeout_seconds: Optional[int]        # Tempo para considerar falha e ir para próximo
    concurrent: bool = False              # True = enviar junto com o anterior

class EscalationConfig(BaseModel):
    """Configuração de escalonamento automático."""
    timeout_seconds: int                  # Tempo sem leitura para escalar
    escalate_to: RecipientType            # COORDINATOR normalmente
    escalation_message_template: str      # Template da mensagem de escalonamento
```

### 3.4 Fluxo de Processamento Detalhado

```
ENTRADA: CommunicationIntent
    │
    ▼
[1. VALIDAÇÃO]
    │ ├─ Campos obrigatórios preenchidos?
    │ ├─ Template existe (se especificado)?
    │ ├─ Recipient_id válido?
    │ └─ Se agendada: scheduled_at > now?
    │       └─ SIM → Salvar com status SCHEDULED, agendar worker
    │
    ▼
[2. RESOLUÇÃO DO DESTINATÁRIO]
    │ ├─ recipient_type == PROFESSIONAL?
    │ │   └─ Consultar Keycloak → obter email, roles, unidade
    │ ├─ recipient_type == PATIENT?
    │ │   └─ Consultar DB → obter telefone, email, preferências
    │ ├─ recipient_type == TEAM?
    │ │   └─ Expandir equipe → lista de profissionais
    │ └─ recipient_type == BROADCAST?
    │       └─ Expandir recipient_ids → resolver cada um
    │
    ▼
[3. CONSULTA DE PREFERÊNCIAS (LGPD)]
    │ ├─ Paciente tem opt-in para o canal primário?
    │ ├─ Estamos em quiet hours?
    │ ├─ Paciente bloqueou algum canal?
    │ └─ EXCEÇÃO: severity == CRITICAL ignora quiet hours (Art. 7, VII LGPD)
    │
    ▼
[4. SELEÇÃO DE REGRA DE ROTEAMENTO]
    │ ├─ Avaliar regras em ordem de prioridade
    │ ├─ Primeira regra cujas condições casam → usar ação dessa regra
    │ └─ Nenhuma regra casa → usar regra default (mapa severidade → canais)
    │
    ▼
[5. RENDERIZAÇÃO DO CONTEÚDO]
    │ ├─ Para cada canal selecionado:
    │ │   ├─ Buscar variante do template para aquele canal
    │ │   ├─ Substituir parâmetros (Jinja2 ou similar)
    │ │   └─ Validar resultado (não vazio, tamanho ok)
    │ └─ Se content_raw (sem template): usar diretamente
    │
    ▼
[6. DESPACHO (DISPATCH)]
    │ ├─ Para cada ChannelStep na ação:
    │ │   ├─ Se delay_seconds > 0: agendar
    │ │   ├─ Criar DeliveryResult (status: QUEUED)
    │ │   ├─ Chamar DispatcherManager.dispatch(channel, message)
    │ │   ├─ Atualizar DeliveryResult (status: SENT/FAILED)
    │ │   └─ Se concurrent==True: enviar em paralelo com anterior
    │ │
    │ ├─ Se canal primário FALHOU:
    │ │   └─ Ir para próximo canal na cascata (EF-COM-002)
    │ │
    │ └─ Se require_ack == True:
    │       └─ Iniciar timer de timeout (FallbackMonitor)
    │
    ▼
[7. MONITORAMENTO DE FALLBACK]
    │ ├─ Timer verifica se DeliveryStatus mudou para READ dentro do timeout
    │ ├─ Se NÃO leu em timeout:
    │ │   ├─ Tentar próximo canal na cascata
    │ │   └─ Se todos falharam + escalation config:
    │ │       └─ Criar novo CommunicationIntent (parent_intent_id = current)
    │ │           com recipient_type = COORDINATOR, category = ESCALATION
    │ └─ Se SIM leu: marcar intent como COMPLETED
    │
    ▼
[8. REGISTRO E MÉTRICAS]
    ├─ Atualizar intent.status (COMPLETED | FAILED | EXPIRED)
    ├─ Calcular latências (send, deliver, read)
    ├─ Publicar evento Redis: comm.sent / comm.delivered / comm.failed
    └─ Incrementar contadores Prometheus
```

### 3.5 API Endpoints

```yaml
# ── Envio de Mensagem ──
POST /api/v1/routing/send
  Description: Envia uma intenção de comunicação para processamento
  Auth: Keycloak JWT (roles: admin, doctor, nurse, care_coordinator, system)
  Body: CommunicationIntent (JSON)
  Response 202:
    body:
      intent_id: UUID
      status: "pending"
      message: "Intent accepted for processing"
  Response 400: Validação falhou
  Response 401: Não autenticado
  Response 403: Role insuficiente

# ── Envio em Batch ──
POST /api/v1/routing/send-batch
  Description: Envia múltiplas intenções (ex: lembrete de medicação para 50 pacientes)
  Auth: Keycloak JWT (roles: admin, system)
  Body: { intents: List[CommunicationIntent] }
  Response 202:
    body:
      accepted: int
      rejected: int
      intent_ids: List[UUID]
  Limite: 100 intents por chamada

# ── Consultar Intent ──
GET /api/v1/routing/intents/{intent_id}
  Description: Status detalhado de uma intenção
  Auth: Keycloak JWT
  Response 200:
    body:
      intent: CommunicationIntent
      deliveries: List[DeliveryResult]
      timeline: List[TimelineEvent]  # eventos cronológicos

# ── Listar Intents ──
GET /api/v1/routing/intents
  Description: Lista intenções com filtros
  Auth: Keycloak JWT (roles: admin, care_coordinator)
  Query Params:
    status: Optional[IntentStatus]
    severity: Optional[Severity]
    category: Optional[MessageCategory]
    source_module: Optional[str]
    recipient_id: Optional[str]
    date_from: Optional[datetime]
    date_to: Optional[datetime]
    page: int = 1
    page_size: int = 50
  Response 200: { items: List, total: int, page: int }

# ── Cancelar Intent ──
PUT /api/v1/routing/intents/{intent_id}/cancel
  Description: Cancela uma intenção pendente ou agendada
  Auth: Keycloak JWT
  Response 200: { status: "cancelled" }
  Response 409: Já entregue, não pode cancelar

# ── Regras de Roteamento ──
GET /api/v1/routing/rules
  Description: Lista regras de roteamento ativas
  Auth: Keycloak JWT (role: admin)
  Response 200: List[RoutingRule]

POST /api/v1/routing/rules
  Description: Criar nova regra
  Auth: Keycloak JWT (role: admin)
  Body: RoutingRule
  Response 201: { id: str }

PUT /api/v1/routing/rules/{rule_id}
  Description: Atualizar regra
  Auth: Keycloak JWT (role: admin)

DELETE /api/v1/routing/rules/{rule_id}
  Description: Desativar regra (soft delete)
  Auth: Keycloak JWT (role: admin)

# ── Métricas ──
GET /api/v1/routing/metrics
  Description: Métricas do motor de roteamento
  Auth: Keycloak JWT (roles: admin, care_coordinator)
  Response 200:
    body:
      total_intents_today: int
      by_status: { pending: int, completed: int, failed: int, ... }
      by_severity: { critical: int, high: int, ... }
      by_channel: { rocketchat: int, push: int, ... }
      avg_latency_ms: { send: float, deliver: float, read: float }
      fallback_rate: float          # % de mensagens que usaram fallback
      escalation_count_today: int
```

### 3.6 Comportamento em Cenários Críticos

#### Cenário 1: Alerta Crítico de eGFR (Oswaldo → Equipe Médica)

```
Evento: Oswaldo publica alert.created (patient_id=P001, severity=CRITICAL, type="egfr-drop")
    │
Consumer Redis (D5) consome e gera:
    │
CommunicationIntent:
    source_module: "intellicare-oswaldo"
    recipient_type: PROFESSIONAL
    recipient_id: "dr-silva-uuid"       # Médico responsável do P001
    severity: CRITICAL
    category: CLINICAL_ALERT
    content_template_id: "clinical_alert_egfr_drop"
    content_params: {
        patient_name: "Maria Santos",
        patient_id: "P001",
        egfr_current: 28.5,
        egfr_previous: 38.2,
        delta: -25.4,
        period_days: 90,
        alert_type: "Queda rápida de eGFR",
        portal_url: "https://portal.gsi.srv.br/patient/P001/alerts"
    }
    require_ack: True
    correlation_id: "corr-2026-0215-001"
    │
Router processa:
    1. Resolve dr-silva-uuid → Dr. João Silva, equipe UBS Centro
    2. Preferências: sem restrições (é profissional)
    3. Regra: CRITICAL + PROFESSIONAL → Push + Rocket.Chat (simultâneo), fallback SMS em 5min
    4. Renderiza:
       - Push: título="⚠️ ALERTA CRÍTICO", body="Maria Santos: eGFR caiu 25% (28.5 ml/min)"
       - RC: markdown="🚨 **ALERTA CRÍTICO**\n\nPaciente: Maria Santos\neGFR: 38.2 → 28.5 (-25%)..."
    5. Despacha: Push + RC simultâneo
    6. Timer: 5 min para ack
    │
T+0s:  Push enviado → DeliveryResult(push, SENT)
T+0s:  RC enviado → DeliveryResult(rocketchat, SENT)
T+2s:  Push entregue → DeliveryResult(push, DELIVERED)
T+3min: Dr. Silva lê no RC → DeliveryResult(rocketchat, READ)
T+3min: Intent → COMPLETED (ack recebido dentro do timeout)
```

#### Cenário 2: Fallback + Escalonamento

```
Mesmo cenário, mas Dr. Silva está em cirurgia:

T+0s:  Push enviado → SENT
T+0s:  RC enviado → SENT
T+5min: Nenhum READ → FallbackMonitor ativa
T+5min: SMS enviado → DeliveryResult(sms, SENT)
T+10min: Nenhum READ → EscalationConfig ativa
T+10min: Novo CommunicationIntent criado:
         parent_intent_id: <original>
         recipient_type: COORDINATOR
         severity: CRITICAL
         category: ESCALATION
         content_template_id: "escalation_unread_critical"
         content_params: {
             original_alert: "eGFR drop P001",
             original_recipient: "Dr. João Silva",
             minutes_unread: 10
         }
T+10min: Coordenador recebe no RC + Push: 
         "⚠️ ESCALONAMENTO: Alerta crítico para Dr. Silva não lido há 10 min"
```

### 3.7 Requisitos Não-Funcionais

| Requisito | Meta | Medição |
|---|---|---|
| Latência de processamento | < 500ms (CRITICAL), < 2s (outros) | Prometheus histogram |
| Throughput | ≥ 100 intents/segundo | Load test |
| Disponibilidade | 99.9% | Uptime monitor |
| Persistência | Todas as intents e results persistidos | Zero data loss |
| Idempotência | Mesmo intent_id processado apenas 1 vez | Dedup por UUID |
| Recuperação | Intents PENDING reprocessados após restart | Startup scan |

### 3.8 Testes Esperados

```
test_routing_engine/
├── test_intent_validation.py
│   ├── test_valid_intent_accepted
│   ├── test_missing_required_fields_rejected
│   ├── test_invalid_severity_rejected
│   └── test_expired_intent_rejected
├── test_rule_matching.py
│   ├── test_critical_professional_matches_rule
│   ├── test_low_patient_matches_default
│   ├── test_custom_rule_overrides_default
│   ├── test_rules_evaluated_in_priority_order
│   └── test_no_match_uses_fallback_rule
├── test_routing_flow.py
│   ├── test_critical_alert_routes_to_push_and_rc
│   ├── test_medium_routes_to_rc_only
│   ├── test_patient_routes_to_whatsapp
│   ├── test_scheduled_intent_waits
│   └── test_expired_intent_not_sent
├── test_fallback.py
│   ├── test_primary_failure_triggers_fallback
│   ├── test_all_channels_fail_marks_intent_failed
│   ├── test_escalation_creates_new_intent
│   └── test_concurrent_channels_sent_simultaneously
├── test_delivery_tracking.py
│   ├── test_delivery_result_created_per_attempt
│   ├── test_latency_calculated_correctly
│   ├── test_read_ack_completes_intent
│   └── test_metrics_incremented
└── test_api.py
    ├── test_send_endpoint_returns_202
    ├── test_send_batch_limit_100
    ├── test_get_intent_with_deliveries
    ├── test_cancel_pending_intent
    ├── test_cancel_completed_fails_409
    ├── test_list_intents_filtered
    ├── test_auth_required
    └── test_role_based_access
```

---

## 4. EF-COM-002 — Dispatcher Multi-Canal

### 4.1 Descrição Funcional Detalhada

Cada canal de comunicação é acessado através de um **Dispatcher** — uma classe que implementa uma interface padronizada. O `DispatcherManager` gerencia todos os dispatchers e permite ao Router enviar para qualquer canal sem acoplamento.

### 4.2 Interface IChannelDispatcher

```python
from abc import ABC, abstractmethod

class IChannelDispatcher(ABC):
    """Interface comum que todos os dispatchers de canal devem implementar."""
    
    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Nome único do canal. Ex: 'rocketchat', 'matrix', 'push'."""
        ...
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Nome legível. Ex: 'Rocket.Chat', 'Web Push'."""
        ...
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Verifica se o canal está operacional (health check)."""
        ...
    
    @abstractmethod
    async def send(
        self,
        recipient: ResolvedRecipient,
        content: RenderedContent,
        metadata: Dict
    ) -> DispatchResult:
        """
        Envia mensagem para o destinatário.
        
        Args:
            recipient: Destinatário resolvido (com dados de contato)
            content: Conteúdo já renderizado para este canal
            metadata: Dados extras (correlation_id, intent_id, etc.)
        
        Returns:
            DispatchResult com status e channel_message_id
        """
        ...
    
    @abstractmethod
    async def check_delivery_status(
        self, 
        channel_message_id: str
    ) -> DeliveryStatus:
        """Consulta status de entrega no canal externo."""
        ...
    
    @abstractmethod
    async def get_health(self) -> ChannelHealth:
        """Retorna saúde detalhada do canal."""
        ...
    
    async def supports_read_receipt(self) -> bool:
        """Se o canal suporta confirmação de leitura."""
        return False
    
    async def supports_rich_content(self) -> bool:
        """Se o canal suporta botões, imagens, attachments."""
        return False

class ResolvedRecipient(BaseModel):
    """Destinatário com dados de contato resolvidos."""
    user_id: str
    display_name: str
    channel_specific_id: Optional[str]  # RC user_id, Jitsi room, phone number, email
    email: Optional[str]
    phone: Optional[str]
    roles: List[str]
    team_id: Optional[str]

class RenderedContent(BaseModel):
    """Conteúdo renderizado para um canal específico."""
    format: str                   # "markdown", "html", "plain", "whatsapp_template", "push"
    body: str                     # Corpo da mensagem
    subject: Optional[str]        # Para email
    title: Optional[str]          # Para push
    action_url: Optional[str]     # URL para ação
    action_label: Optional[str]   # Texto do botão
    attachments: Optional[List[Dict]]  # Anexos
    
class DispatchResult(BaseModel):
    """Resultado do envio por um dispatcher."""
    success: bool
    channel_message_id: Optional[str]
    channel_room_id: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    timestamp: datetime

class ChannelHealth(BaseModel):
    """Saúde de um canal."""
    channel: str
    status: str                   # "healthy", "degraded", "unavailable"
    latency_ms: Optional[int]
    last_check: datetime
    details: Optional[Dict]
```

### 4.3 DispatcherManager

```python
class DispatcherManager:
    """Gerencia todos os dispatchers registrados."""
    
    _dispatchers: Dict[str, IChannelDispatcher]
    
    def register(self, dispatcher: IChannelDispatcher) -> None:
        """Registra um dispatcher."""
        
    def get(self, channel_name: str) -> Optional[IChannelDispatcher]:
        """Obtém dispatcher por nome do canal."""
        
    async def dispatch(
        self, 
        channel: str, 
        recipient: ResolvedRecipient,
        content: RenderedContent,
        metadata: Dict
    ) -> DispatchResult:
        """Despacha para um canal específico."""
        
    async def health_check_all(self) -> Dict[str, ChannelHealth]:
        """Health check de todos os canais."""
        
    def list_available_channels(self) -> List[str]:
        """Lista canais disponíveis."""
```

### 4.4 Dispatchers a Implementar

Cada um será detalhado em seu respectivo domínio (D2, D4), mas o DEV-1 deve criar **stubs** para que o Router funcione:

| Dispatcher | Domínio | Implementação Real |
|---|---|---|
| `RocketChatDispatcher` | D2 | DEV-2 implementa |
| `JitsiDispatcher` | D3 | DEV-3 implementa (teleconsultas) |
| `PushDispatcher` | D4 | DEV-4 implementa |
| `EmailDispatcher` | D4 | DEV-4 implementa |
| `WhatsAppDispatcher` | D4 | DEV-4 implementa |
| `SMSDispatcher` | D4 | DEV-4 implementa |
| `JitsiDispatcher` | D3 | DEV-3 implementa |

### 4.5 API Endpoints

```yaml
GET /api/v1/channels
  Description: Lista todos os canais registrados
  Response 200: [
    { name: "rocketchat", display: "Rocket.Chat", available: true, read_receipt: true },
    { name: "push", display: "Web Push", available: true, read_receipt: false },
    ...
  ]

GET /api/v1/channels/{channel}/health
  Description: Saúde detalhada de um canal
  Response 200: ChannelHealth

POST /api/v1/channels/{channel}/test
  Description: Enviar mensagem de teste
  Auth: admin only
  Body: { recipient_id: str, message: str }
  Response 200: DispatchResult
```

### 4.6 Testes Esperados

```
test_dispatchers/
├── test_dispatcher_interface.py
│   ├── test_all_dispatchers_implement_interface
│   ├── test_dispatcher_registration
│   └── test_unknown_channel_raises_error
├── test_dispatcher_manager.py
│   ├── test_dispatch_to_available_channel
│   ├── test_dispatch_to_unavailable_returns_error
│   ├── test_health_check_all
│   └── test_list_channels
├── test_matrix_dispatcher.py    # Refactor do existente
│   ├── test_send_message
│   ├── test_create_room
│   ├── test_health_check
│   └── test_unavailable_server
└── test_stub_dispatchers.py     # Stubs para outros domínios
    ├── test_rc_stub_registered
    ├── test_push_stub_registered
    └── test_email_stub_registered
```

---

## 5. EF-COM-003 — Sistema de Templates de Mensagens

### 5.1 Descrição Funcional Detalhada

Templates garantem que mensagens clínicas sejam padronizadas, acessíveis e adaptadas a cada canal. Um único evento clínico gera mensagens formatadas diferentemente para Rocket.Chat (Markdown), email (HTML), WhatsApp (template aprovado), SMS (texto curto) e Push (título+body).

### 5.2 Modelo de Dados

```python
class MessageTemplate(BaseModel):
    """Template de mensagem com variantes por canal."""
    
    id: str                               # "clinical_alert_egfr_drop"
    name: str                             # "Alerta de Queda de eGFR"
    description: str                      # "Usado quando eGFR cai > 15% em 90 dias"
    category: MessageCategory             # CLINICAL_ALERT
    version: int = 1                      # Incrementa a cada atualização
    
    # Variantes por canal
    channel_variants: Dict[str, ChannelVariant]
    
    # Schema dos parâmetros esperados (JSON Schema)
    params_schema: Dict                   # Para validação antes de renderizar
    
    # Parâmetros de exemplo (para preview)
    sample_params: Dict                   # Dados fake para teste
    
    # Controle
    active: bool = True
    locale: str = "pt-BR"                 # Idioma (expansível)
    created_at: datetime
    updated_at: datetime
    created_by: str                       # user_id de quem criou

class ChannelVariant(BaseModel):
    """Variante de um template para um canal específico."""
    
    format: str                           # "markdown", "html", "plain", "whatsapp_template", "push_json"
    body: str                             # Template com {{placeholders}} Jinja2
    subject: Optional[str]                # Para email
    title: Optional[str]                  # Para push
    action_url_template: Optional[str]    # URL com placeholders
    action_label: Optional[str]
    max_length: Optional[int]             # Para SMS: 160, para Push: 200
    
    # Para WhatsApp Business API
    whatsapp_template_name: Optional[str] # Nome do template aprovado pela Meta
    whatsapp_components: Optional[List]   # Estrutura de componentes
```

### 5.3 Templates Iniciais (Pré-Cadastrados)

O sistema deve ser entregue com os seguintes templates pré-cadastrados:

#### Template 1: `clinical_alert_generic`
```yaml
id: clinical_alert_generic
name: Alerta Clínico Genérico
category: CLINICAL_ALERT
params_schema:
  required: [patient_name, patient_id, severity, alert_type, message, source_module, correlation_id]
  properties:
    patient_name: { type: string }
    patient_id: { type: string }
    severity: { type: string, enum: [CRITICAL, HIGH, MEDIUM, LOW] }
    alert_type: { type: string }
    message: { type: string }
    source_module: { type: string }
    correlation_id: { type: string }
    portal_url: { type: string }

channel_variants:
  rocketchat:
    format: markdown
    body: |
      {{ "🚨" if severity == "CRITICAL" else "⚠️" if severity == "HIGH" else "ℹ️" }} **ALERTA CLÍNICO — {{severity}}**
      
      **Paciente**: {{patient_name}} (`{{patient_id}}`)
      **Tipo**: {{alert_type}}
      **Mensagem**: {{message}}
      **Módulo**: {{source_module}}
      **Referência**: `{{correlation_id}}`
      
      {% if portal_url %}[📋 Ver no Portal]({{portal_url}}){% endif %}

  push:
    format: push_json
    title: "{{ '🚨' if severity == 'CRITICAL' else '⚠️' }} Alerta — {{severity}}"
    body: "{{patient_name}}: {{message}}"
    action_url_template: "{{portal_url}}"
    action_label: "Ver Alerta"
    max_length: 200

  email:
    format: html
    subject: "[IntelliCare] Alerta {{severity}} — {{patient_name}}"
    body: |
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: {{ '#DC2626' if severity == 'CRITICAL' else '#F59E0B' if severity == 'HIGH' else '#3B82F6' }}; 
                    color: white; padding: 16px; border-radius: 8px 8px 0 0;">
          <h2 style="margin: 0;">⚠️ Alerta Clínico — {{severity}}</h2>
        </div>
        <div style="border: 1px solid #E5E7EB; padding: 20px; border-radius: 0 0 8px 8px;">
          <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="padding: 8px; font-weight: bold;">Paciente</td><td>{{patient_name}}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Tipo</td><td>{{alert_type}}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Mensagem</td><td>{{message}}</td></tr>
            <tr><td style="padding: 8px; font-weight: bold;">Módulo</td><td>{{source_module}}</td></tr>
          </table>
          {% if portal_url %}
          <div style="text-align: center; margin-top: 20px;">
            <a href="{{portal_url}}" style="background: #3B82F6; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none;">
              Ver no Portal
            </a>
          </div>
          {% endif %}
        </div>
        <p style="color: #9CA3AF; font-size: 12px; text-align: center; margin-top: 16px;">
          IntelliCare — Plataforma de Inteligência Clínica
        </p>
      </div>

  whatsapp:
    format: plain
    body: |
      {{ "🚨" if severity == "CRITICAL" else "⚠️" }} *ALERTA {{severity}}*
      
      Paciente: {{patient_name}}
      {{message}}
      
      {% if portal_url %}Acesse: {{portal_url}}{% endif %}
    max_length: 1024

  sms:
    format: plain
    body: "INTELLICARE ALERTA {{severity}}: {{patient_name}} - {{message | truncate(80)}}{% if portal_url %} {{portal_url}}{% endif %}"
    max_length: 160

sample_params:
  patient_name: "Maria Santos"
  patient_id: "P001"
  severity: "CRITICAL"
  alert_type: "Queda de eGFR"
  message: "eGFR caiu 25% nos últimos 90 dias (38.2 → 28.5 ml/min/1.73m²)"
  source_module: "intellicare-oswaldo"
  correlation_id: "corr-2026-0215-001"
  portal_url: "https://portal.gsi.srv.br/patient/P001/alerts"
```

#### Template 2: `medication_reminder`
```yaml
id: medication_reminder
name: Lembrete de Medicação
category: MEDICATION_REMINDER
params_schema:
  required: [patient_name, medication_name, dosage, time]
  properties:
    patient_name: { type: string }
    medication_name: { type: string }
    dosage: { type: string }
    time: { type: string }
    instructions: { type: string }

channel_variants:
  whatsapp:
    format: plain
    body: |
      💊 Olá {{patient_name}}!
      
      Lembrete: tome *{{medication_name}}* ({{dosage}}) às *{{time}}*.
      {% if instructions %}
      📝 {{instructions}}
      {% endif %}
      
      Cuide da sua saúde! 💙
      _IntelliCare_
    max_length: 1024
    
  sms:
    format: plain
    body: "INTELLICARE: {{patient_name}}, tome {{medication_name}} ({{dosage}}) as {{time}}."
    max_length: 160
    
  push:
    format: push_json
    title: "💊 Hora da Medicação"
    body: "{{medication_name}} ({{dosage}}) — {{time}}"
    max_length: 200
```

#### Template 3: `teleconsult_invite`
```yaml
id: teleconsult_invite
name: Convite para Teleconsulta
category: TELECONSULT
params_schema:
  required: [patient_name, professional_name, professional_role, date, time, jitsi_url]

channel_variants:
  whatsapp:
    format: plain
    body: |
      📹 Olá {{patient_name}}!
      
      Sua teleconsulta com *{{professional_name}}* ({{professional_role}}) está agendada:
      
      📅 Data: *{{date}}*
      🕐 Horário: *{{time}}*
      
      Acesse pelo link: {{jitsi_url}}
      
      Dicas:
      • Use Wi-Fi ou 4G
      • Procure um local silencioso
      • Tenha seus exames em mãos
      
      _IntelliCare_

  rocketchat:
    format: markdown
    body: |
      📹 **Teleconsulta Agendada**
      
      **Paciente**: {{patient_name}}
      **Profissional**: {{professional_name}} ({{professional_role}})
      **Data**: {{date}} às {{time}}
      **Link**: [Entrar na Teleconsulta]({{jitsi_url}})

  email:
    format: html
    subject: "[IntelliCare] Teleconsulta — {{date}} às {{time}}"
    body: |
      <div style="font-family: Arial; max-width: 600px; margin: 0 auto;">
        <div style="background: #059669; color: white; padding: 16px; border-radius: 8px 8px 0 0;">
          <h2>📹 Teleconsulta Agendada</h2>
        </div>
        <div style="padding: 20px; border: 1px solid #E5E7EB; border-radius: 0 0 8px 8px;">
          <p><strong>Profissional:</strong> {{professional_name}} ({{professional_role}})</p>
          <p><strong>Data:</strong> {{date}} às {{time}}</p>
          <div style="text-align: center; margin: 24px 0;">
            <a href="{{jitsi_url}}" style="background: #059669; color: white; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-size: 16px;">
              📹 Entrar na Teleconsulta
            </a>
          </div>
          <p style="color: #6B7280; font-size: 14px;">
            Dicas: use Wi-Fi, procure local silencioso, tenha exames em mãos.
          </p>
        </div>
      </div>
```

#### Template 4: `escalation_unread_critical`
```yaml
id: escalation_unread_critical
name: Escalonamento de Alerta Crítico Não Lido
category: ESCALATION
params_schema:
  required: [original_alert, original_recipient, minutes_unread, patient_name]

channel_variants:
  rocketchat:
    format: markdown
    body: |
      🔴 **ESCALONAMENTO AUTOMÁTICO**
      
      Um alerta **CRÍTICO** não foi lido pelo profissional responsável.
      
      **Alerta**: {{original_alert}}
      **Paciente**: {{patient_name}}
      **Destinatário original**: {{original_recipient}}
      **Tempo sem leitura**: {{minutes_unread}} minutos
      
      ⚡ **Ação necessária: verificar imediatamente.**

  push:
    title: "🔴 ESCALONAMENTO — Alerta não lido"
    body: "{{patient_name}}: alerta crítico sem resposta há {{minutes_unread}}min"
```

### 5.4 Motor de Renderização

```python
class TemplateRenderer:
    """Renderiza templates com parâmetros usando Jinja2."""
    
    def __init__(self, template_repository: TemplateRepository):
        self._repo = template_repository
        self._jinja_env = Environment(
            autoescape=False,
            undefined=StrictUndefined  # Erro se parâmetro faltando
        )
    
    async def render(
        self,
        template_id: str,
        channel: str,
        params: Dict
    ) -> RenderedContent:
        """
        Renderiza um template para um canal específico.
        
        1. Busca template do repositório
        2. Valida params contra params_schema
        3. Seleciona variante do canal
        4. Renderiza com Jinja2
        5. Valida resultado (não vazio, max_length)
        6. Retorna RenderedContent
        """
        
    async def preview(
        self,
        template_id: str,
        channel: Optional[str] = None
    ) -> Dict[str, RenderedContent]:
        """Renderiza template com sample_params para preview."""
        
    async def validate_params(
        self, 
        template_id: str, 
        params: Dict
    ) -> List[str]:
        """Valida parâmetros contra schema, retorna lista de erros."""
```

### 5.5 API Endpoints

```yaml
# ── CRUD de Templates ──
POST /api/v1/templates
  Auth: admin
  Body: MessageTemplate
  Response 201: { id: str, version: int }

GET /api/v1/templates
  Auth: admin, care_coordinator
  Query: category, active, page, page_size
  Response 200: { items: List[MessageTemplate], total: int }

GET /api/v1/templates/{id}
  Response 200: MessageTemplate (com todas as variantes)

PUT /api/v1/templates/{id}
  Auth: admin
  Body: MessageTemplate (versão incrementa automaticamente)
  Response 200: { id: str, version: int }

DELETE /api/v1/templates/{id}
  Auth: admin
  Response 200: { deactivated: true }  # Soft-delete

# ── Preview ──
POST /api/v1/templates/{id}/preview
  Description: Renderiza template com dados reais ou de exemplo
  Auth: admin, care_coordinator
  Body (opcional): { params: Dict, channel: Optional[str] }
  Response 200: {
    "rocketchat": { format: "markdown", body: "..." },
    "email": { format: "html", subject: "...", body: "..." },
    "push": { format: "push_json", title: "...", body: "..." },
    ...
  }

# ── Validação ──
POST /api/v1/templates/{id}/validate
  Description: Valida se parâmetros estão corretos para um template
  Body: { params: Dict }
  Response 200: { valid: true, errors: [] }
  Response 200: { valid: false, errors: ["Missing: patient_name", "Invalid: severity"] }
```

### 5.6 Testes Esperados

```
test_templates/
├── test_template_crud.py
│   ├── test_create_template
│   ├── test_get_template
│   ├── test_update_increments_version
│   ├── test_delete_soft_deletes
│   └── test_list_filtered_by_category
├── test_template_renderer.py
│   ├── test_render_clinical_alert_rocketchat
│   ├── test_render_clinical_alert_email
│   ├── test_render_clinical_alert_push
│   ├── test_render_clinical_alert_whatsapp
│   ├── test_render_clinical_alert_sms
│   ├── test_render_with_missing_param_raises_error
│   ├── test_render_sms_respects_max_length
│   ├── test_render_conditional_sections
│   └── test_preview_uses_sample_params
├── test_template_validation.py
│   ├── test_valid_params_pass
│   ├── test_missing_required_param_fails
│   ├── test_wrong_type_param_fails
│   └── test_extra_params_ignored
└── test_initial_templates.py
    ├── test_clinical_alert_generic_exists
    ├── test_medication_reminder_exists
    ├── test_teleconsult_invite_exists
    ├── test_escalation_template_exists
    └── test_all_templates_have_5_channel_variants
```

---

## 6. SCHEMA SQL (MIGRATIONS ALEMBIC)

```sql
-- Migration: 2026_02_15_0001_create_routing_tables.py
-- Schema: comunicacao_operacional

-- Intenções de comunicação
CREATE TABLE comunicacao_operacional.communication_intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_module VARCHAR(100) NOT NULL,
    source_event_id VARCHAR(200),
    recipient_type VARCHAR(20) NOT NULL,
    recipient_id VARCHAR(200) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    category VARCHAR(30) NOT NULL,
    content_template_id VARCHAR(100),
    content_params JSONB,
    content_raw TEXT,
    preferred_channel VARCHAR(30),
    excluded_channels VARCHAR(200)[] DEFAULT '{}',
    require_ack BOOLEAN DEFAULT FALSE,
    max_attempts INT DEFAULT 3,
    scheduled_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    correlation_id VARCHAR(200) NOT NULL,
    parent_intent_id UUID REFERENCES comunicacao_operacional.communication_intents(id),
    metadata JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_to TIMESTAMPTZ NOT NULL DEFAULT '9999-12-31',
    rowversion INT NOT NULL DEFAULT 1
);

CREATE INDEX idx_intents_status ON comunicacao_operacional.communication_intents(status);
CREATE INDEX idx_intents_severity ON comunicacao_operacional.communication_intents(severity);
CREATE INDEX idx_intents_recipient ON comunicacao_operacional.communication_intents(recipient_id);
CREATE INDEX idx_intents_correlation ON comunicacao_operacional.communication_intents(correlation_id);
CREATE INDEX idx_intents_scheduled ON comunicacao_operacional.communication_intents(scheduled_at) WHERE scheduled_at IS NOT NULL;
CREATE INDEX idx_intents_created ON comunicacao_operacional.communication_intents(created_at);

-- Resultados de entrega
CREATE TABLE comunicacao_operacional.delivery_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent_id UUID NOT NULL REFERENCES comunicacao_operacional.communication_intents(id),
    channel VARCHAR(30) NOT NULL,
    attempt_number INT NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    channel_message_id VARCHAR(300),
    channel_room_id VARCHAR(300),
    error_code VARCHAR(50),
    error_message TEXT,
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    latency_send_ms INT,
    latency_deliver_ms INT,
    latency_read_ms INT
);

CREATE INDEX idx_deliveries_intent ON comunicacao_operacional.delivery_results(intent_id);
CREATE INDEX idx_deliveries_status ON comunicacao_operacional.delivery_results(status);
CREATE INDEX idx_deliveries_channel ON comunicacao_operacional.delivery_results(channel);

-- Templates de mensagem
CREATE TABLE comunicacao_operacional.message_templates (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(30) NOT NULL,
    version INT NOT NULL DEFAULT 1,
    channel_variants JSONB NOT NULL,
    params_schema JSONB NOT NULL,
    sample_params JSONB,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    locale VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(200)
);

CREATE INDEX idx_templates_category ON comunicacao_operacional.message_templates(category);
CREATE INDEX idx_templates_active ON comunicacao_operacional.message_templates(active);

-- Regras de roteamento
CREATE TABLE comunicacao_operacional.routing_rules (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    priority INT NOT NULL DEFAULT 100,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    conditions JSONB NOT NULL,
    action JSONB NOT NULL,
    institution_id VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rules_priority ON comunicacao_operacional.routing_rules(priority) WHERE active = TRUE;
```

---

## 7. ESTRUTURA DE CÓDIGO SUGERIDA

```
comunicacao/
├── routing/
│   ├── __init__.py
│   ├── engine.py                 # RoutingEngine principal
│   ├── intent_processor.py       # Processamento de intents
│   ├── rule_matcher.py           # Avaliação de regras
│   ├── fallback_monitor.py       # Monitor de timeout/fallback
│   ├── recipient_resolver.py     # Resolução de destinatários
│   └── models.py                 # CommunicationIntent, DeliveryResult, enums
├── dispatchers/
│   ├── __init__.py
│   ├── base.py                   # IChannelDispatcher, DispatcherManager
│   ├── matrix_dispatcher.py      # Refatorar existente
│   ├── rocketchat_dispatcher.py  # Stub (D2 implementa)
│   ├── push_dispatcher.py        # Stub (D4 implementa)
│   ├── email_dispatcher.py       # Stub (D4 implementa)
│   ├── whatsapp_dispatcher.py    # Stub (D4 implementa)
│   └── sms_dispatcher.py         # Stub (D4 implementa)
├── templates/
│   ├── __init__.py
│   ├── models.py                 # MessageTemplate, ChannelVariant
│   ├── repository.py             # TemplateRepository (PostgreSQL)
│   ├── renderer.py               # TemplateRenderer (Jinja2)
│   ├── validator.py              # Validação de parâmetros
│   └── initial_templates/        # Templates pré-cadastrados em YAML
│       ├── clinical_alert_generic.yml
│       ├── medication_reminder.yml
│       ├── teleconsult_invite.yml
│       ├── escalation_unread.yml
│       └── ...
├── api/
│   ├── routing_routes.py         # Endpoints de roteamento
│   ├── template_routes.py        # Endpoints de templates
│   └── channel_routes.py         # Endpoints de canais
└── tests/
    ├── test_routing_engine/
    ├── test_dispatchers/
    └── test_templates/
```

---

## 8. CRITÉRIOS DE ACEITE CONSOLIDADOS

| # | Critério | Verificação |
|---|----------|-------------|
| 1 | Intent CRITICAL processada em < 500ms | Pytest + benchmark |
| 2 | Intent MEDIUM processada em < 2s | Pytest + benchmark |
| 3 | Fallback acionado dentro do timeout configurado | Teste com mock de falha |
| 4 | Escalonamento cria novo intent com parent_id | Teste unitário |
| 5 | Templates renderizados corretamente para 5+ canais | Teste de snapshot |
| 6 | API retorna 202 para envio assíncrono | Teste de API |
| 7 | Métricas Prometheus incrementadas | Teste de integração |
| 8 | Auth Keycloak em todos os endpoints | Teste de segurança |
| 9 | Idempotência: mesmo UUID não processado 2x | Teste com duplicata |
| 10 | Regras avaliadas em ordem de prioridade | Teste com regras conflitantes |
| 11 | Todas as tentativas geram DeliveryResult | Teste de persistência |
| 12 | Preview de template funciona sem enviar | Teste de API |
| 13 | Cobertura de testes ≥ 80% | pytest-cov |

---

## 9. DEPENDÊNCIAS DE PACOTES

```txt
# requirements.txt (adições para D1)
jinja2>=3.1.2          # Motor de templates
jsonschema>=4.19.0     # Validação de params_schema
pyyaml>=6.0.1          # Leitura de templates YAML
prometheus-client>=0.19.0  # Métricas
```

---

## 10. ENTREGÁVEIS DO DEV

Ao receber esta especificação, o agente DEV responsável pelo Domínio 1 deve entregar:

1. **Especificação Técnica**: Diagrama de classes, sequência, componentes
2. **Plano de Implementação**: Estimativa, ordem de tarefas, riscos
3. **Código**: Implementação completa com testes
4. **Migrations**: Alembic para criar as tabelas
5. **Templates Iniciais**: Pelo menos 5 templates pré-cadastrados
6. **Stubs de Dispatchers**: Para que outros domínios possam integrar
7. **Documentação**: Docstrings + README do domínio

**Prazo estimado**: 2 sprints (S1 + S2)
