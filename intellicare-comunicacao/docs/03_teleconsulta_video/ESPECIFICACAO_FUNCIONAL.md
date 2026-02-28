# Domínio 3 — Teleconsulta e Vídeo
## Especificação Funcional Detalhada

**Identificadores**: EF-COM-020, EF-COM-021  
**Prioridade Global**: ALTA  
**Sprint**: S3–S4  
**Dependências**: D1 (roteamento), D2 (canais RC para notificação)  
**Dependentes**: D4 (notificações externas de convite), D5 (eventos), D7 (métricas)

---

## 1. OBJETIVO

Implementar o módulo de teleconsulta e salas de caso multidisciplinar, utilizando Jitsi Meet (`https://meet.gsi.srv.br`) como backend de videoconferência, com:

1. **Agendamento inteligente** de teleconsultas (profissional ↔ paciente)
2. **Geração de salas Jitsi** com JWT autenticado via Keycloak
3. **Salas de caso multidisciplinar** (reuniões de equipe sobre pacientes)
4. **Detecção de no-show** com reescalonamento automático
5. **Registro FHIR** (Encounter) para conformidade
6. **Integração WhatsApp/SMS** para envio de links ao paciente

**Estado Atual**: Jitsi Meet operacional com Keycloak SSO em `https://meet.gsi.srv.br`. Nenhuma integração programática com IntelliCare. Salas são criadas manualmente.

---

## 2. CONTEXTO ARQUITETURAL

```
┌──────────────────────────────────────────────────────────┐
│                    Paciente (celular)                     │
│                                                          │
│    WhatsApp ◄────── Link Jitsi ──────► Navegador         │
│                                           │              │
└───────────────────────────────────────────┼──────────────┘
                                            │
                                 https://meet.gsi.srv.br
                                            │
┌───────────────────────────────────────────┼──────────────┐
│                       JITSI MEET          │              │
│  ┌──────────┐  ┌──────────┐  ┌───────────┴───────────┐  │
│  │ Prosody  │  │ Jicofo   │  │  Jitsi Videobridge    │  │
│  │ (XMPP)   │  │ (Focus)  │  │  (SFU)                │  │
│  └────┬─────┘  └──────────┘  └───────────────────────┘  │
│       │ JWT Auth                                         │
└───────┼──────────────────────────────────────────────────┘
        │
┌───────┼──────────────────────────────────────────────────┐
│       │        intellicare-comunicacao                    │
│  ┌────┴─────────────────────────────────────────┐        │
│  │         TeleconsultService                    │        │
│  │  • Agenda sessões                             │        │
│  │  • Gera JWT para Jitsi                        │        │
│  │  • Monitora no-show                           │        │
│  │  • Registra FHIR Encounter                    │        │
│  └──────────────────────────────────────────────┘        │
│                                                          │
│  ┌──────────────────────────────────────────────┐        │
│  │         CaseRoomService                       │        │
│  │  • Cria salas de caso multidisciplinar        │        │
│  │  • Agenda reuniões recorrentes                │        │
│  │  • Gera atas automáticas (summary)            │        │
│  └──────────────────────────────────────────────┘        │
│                                                          │
│  ┌──────────────────────────────────────────────┐        │
│  │         JitsiJWTGenerator                     │        │
│  │  • Assina tokens JWT para autenticação Jitsi  │        │
│  └──────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────┘
```

---

## 3. EF-COM-020 — Agendamento de Teleconsultas

### 3.1 Modelo de Dados

```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class TeleconsultStatus(str, Enum):
    """Estado da teleconsulta."""
    SCHEDULED = "scheduled"           # Agendada, aguardando
    REMINDER_SENT = "reminder_sent"   # Lembrete enviado (30min antes)
    LINK_SENT = "link_sent"           # Link enviado ao paciente
    PROFESSIONAL_JOINED = "professional_joined"   # Profissional entrou
    PATIENT_JOINED = "patient_joined"             # Paciente entrou
    IN_PROGRESS = "in_progress"       # Ambos presentes, consulta ativa
    COMPLETED = "completed"           # Finalizada normalmente
    NO_SHOW_PATIENT = "no_show_patient"     # Paciente não compareceu
    NO_SHOW_PROFESSIONAL = "no_show_professional"  # Profissional não compareceu
    CANCELLED = "cancelled"           # Cancelada
    RESCHEDULED = "rescheduled"       # Reagendada


class TeleconsultType(str, Enum):
    """Tipo de teleconsulta."""
    FOLLOW_UP = "follow_up"           # Retorno / acompanhamento
    URGENT = "urgent"                 # Urgência (prioridade alta)
    INITIAL = "initial"               # Primeira consulta
    LAB_REVIEW = "lab_review"         # Revisão de exames
    CARE_PLAN_REVIEW = "care_plan_review"  # Revisão de plano de cuidado
    MULTIDISCIPLINARY = "multidisciplinary"  # Equipe multidisciplinar


class TeleconsultSession(BaseModel):
    """Sessão de teleconsulta."""
    
    id: UUID = Field(default_factory=uuid4)
    
    # Participantes
    patient_id: str
    patient_name: str
    patient_phone: Optional[str]      # Para envio de link via WhatsApp/SMS
    professional_id: str
    professional_name: str
    professional_role: str            # "doctor", "nurse", etc.
    
    # Agendamento
    session_type: TeleconsultType
    scheduled_at: datetime            # Horário agendado
    duration_minutes: int = 30        # Duração planejada
    timezone: str = "America/Sao_Paulo"
    
    # Jitsi
    jitsi_room_name: str              # intellicare-{uuid_short}
    jitsi_url: str                    # https://meet.gsi.srv.br/intellicare-xxx
    jitsi_jwt_professional: Optional[str]   # JWT para o profissional
    jitsi_jwt_patient: Optional[str]        # JWT para o paciente (guest)
    
    # Status
    status: TeleconsultStatus = TeleconsultStatus.SCHEDULED
    
    # Timestamps reais
    professional_joined_at: Optional[datetime]
    patient_joined_at: Optional[datetime]
    started_at: Optional[datetime]           # Quando ambos entraram
    ended_at: Optional[datetime]
    actual_duration_minutes: Optional[int]
    
    # Notificações
    link_sent_at: Optional[datetime]         # Quando link foi enviado
    link_sent_via: Optional[str]             # "whatsapp" | "sms" | "rocketchat"
    reminder_sent_at: Optional[datetime]
    no_show_detected_at: Optional[datetime]
    
    # FHIR
    fhir_encounter_id: Optional[str]         # ID do Encounter gerado
    
    # Notas
    professional_notes: Optional[str]        # Notas pós-consulta
    follow_up_needed: Optional[bool]
    follow_up_days: Optional[int]            # Reagendar em X dias
    
    # Relacionamentos
    origin_alert_id: Optional[str]           # Se originada de um alerta
    origin_care_plan_id: Optional[str]       # Se parte de plano de cuidado
    rescheduled_from: Optional[UUID]         # ID da sessão anterior (se reagendada)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str                          # user_id de quem agendou
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TeleconsultScheduleRequest(BaseModel):
    """Request para agendar teleconsulta."""
    patient_id: str
    professional_id: str
    session_type: TeleconsultType = TeleconsultType.FOLLOW_UP
    scheduled_at: datetime
    duration_minutes: int = 30
    send_link_via: str = "whatsapp"        # "whatsapp" | "sms" | "both" | "none"
    notes: Optional[str]
    origin_alert_id: Optional[str]
    origin_care_plan_id: Optional[str]


class TeleconsultScheduleResponse(BaseModel):
    """Response do agendamento."""
    session_id: UUID
    jitsi_url: str
    jitsi_jwt_professional: str
    scheduled_at: datetime
    status: TeleconsultStatus
    link_sent: bool
    link_sent_via: Optional[str]
```

### 3.2 JitsiJWTGenerator

```python
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional

class JitsiJWTGenerator:
    """Gera tokens JWT para autenticação no Jitsi Meet."""
    
    def __init__(self, config: JitsiConfig):
        self._config = config
    
    def generate(
        self,
        room_name: str,
        user_name: str,
        user_email: str,
        user_id: str,
        is_moderator: bool = False,
        avatar_url: Optional[str] = None,
        duration_minutes: int = 120
    ) -> str:
        """
        Gera JWT compatível com Jitsi.
        
        Payload JWT (padrão Jitsi):
        {
            "aud": "jitsi",
            "iss": "<APP_ID>",
            "sub": "meet.gsi.srv.br",
            "room": "intellicare-xxx",
            "exp": <timestamp>,
            "nbf": <timestamp>,
            "context": {
                "user": {
                    "id": "<keycloak_user_id>",
                    "name": "Dr. João Silva",
                    "email": "joao@gsi.srv.br",
                    "avatar": "",
                    "moderator": true
                },
                "features": {
                    "livestreaming": false,
                    "recording": true,
                    "screen-sharing": true
                }
            }
        }
        """
        now = datetime.utcnow()
        
        payload = {
            "aud": "jitsi",
            "iss": self._config.app_id,
            "sub": self._config.domain,
            "room": room_name,
            "exp": int((now + timedelta(minutes=duration_minutes)).timestamp()),
            "nbf": int((now - timedelta(minutes=5)).timestamp()),
            "context": {
                "user": {
                    "id": user_id,
                    "name": user_name,
                    "email": user_email,
                    "avatar": avatar_url or "",
                    "moderator": is_moderator
                },
                "features": {
                    "livestreaming": False,
                    "recording": self._config.allow_recording,
                    "screen-sharing": True
                }
            }
        }
        
        return jwt.encode(
            payload, 
            self._config.app_secret, 
            algorithm="HS256"
        )


class JitsiConfig(BaseModel):
    """Configuração do Jitsi."""
    domain: str = "meet.gsi.srv.br"
    base_url: str = "https://meet.gsi.srv.br"
    app_id: str = "intellicare"         # JWT_APP_ID configurado no Jitsi
    app_secret: str                      # JWT_APP_SECRET
    room_prefix: str = "intellicare-"    # Prefixo das salas
    allow_recording: bool = True
    default_duration_minutes: int = 30
    max_duration_minutes: int = 120
    no_show_timeout_minutes: int = 10    # Tempo para considerar no-show
    reminder_before_minutes: int = 30    # Enviar lembrete X min antes
```

### 3.3 TeleconsultService

```python
class TeleconsultService:
    """Serviço principal de teleconsulta."""
    
    def __init__(
        self,
        db: AsyncSession,
        jwt_generator: JitsiJWTGenerator,
        routing_engine: RoutingEngine,       # Para enviar notificações
        rc_channel_service: RocketChatChannelService,
        patient_client: PatientClient,       # Para buscar dados do paciente
    ):
        self._db = db
        self._jwt = jwt_generator
        self._routing = routing_engine
        self._rc = rc_channel_service
        self._patients = patient_client
    
    async def schedule(self, request: TeleconsultScheduleRequest, created_by: str) -> TeleconsultScheduleResponse:
        """
        Agenda teleconsulta.
        
        Fluxo:
        1. Validar que profissional e paciente existem
        2. Verificar conflitos de horário
        3. Gerar nome de sala Jitsi (intellicare-{uuid[:8]})
        4. Gerar JWTs (profissional como moderador, paciente como guest)
        5. Criar TeleconsultSession no banco
        6. Agendar jobs de:
           a. Envio de link ao paciente (imediato ou X min antes)
           b. Lembrete 30 min antes
           c. Verificação de no-show (scheduled_at + 10 min)
        7. Notificar profissional via RC
        8. Publicar evento: teleconsult.scheduled → Redis Stream
        9. Retornar URL e JWT
        """
    
    async def cancel(self, session_id: UUID, cancelled_by: str, reason: Optional[str] = None) -> TeleconsultSession:
        """
        Cancela teleconsulta.
        
        Fluxo:
        1. Atualizar status → CANCELLED
        2. Cancelar jobs agendados (lembrete, no-show)
        3. Notificar profissional e paciente
        4. Publicar evento: teleconsult.cancelled → Redis Stream
        """
    
    async def reschedule(self, session_id: UUID, new_time: datetime, rescheduled_by: str) -> TeleconsultScheduleResponse:
        """
        Reagenda teleconsulta.
        
        Fluxo:
        1. Cancelar sessão atual
        2. Criar nova sessão com rescheduled_from = session_id original
        3. Notificar ambos com novo horário
        4. Publicar evento: teleconsult.rescheduled → Redis Stream
        """
    
    async def register_join(self, session_id: UUID, user_id: str, user_type: str) -> TeleconsultSession:
        """
        Registra que profissional ou paciente entrou na sala.
        
        Chamado via webhook do Jitsi (participant_joined).
        
        Fluxo:
        1. Se user_type == "professional":
           - session.professional_joined_at = now
           - session.status = PROFESSIONAL_JOINED
        2. Se user_type == "patient":
           - session.patient_joined_at = now
           - session.status = PATIENT_JOINED
        3. Se ambos presentes:
           - session.started_at = now
           - session.status = IN_PROGRESS
           - Cancelar job de no-show
        """
    
    async def register_end(self, session_id: UUID) -> TeleconsultSession:
        """
        Registra fim da teleconsulta.
        
        Chamado via webhook do Jitsi (conference_destroyed) ou pelo profissional.
        
        Fluxo:
        1. session.ended_at = now
        2. session.actual_duration_minutes = (ended_at - started_at).minutes
        3. session.status = COMPLETED
        4. Criar FHIR Encounter
        5. Publicar evento: teleconsult.completed → Redis Stream
        """
    
    async def check_no_show(self, session_id: UUID) -> None:
        """
        Verifica no-show (chamado pelo scheduler no scheduled_at + 10 min).
        
        Fluxo:
        1. Buscar sessão
        2. Se status ainda é SCHEDULED ou LINK_SENT:
           a. Se profissional não entrou → NO_SHOW_PROFESSIONAL
           b. Se paciente não entrou → NO_SHOW_PATIENT
        3. Notificar coordenador de cuidado
        4. Se no-show do paciente e origin_care_plan_id:
           → Marcar tarefa como "não realizada" no plano de cuidado
        5. Publicar evento: teleconsult.no_show → Redis Stream
        """
    
    async def add_notes(self, session_id: UUID, notes: str, follow_up_needed: bool, follow_up_days: Optional[int]) -> TeleconsultSession:
        """
        Profissional adiciona notas pós-consulta.
        
        Fluxo:
        1. Atualizar session.professional_notes
        2. Se follow_up_needed e follow_up_days:
           a. schedule(nova_consulta, scheduled_at = now + follow_up_days)
        3. Publicar evento: teleconsult.notes_added → Redis Stream
        """
    
    async def get_upcoming(self, professional_id: str, hours_ahead: int = 24) -> List[TeleconsultSession]:
        """Retorna teleconsultas das próximas X horas do profissional."""
    
    async def get_patient_history(self, patient_id: str) -> List[TeleconsultSession]:
        """Retorna histórico de teleconsultas do paciente."""
    
    async def get_daily_stats(self, date: Optional[datetime] = None) -> Dict:
        """Estatísticas do dia: total, completadas, no-show, duração média."""
```

### 3.4 Fluxo Detalhado de Agendamento

```
=== AGENDAMENTO DE TELECONSULTA ===

Profissional (Dr. João) via Portal/RC/Bot:
    POST /api/v1/teleconsult/schedule
    {
        patient_id: "P001",
        professional_id: "PROF-001",
        session_type: "follow_up",
        scheduled_at: "2026-02-20T14:00:00-03:00",
        duration_minutes: 30,
        send_link_via: "whatsapp"
    }
    │
    ▼
TeleconsultService.schedule():
    │
    ├── 1. Validar participantes
    │      GET Wanda /api/v1/patients/P001 → { name: "Maria Santos", phone: "+5511999…" }
    │      GET Keycloak /admin/realms/bemcuidar/users/PROF-001 → { name: "Dr. João" }
    │
    ├── 2. Verificar conflitos
    │      SELECT * FROM teleconsult_sessions
    │      WHERE professional_id = 'PROF-001'
    │        AND scheduled_at BETWEEN '14:00' AND '14:30'
    │        AND status NOT IN ('cancelled', 'rescheduled', 'completed')
    │      → Se encontrou → RAISE ConflictError
    │
    ├── 3. Gerar sala Jitsi
    │      room_name = "intellicare-a1b2c3d4"
    │      jitsi_url = "https://meet.gsi.srv.br/intellicare-a1b2c3d4"
    │
    ├── 4. Gerar JWTs
    │      jwt_professional = JitsiJWTGenerator.generate(
    │          room=room_name, user="Dr. João", moderator=True)
    │      jwt_patient = JitsiJWTGenerator.generate(
    │          room=room_name, user="Maria Santos", moderator=False)
    │
    ├── 5. Criar sessão no banco
    │      INSERT INTO teleconsult_sessions (...)
    │
    ├── 6. Enviar link ao paciente via WhatsApp
    │      RoutingEngine.route(CommunicationIntent(
    │          intent_type=TELECONSULT_INVITE,
    │          recipient_type=PATIENT,
    │          recipient_id="P001",
    │          severity=HIGH,
    │          channels=[WHATSAPP],
    │          payload={
    │              url: jitsi_url + "?jwt=" + jwt_patient,
    │              professional_name: "Dr. João Silva",
    │              date: "20/02/2026",
    │              time: "14:00",
    │              type: "Retorno"
    │          }
    │      ))
    │
    ├── 7. Enviar confirmação ao profissional via RC
    │      RC DM ao Dr. João:
    │      📹 **Teleconsulta Agendada**
    │      Paciente: Maria Santos
    │      Data: 20/02/2026 às 14:00
    │      Tipo: Retorno
    │      Link: https://meet.gsi.srv.br/intellicare-a1b2c3d4?jwt=xxx
    │      [Entrar na Sala]
    │
    ├── 8. Agendar jobs:
    │      a. reminder_job: em (scheduled_at - 30min) → enviar lembrete
    │      b. no_show_job: em (scheduled_at + 10min) → check_no_show
    │
    └── 9. Publicar Redis Stream: teleconsult.scheduled
           { session_id, patient_id, professional_id, scheduled_at, type }


=== 30 MIN ANTES — LEMBRETE ===

Scheduler → reminder_job:
    │
    ├── Enviar WhatsApp ao paciente:
    │   "Olá Maria! Sua teleconsulta com Dr. João é em 30 minutos (14:00).
    │    Acesse pelo link: [link]. Certifique-se de estar em local silencioso
    │    com boa conexão de internet."
    │
    └── Enviar RC DM ao profissional:
        "📹 Lembrete: Teleconsulta com Maria Santos em 30 minutos."


=== DURANTE A SESSÃO ===

Jitsi Webhook → participant_joined:
    │
    ├── Identificar participante pelo JWT user_id
    │
    ├── register_join(session_id, user_id, "professional")
    │   → session.professional_joined_at = now
    │   → status = PROFESSIONAL_JOINED
    │
    └── register_join(session_id, user_id, "patient")
        → session.patient_joined_at = now
        → Se profissional já presente:
           → session.started_at = now
           → status = IN_PROGRESS
           → Cancelar no_show_job


Jitsi Webhook → conference_destroyed:
    │
    └── register_end(session_id)
        → session.ended_at = now
        → session.actual_duration_minutes = 25
        → status = COMPLETED
        → Criar FHIR Encounter
        → Publicar teleconsult.completed


=== NO-SHOW (scheduled_at + 10 min) ===

Scheduler → no_show_job:
    │
    ├── check_no_show(session_id)
    │
    ├── Se paciente não entrou (status ≠ IN_PROGRESS):
    │   → status = NO_SHOW_PATIENT
    │   → Notificar profissional: "Paciente Maria Santos não compareceu."
    │   → Notificar coordenador de cuidado
    │   → Se tem care_plan_id: atualizar tarefa como "não realizada"
    │   → Publicar teleconsult.no_show
    │
    └── Se profissional não entrou (status ≠ IN_PROGRESS):
        → status = NO_SHOW_PROFESSIONAL
        → Notificar paciente (reagendar sugestão)
        → Notificar coordenador/admin
        → Publicar teleconsult.no_show
```

### 3.5 Templates de Notificação

```python
TELECONSULT_TEMPLATES = {
    "teleconsult_invite": {
        "whatsapp": {
            "template_name": "teleconsulta_convite",
            "body": (
                "Olá {{patient_name}}!\n\n"
                "Sua teleconsulta foi agendada:\n"
                "📋 Tipo: {{session_type}}\n"
                "👨‍⚕️ Profissional: {{professional_name}}\n"
                "📅 Data: {{date}}\n"
                "🕐 Horário: {{time}}\n\n"
                "Para participar, clique no link abaixo no horário marcado:\n"
                "🔗 {{jitsi_url}}\n\n"
                "💡 Dicas:\n"
                "• Use Wi-Fi ou 4G\n"
                "• Fique em local silencioso\n"
                "• Permita acesso à câmera e microfone\n\n"
                "Em caso de dúvidas, responda esta mensagem."
            )
        },
        "sms": {
            "body": (
                "IntelliCare: Teleconsulta com {{professional_name}} "
                "em {{date}} {{time}}. Acesse: {{jitsi_url}}"
            )
        },
        "rocketchat": {
            "body": (
                "📹 **Teleconsulta Agendada**\n"
                "Paciente: {{patient_name}}\n"
                "Data: {{date}} às {{time}}\n"
                "Tipo: {{session_type}}\n"
                "[Entrar na Sala]({{jitsi_url}})"
            )
        }
    },
    "teleconsult_reminder": {
        "whatsapp": {
            "body": (
                "Olá {{patient_name}}!\n\n"
                "Lembrete: sua teleconsulta com {{professional_name}} "
                "é em {{minutes_until}} minutos ({{time}}).\n\n"
                "🔗 Acesse: {{jitsi_url}}\n\n"
                "Certifique-se de estar em local com boa conexão."
            )
        },
        "sms": {
            "body": (
                "IntelliCare: Lembrete! Teleconsulta em {{minutes_until}} min. "
                "Acesse: {{jitsi_url}}"
            )
        }
    },
    "teleconsult_no_show": {
        "rocketchat": {
            "body": (
                "⚠️ **No-Show Detectado**\n"
                "Teleconsulta: {{session_id}}\n"
                "Paciente: {{patient_name}}\n"
                "Horário: {{scheduled_time}}\n"
                "Tipo: {{no_show_type}}\n\n"
                "Ação recomendada: {{recommended_action}}"
            )
        }
    }
}
```

---

## 4. EF-COM-021 — Salas de Caso Multidisciplinar

### 4.1 Descrição Funcional

Salas de caso são reuniões periódicas por vídeo onde a equipe multidisciplinar discute pacientes complexos. Diferem de teleconsultas individuais:

| Aspecto | Teleconsulta | Sala de Caso |
|---|---|---|
| Participantes | 1 profissional + 1 paciente | N profissionais (sem paciente) |
| Frequência | Pontual, agendada | Recorrente (semanal/quinzenal) |
| Objetivo | Atendimento clínico | Discussão de casos, decisão de equipe |
| Registro | FHIR Encounter | Ata + decisões |
| Canal RC | DM ao profissional | #caso-{patient_id} |

### 4.2 Modelo de Dados

```python
class CaseRoomStatus(str, Enum):
    PLANNED = "planned"
    ACTIVE = "active"                  # Reunião em andamento
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CaseRoomType(str, Enum):
    PATIENT_REVIEW = "patient_review"       # Revisão de paciente específico
    TEAM_MEETING = "team_meeting"           # Reunião de equipe geral
    INCIDENT_REVIEW = "incident_review"     # Revisão de incidente/evento adverso


class CaseRoom(BaseModel):
    """Sala de caso multidisciplinar."""
    
    id: UUID = Field(default_factory=uuid4)
    
    # Contexto
    room_type: CaseRoomType
    title: str                            # "Revisão — Maria Santos (P001)"
    description: Optional[str]            # Pauta da reunião
    patient_id: Optional[str]             # Se room_type == PATIENT_REVIEW
    patient_name: Optional[str]
    team_id: str                          # Equipe responsável
    
    # Reunião
    scheduled_at: datetime
    duration_minutes: int = 60
    recurrence: Optional[str]             # "weekly" | "biweekly" | "monthly" | None
    next_occurrence: Optional[datetime]
    
    # Participantes
    participants: List[CaseRoomParticipant]
    
    # Jitsi
    jitsi_room_name: str     
    jitsi_url: str
    
    # Status
    status: CaseRoomStatus = CaseRoomStatus.PLANNED
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    
    # Ata
    summary: Optional[str]                # Resumo/ata
    decisions: Optional[List[str]]        # Decisões tomadas
    action_items: Optional[List[CaseRoomAction]]  # Ações definidas
    
    # RC
    rc_channel_id: Optional[str]          # #caso-{patient_id} no RC
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str


class CaseRoomParticipant(BaseModel):
    """Participante de uma sala de caso."""
    user_id: str
    username: str
    role: str                              # "doctor", "nurse", etc.
    is_presenter: bool = False             # Quem apresenta o caso
    attended: bool = False                 # Marcado após reunião
    joined_at: Optional[datetime]
    left_at: Optional[datetime]


class CaseRoomAction(BaseModel):
    """Ação definida na reunião."""
    id: UUID = Field(default_factory=uuid4)
    description: str                       # "Solicitar ecocardiograma"
    assigned_to: str                       # user_id do responsável
    assigned_to_name: str
    due_date: Optional[datetime]
    status: str = "pending"                # "pending" | "completed" | "cancelled"
    completed_at: Optional[datetime]


class CaseRoomCreateRequest(BaseModel):
    """Request para criar sala de caso."""
    room_type: CaseRoomType
    title: str
    description: Optional[str]
    patient_id: Optional[str]              # Requerido se PATIENT_REVIEW
    team_id: str
    scheduled_at: datetime
    duration_minutes: int = 60
    recurrence: Optional[str]
    participant_ids: List[str]             # user_ids dos participantes
```

### 4.3 CaseRoomService

```python
class CaseRoomService:
    """Serviço de salas de caso multidisciplinar."""
    
    def __init__(
        self,
        db: AsyncSession,
        jwt_generator: JitsiJWTGenerator,
        rc_channel_service: RocketChatChannelService,
        patient_client: PatientClient,
    ):
        self._db = db
        self._jwt = jwt_generator
        self._rc = rc_channel_service
        self._patients = patient_client
    
    async def create(self, request: CaseRoomCreateRequest, created_by: str) -> CaseRoom:
        """
        Cria sala de caso.
        
        Fluxo:
        1. Validar participantes e paciente (se aplicável)
        2. Gerar sala Jitsi
        3. Buscar/criar canal RC #caso-{patient_id} ou #equipe-{team_id}
        4. Salvar CaseRoom no banco
        5. Enviar convite para todos os participantes via RC
        6. Se recurrence: agendar próxima ocorrência
        7. Publicar evento: case_room.created → Redis Stream
        """
    
    async def start(self, room_id: UUID) -> CaseRoom:
        """
        Inicia reunião (quando primeiro participante entra).
        
        Fluxo:
        1. status = ACTIVE
        2. started_at = now
        3. Enviar mensagem no canal RC: "🟢 Reunião iniciada: {title}"
        """
    
    async def end(self, room_id: UUID) -> CaseRoom:
        """
        Finaliza reunião.
        
        Fluxo:
        1. status = COMPLETED
        2. ended_at = now
        3. Enviar resumo no canal RC
        4. Se recurrence: criar próxima ocorrência
        5. Publicar evento: case_room.completed → Redis Stream
        """
    
    async def add_summary(self, room_id: UUID, summary: str, decisions: List[str], action_items: List[Dict]) -> CaseRoom:
        """
        Adiciona ata/resumo pós-reunião.
        
        Fluxo:
        1. Atualizar summary, decisions, action_items
        2. Enviar ata formatada no canal RC #caso-{patient_id}
        3. Para cada action_item: criar task no plano de cuidado (via Geralda API se aplicável)
        4. Publicar evento: case_room.minutes_added → Redis Stream
        """
    
    async def get_upcoming(self, team_id: str) -> List[CaseRoom]:
        """Lista próximas reuniões da equipe."""
    
    async def get_patient_case_rooms(self, patient_id: str) -> List[CaseRoom]:
        """Histórico de reuniões sobre um paciente."""
    
    async def handle_recurrence(self, room_id: UUID) -> Optional[CaseRoom]:
        """
        Cria próxima ocorrência baseada na recurrence.
        
        Se recurrence == "weekly" → next = last + 7 dias
        Se recurrence == "biweekly" → next = last + 14 dias
        Se recurrence == "monthly" → next = last + 30 dias
        """
```

### 4.4 Fluxo — Sala de Caso Multidisciplinar

```
=== CRIAÇÃO DE SALA DE CASO ===

Coordenador (Ana) via Portal:
    POST /api/v1/case-room
    {
        room_type: "patient_review",
        title: "Revisão Semanal — Maria Santos (P001)",
        patient_id: "P001",
        team_id: "EQUIPE-UBS-CENTRO",
        scheduled_at: "2026-02-19T10:00:00-03:00",
        duration_minutes: 60,
        recurrence: "weekly",
        participant_ids: ["PROF-001", "PROF-002", "PROF-003"]
    }
    │
    ▼
CaseRoomService.create():
    │
    ├── 1. Buscar dados do paciente P001 (Wanda)
    │      → { name: "Maria Santos", conditions: ["DM2", "HAS", "DRC 3a"] }
    │
    ├── 2. Buscar/criar canal RC #caso-P001
    │      → { channel_id: "room_abc" }
    │
    ├── 3. Gerar sala Jitsi: intellicare-case-e5f6g7h8
    │
    ├── 4. Gerar JWTs para todos os participantes
    │
    ├── 5. Salvar no banco
    │
    ├── 6. Enviar convites via RC para cada participante:
    │      📋 **Reunião de Caso — Maria Santos (P001)**
    │      📅 Quarta-feira, 19/02/2026 às 10:00 (semanal)
    │      ⏱️ Duração: 60 min
    │      
    │      **Pauta Sugerida**:
    │      • Revisão de exames recentes (eGFR: 28.5 ↓)
    │      • Ajuste do plano de cuidado
    │      • Avaliação de adesão medicamentosa
    │      
    │      **Participantes**: Dr. João, Enf. Maria, Nut. Carlos
    │      
    │      [Entrar na Sala](https://meet.gsi.srv.br/intellicare-case-e5f6g7h8)
    │
    ├── 7. Pinar mensagem no #caso-P001 com resumo clínico atualizado
    │
    └── 8. Agendar: lembrete 30min antes + recorrência semanal


=== PÓS-REUNIÃO — ATA ===

Coordenador (Ana) via Portal:
    POST /api/v1/case-room/{room_id}/summary
    {
        summary: "Revisão de Maria Santos. eGFR em queda (28.5). Decisão de encaminhar a nefrologia e ajustar metformina.",
        decisions: [
            "Encaminhar para nefrologia com urgência",
            "Reduzir metformina de 2000mg para 1000mg",
            "Solicitar ultrassom renal"
        ],
        action_items: [
            {
                description: "Solicitar encaminhamento para nefrologia",
                assigned_to: "PROF-001",
                due_date: "2026-02-20"
            },
            {
                description: "Ajustar prescrição de metformina",
                assigned_to: "PROF-001",
                due_date: "2026-02-19"
            },
            {
                description: "Agendar ultrassom renal",
                assigned_to: "PROF-002",
                due_date: "2026-02-21"
            }
        ]
    }
    │
    ▼
Mensagem no #caso-P001:
    📝 **Ata — Reunião 19/02/2026**
    
    **Resumo**: Revisão de Maria Santos. eGFR em queda (28.5). 
    Decisão de encaminhar a nefrologia e ajustar metformina.
    
    **Decisões**:
    1. ✅ Encaminhar para nefrologia com urgência
    2. ✅ Reduzir metformina de 2000mg para 1000mg
    3. ✅ Solicitar ultrassom renal
    
    **Ações Pendentes**:
    | # | Ação | Responsável | Prazo |
    |---|------|-------------|-------|
    | 1 | Solicitar encaminhamento nefrologia | Dr. João | 20/02 |
    | 2 | Ajustar prescrição metformina | Dr. João | 19/02 |
    | 3 | Agendar ultrassom renal | Enf. Maria | 21/02 |
    
    Próxima reunião: 26/02/2026 10:00
```

---

## 5. FHIR ENCOUNTER

### 5.1 Mapeamento Teleconsulta → FHIR Encounter

```python
class FHIREncounterBuilder:
    """Constrói recurso FHIR Encounter a partir de TeleconsultSession."""
    
    def build(self, session: TeleconsultSession) -> Dict:
        """
        Gera Encounter FHIR R4.
        
        Referência: https://hl7.org/fhir/encounter.html
        """
        return {
            "resourceType": "Encounter",
            "id": str(session.id),
            "status": self._map_status(session.status),
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "VR",                  # Virtual
                "display": "virtual"
            },
            "type": [{
                "coding": [{
                    "system": "http://intellicare.gsi.srv.br/fhir/encounter-type",
                    "code": session.session_type.value,
                    "display": self._type_display(session.session_type)
                }]
            }],
            "subject": {
                "reference": f"Patient/{session.patient_id}",
                "display": session.patient_name
            },
            "participant": [{
                "individual": {
                    "reference": f"Practitioner/{session.professional_id}",
                    "display": session.professional_name
                },
                "type": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        "code": "ATND",
                        "display": "attender"
                    }]
                }]
            }],
            "period": {
                "start": session.started_at.isoformat() if session.started_at else session.scheduled_at.isoformat(),
                "end": session.ended_at.isoformat() if session.ended_at else None
            },
            "length": {
                "value": session.actual_duration_minutes or session.duration_minutes,
                "unit": "min",
                "system": "http://unitsofmeasure.org",
                "code": "min"
            },
            "reasonCode": self._build_reason_codes(session),
            "serviceProvider": {
                "reference": "Organization/intellicare",
                "display": "IntelliCare - Plataforma de Saúde Inteligente"
            },
            "extension": [{
                "url": "http://intellicare.gsi.srv.br/fhir/teleconsult-metadata",
                "extension": [
                    {"url": "jitsi-room", "valueString": session.jitsi_room_name},
                    {"url": "no-show", "valueBoolean": session.status in [
                        TeleconsultStatus.NO_SHOW_PATIENT,
                        TeleconsultStatus.NO_SHOW_PROFESSIONAL
                    ]},
                    {"url": "link-sent-via", "valueString": session.link_sent_via or "none"}
                ]
            }]
        }
    
    def _map_status(self, status: TeleconsultStatus) -> str:
        mapping = {
            TeleconsultStatus.SCHEDULED: "planned",
            TeleconsultStatus.IN_PROGRESS: "in-progress",
            TeleconsultStatus.COMPLETED: "finished",
            TeleconsultStatus.CANCELLED: "cancelled",
            TeleconsultStatus.NO_SHOW_PATIENT: "cancelled",
            TeleconsultStatus.NO_SHOW_PROFESSIONAL: "cancelled",
        }
        return mapping.get(status, "unknown")
```

---

## 6. API ENDPOINTS

```yaml
# ── Teleconsultas ──
POST /api/v1/teleconsult/schedule
  Description: Agenda uma teleconsulta
  Auth: Keycloak (doctor, nurse, care_coordinator)
  Body: TeleconsultScheduleRequest
  Response 201: TeleconsultScheduleResponse

GET /api/v1/teleconsult/{session_id}
  Description: Detalhes de uma teleconsulta
  Auth: Keycloak (participantes da sessão, admin)
  Response 200: TeleconsultSession

PUT /api/v1/teleconsult/{session_id}/cancel
  Description: Cancela teleconsulta
  Auth: Keycloak (participantes, admin)
  Body: { reason: Optional[str] }
  Response 200: TeleconsultSession

PUT /api/v1/teleconsult/{session_id}/reschedule
  Description: Reagenda teleconsulta
  Auth: Keycloak (participantes, admin)
  Body: { new_scheduled_at: datetime }
  Response 200: TeleconsultScheduleResponse

PUT /api/v1/teleconsult/{session_id}/join
  Description: Registra entrada de participante
  Auth: Keycloak (participantes)
  Body: { user_type: "professional" | "patient" }
  Response 200: TeleconsultSession

PUT /api/v1/teleconsult/{session_id}/end
  Description: Registra fim da teleconsulta
  Auth: Keycloak (moderador/profissional)
  Response 200: TeleconsultSession

POST /api/v1/teleconsult/{session_id}/notes
  Description: Adiciona notas pós-consulta
  Auth: Keycloak (professional da sessão)
  Body: { notes: str, follow_up_needed: bool, follow_up_days: Optional[int] }
  Response 200: TeleconsultSession

GET /api/v1/teleconsult/upcoming
  Description: Próximas teleconsultas do profissional
  Auth: Keycloak (professional autenticado)
  Query: hours_ahead (default: 24)
  Response 200: List[TeleconsultSession]

GET /api/v1/teleconsult/patient/{patient_id}/history
  Description: Histórico de teleconsultas do paciente
  Auth: Keycloak (equipe do paciente, admin)
  Query: page, page_size
  Response 200: { items: List[TeleconsultSession], total: int }

GET /api/v1/teleconsult/stats
  Description: Estatísticas de teleconsulta
  Auth: Keycloak (admin, care_coordinator)
  Query: date (default: hoje), period (day|week|month)
  Response 200: {
    total: int,
    completed: int,
    no_show_patient: int,
    no_show_professional: int,
    cancelled: int,
    avg_duration_minutes: float,
    avg_wait_time_minutes: float
  }

# ── Salas de Caso ──
POST /api/v1/case-room
  Description: Cria sala de caso multidisciplinar
  Auth: Keycloak (doctor, care_coordinator, admin)
  Body: CaseRoomCreateRequest
  Response 201: CaseRoom

GET /api/v1/case-room/{room_id}
  Description: Detalhes da sala de caso
  Auth: Keycloak (participantes, admin)
  Response 200: CaseRoom

PUT /api/v1/case-room/{room_id}/start
  Description: Inicia reunião
  Auth: Keycloak (participantes)
  Response 200: CaseRoom

PUT /api/v1/case-room/{room_id}/end
  Description: Finaliza reunião
  Auth: Keycloak (participantes, admin)
  Response 200: CaseRoom

POST /api/v1/case-room/{room_id}/summary
  Description: Adiciona ata/resumo
  Auth: Keycloak (participantes, admin)
  Body: { summary: str, decisions: List[str], action_items: List }
  Response 200: CaseRoom

GET /api/v1/case-room/upcoming
  Description: Próximas reuniões da equipe
  Auth: Keycloak
  Query: team_id, days_ahead (default: 7)
  Response 200: List[CaseRoom]

GET /api/v1/case-room/patient/{patient_id}
  Description: Histórico de reuniões sobre um paciente
  Auth: Keycloak (equipe do paciente, admin)
  Response 200: List[CaseRoom]

# ── Webhooks Jitsi ──
POST /api/v1/webhooks/jitsi
  Description: Recebe eventos do Jitsi (participant_joined, conference_destroyed, etc.)
  Auth: Token compartilhado
  Response 200: { status: "ok" }
```

---

## 7. SCHEMA SQL

```sql
-- Migration: 2026_02_15_0003_create_teleconsult_tables.py
-- Schema: comunicacao_operacional

-- Sessões de teleconsulta
CREATE TABLE comunicacao_operacional.teleconsult_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Participantes
    patient_id VARCHAR(200) NOT NULL,
    patient_name VARCHAR(300) NOT NULL,
    patient_phone VARCHAR(50),
    professional_id VARCHAR(200) NOT NULL,
    professional_name VARCHAR(300) NOT NULL,
    professional_role VARCHAR(50) NOT NULL,
    
    -- Agendamento
    session_type VARCHAR(50) NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 30,
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Sao_Paulo',
    
    -- Jitsi
    jitsi_room_name VARCHAR(200) NOT NULL UNIQUE,
    jitsi_url VARCHAR(500) NOT NULL,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',
    
    -- Timestamps reais
    professional_joined_at TIMESTAMPTZ,
    patient_joined_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    actual_duration_minutes INT,
    
    -- Notificações
    link_sent_at TIMESTAMPTZ,
    link_sent_via VARCHAR(50),
    reminder_sent_at TIMESTAMPTZ,
    no_show_detected_at TIMESTAMPTZ,
    
    -- FHIR
    fhir_encounter_id VARCHAR(200),
    
    -- Notas
    professional_notes TEXT,
    follow_up_needed BOOLEAN DEFAULT FALSE,
    follow_up_days INT,
    
    -- Relacionamentos
    origin_alert_id VARCHAR(200),
    origin_care_plan_id VARCHAR(200),
    rescheduled_from UUID REFERENCES comunicacao_operacional.teleconsult_sessions(id),
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(200) NOT NULL
);

CREATE INDEX idx_teleconsult_patient ON comunicacao_operacional.teleconsult_sessions(patient_id);
CREATE INDEX idx_teleconsult_professional ON comunicacao_operacional.teleconsult_sessions(professional_id);
CREATE INDEX idx_teleconsult_scheduled ON comunicacao_operacional.teleconsult_sessions(scheduled_at);
CREATE INDEX idx_teleconsult_status ON comunicacao_operacional.teleconsult_sessions(status);
CREATE INDEX idx_teleconsult_room ON comunicacao_operacional.teleconsult_sessions(jitsi_room_name);

-- Salas de caso multidisciplinar
CREATE TABLE comunicacao_operacional.case_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Contexto
    room_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    patient_id VARCHAR(200),
    patient_name VARCHAR(300),
    team_id VARCHAR(200) NOT NULL,
    
    -- Reunião
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 60,
    recurrence VARCHAR(20),
    next_occurrence TIMESTAMPTZ,
    
    -- Jitsi
    jitsi_room_name VARCHAR(200) NOT NULL UNIQUE,
    jitsi_url VARCHAR(500) NOT NULL,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'planned',
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    
    -- Ata
    summary TEXT,
    decisions JSONB DEFAULT '[]',
    
    -- RC
    rc_channel_id VARCHAR(100),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(200) NOT NULL
);

CREATE INDEX idx_case_room_patient ON comunicacao_operacional.case_rooms(patient_id);
CREATE INDEX idx_case_room_team ON comunicacao_operacional.case_rooms(team_id);
CREATE INDEX idx_case_room_scheduled ON comunicacao_operacional.case_rooms(scheduled_at);
CREATE INDEX idx_case_room_status ON comunicacao_operacional.case_rooms(status);

-- Participantes de salas de caso
CREATE TABLE comunicacao_operacional.case_room_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_room_id UUID NOT NULL REFERENCES comunicacao_operacional.case_rooms(id) ON DELETE CASCADE,
    user_id VARCHAR(200) NOT NULL,
    username VARCHAR(200) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_presenter BOOLEAN NOT NULL DEFAULT FALSE,
    attended BOOLEAN NOT NULL DEFAULT FALSE,
    joined_at TIMESTAMPTZ,
    left_at TIMESTAMPTZ,
    
    UNIQUE(case_room_id, user_id)
);

CREATE INDEX idx_participant_room ON comunicacao_operacional.case_room_participants(case_room_id);
CREATE INDEX idx_participant_user ON comunicacao_operacional.case_room_participants(user_id);

-- Ações definidas em reuniões
CREATE TABLE comunicacao_operacional.case_room_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_room_id UUID NOT NULL REFERENCES comunicacao_operacional.case_rooms(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    assigned_to VARCHAR(200) NOT NULL,
    assigned_to_name VARCHAR(300) NOT NULL,
    due_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    completed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_action_room ON comunicacao_operacional.case_room_actions(case_room_id);
CREATE INDEX idx_action_assigned ON comunicacao_operacional.case_room_actions(assigned_to);
CREATE INDEX idx_action_status ON comunicacao_operacional.case_room_actions(status);

-- View analítica consolidada
CREATE OR REPLACE VIEW comunicacao_operacional.v_teleconsult_stats AS
SELECT 
    DATE(scheduled_at AT TIME ZONE 'America/Sao_Paulo') AS date,
    session_type,
    status,
    COUNT(*) as total,
    AVG(actual_duration_minutes) FILTER (WHERE status = 'completed') as avg_duration,
    AVG(EXTRACT(EPOCH FROM (patient_joined_at - scheduled_at))/60) 
        FILTER (WHERE patient_joined_at IS NOT NULL) as avg_wait_minutes,
    COUNT(*) FILTER (WHERE status = 'no_show_patient') as no_shows_patient,
    COUNT(*) FILTER (WHERE status = 'no_show_professional') as no_shows_professional
FROM comunicacao_operacional.teleconsult_sessions
GROUP BY 1, 2, 3;
```

---

## 8. ESTRUTURA DE CÓDIGO

```
comunicacao/
├── teleconsult/
│   ├── __init__.py
│   ├── service.py                  # TeleconsultService
│   ├── models.py                   # TeleconsultSession, enums, request/response
│   ├── jitsi_jwt.py                # JitsiJWTGenerator
│   ├── jitsi_config.py             # JitsiConfig
│   ├── fhir_encounter.py           # FHIREncounterBuilder
│   ├── scheduler.py                # Jobs de lembrete/no-show (APScheduler)
│   └── templates.py                # TELECONSULT_TEMPLATES
├── case_room/
│   ├── __init__.py
│   ├── service.py                  # CaseRoomService
│   ├── models.py                   # CaseRoom, CaseRoomParticipant, CaseRoomAction
│   └── recurrence.py               # Lógica de recorrência
├── api/
│   ├── teleconsult_routes.py       # FastAPI routes
│   ├── case_room_routes.py         # FastAPI routes
│   └── jitsi_webhook_routes.py     # Webhook handler
└── tests/
    ├── test_teleconsult/
    │   ├── test_service.py
    │   ├── test_jitsi_jwt.py
    │   ├── test_fhir_encounter.py
    │   ├── test_scheduler.py
    │   └── test_no_show.py
    ├── test_case_room/
    │   ├── test_service.py
    │   ├── test_recurrence.py
    │   └── test_actions.py
    └── test_api/
        ├── test_teleconsult_routes.py
        ├── test_case_room_routes.py
        └── test_jitsi_webhook.py
```

---

## 9. TESTES ESPERADOS

```
test_teleconsult/
├── test_service.py
│   ├── test_schedule_creates_session
│   ├── test_schedule_generates_jitsi_room
│   ├── test_schedule_sends_link_via_whatsapp
│   ├── test_schedule_sends_confirmation_via_rc
│   ├── test_schedule_conflict_raises_error
│   ├── test_cancel_updates_status
│   ├── test_cancel_notifies_participants
│   ├── test_reschedule_creates_new_session
│   ├── test_reschedule_links_to_original
│   ├── test_register_join_professional
│   ├── test_register_join_patient
│   ├── test_both_joined_starts_session
│   ├── test_register_end_completes_session
│   ├── test_register_end_creates_fhir_encounter
│   ├── test_add_notes_with_follow_up
│   ├── test_add_notes_schedules_next_session
│   ├── test_get_upcoming_returns_correct_sessions
│   └── test_patient_history_ordered_by_date
├── test_jitsi_jwt.py
│   ├── test_generate_valid_jwt
│   ├── test_jwt_contains_correct_room
│   ├── test_jwt_moderator_flag
│   ├── test_jwt_guest_flag
│   ├── test_jwt_expiration_correct
│   └── test_jwt_decodes_with_secret
├── test_no_show.py
│   ├── test_no_show_patient_detected
│   ├── test_no_show_professional_detected
│   ├── test_no_show_cancelled_if_session_started
│   ├── test_no_show_notifies_coordinator
│   └── test_no_show_updates_care_plan
├── test_fhir_encounter.py
│   ├── test_encounter_from_completed_session
│   ├── test_encounter_status_mapping
│   ├── test_encounter_virtual_class
│   └── test_encounter_contains_metadata
└── test_scheduler.py
    ├── test_reminder_sent_30min_before
    ├── test_no_show_check_triggered_10min_after
    └── test_jobs_cancelled_on_session_cancel

test_case_room/
├── test_service.py
│   ├── test_create_room
│   ├── test_create_room_creates_rc_channel
│   ├── test_create_room_sends_invites
│   ├── test_start_room
│   ├── test_end_room
│   ├── test_add_summary
│   ├── test_summary_posted_to_rc
│   ├── test_action_items_created
│   └── test_get_upcoming_by_team
├── test_recurrence.py
│   ├── test_weekly_recurrence
│   ├── test_biweekly_recurrence
│   ├── test_monthly_recurrence
│   └── test_no_recurrence_no_next
└── test_actions.py
    ├── test_create_action_item
    ├── test_complete_action_item
    └── test_overdue_actions_flagged
```

---

## 10. CONFIGURAÇÃO (Variáveis de Ambiente)

```bash
# Jitsi
JITSI_DOMAIN=meet.gsi.srv.br
JITSI_BASE_URL=https://meet.gsi.srv.br
JITSI_APP_ID=intellicare
JITSI_APP_SECRET=<JWT_APP_SECRET do Jitsi>
JITSI_ROOM_PREFIX=intellicare-
JITSI_ALLOW_RECORDING=true
JITSI_WEBHOOK_URL=https://<comunicacao_url>/api/v1/webhooks/jitsi
JITSI_WEBHOOK_TOKEN=<token_seguro>

# Teleconsulta
TELECONSULT_DEFAULT_DURATION=30
TELECONSULT_MAX_DURATION=120
TELECONSULT_NO_SHOW_TIMEOUT=10
TELECONSULT_REMINDER_BEFORE=30
TELECONSULT_DEFAULT_LINK_CHANNEL=whatsapp

# Scheduler (APScheduler)
SCHEDULER_TIMEZONE=America/Sao_Paulo
SCHEDULER_JOB_STORE=postgresql  # ou redis
```

---

## 11. PREREQUISITOS E SETUP

1. **JWT no Jitsi**: Confirmar que Prosody aceita JWT com APP_ID = "intellicare"
   - Verificar `ENABLE_AUTH=1`, `AUTH_TYPE=jwt`, `JWT_APP_ID`, `JWT_APP_SECRET` no docker-compose do Jitsi

2. **Webhook do Jitsi**: Configurar `org.jitsi.omp.jibri` ou mod_webhook no Prosody para enviar eventos (`participant_joined`, `conference_destroyed`) para o IntelliCare

3. **APScheduler**: Instalar e configurar para jobs de lembrete e no-show. Pode usar PostgreSQL como job store para persistência.

4. **Dependências Python**:
   ```
   PyJWT>=2.8.0
   APScheduler>=3.10.4
   aiohttp>=3.9.0
   ```

---

## 12. ENTREGÁVEIS DO DEV

1. **Especificação Técnica**: Diagramas de sequência completos
2. **Plano de Implementação**: Ordem: JitsiJWT → TeleconsultService → CaseRoomService → Webhooks → Scheduler
3. **Código**: Tudo acima com testes ≥ 80%
4. **Migrations**: Alembic para todas as tabelas
5. **Configuração Jitsi**: Script/playbook para configurar webhooks no Jitsi
6. **Documentação**: README + docstrings + exemplos de uso

**Prazo estimado**: 2 sprints (S3 + S4)
