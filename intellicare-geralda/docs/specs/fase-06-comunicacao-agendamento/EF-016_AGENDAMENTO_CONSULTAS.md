# EF-016 — Agendamento de Consultas e Teleconsultas

> Agendamento de consultas presenciais e teleconsultas via Jitsi, com gestao completa do ciclo de vida da sessao.

## 1. Objetivo

Implementar o modulo de agendamento integrado da Geralda, responsavel por:
- Agendar consultas presenciais e teleconsultas
- Gerar links de teleconsulta Jitsi com JWT assinado
- Gerenciar ciclo de vida da sessao (agendado → lembrete → link → em andamento → concluido)
- Registrar pos-consulta e criar follow-up
- Integrar com FHIR Encounter para rastreabilidade clinica
- Detectar no-show automaticamente

## 2. Justificativa

- **Teleconsulta**: Paciente com DRC em pos-alta nao precisa se deslocar
- **Automacao**: Link de videoconferencia gerado e enviado automaticamente
- **Continuidade**: Cada consulta conectada ao plano de cuidado
- **No-show**: Deteccao automatica evita tempo de profissional perdido
- **FHIR**: Cada consulta gera Encounter FHIR auditavel

## 3. Escopo

### 3.1 Tipos de Consulta

| Tipo | Canal | Gerenciado por | Jitsi JWT |
|------|-------|---------------|:---------:|
| `follow_up` | Teleconsulta | Geralda/Comunicacao | Sim |
| `initial` | Presencial ou Teleconsulta | Geralda | Opcional |
| `urgent` | Teleconsulta prioritaria | Geralda | Sim |
| `lab_review` | Teleconsulta | Geralda | Sim |
| `care_plan_review` | Teleconsulta | Geralda | Sim |
| `multidisciplinary` | Teleconsulta (multiplos) | Geralda | Sim |
| `pos_alta` | Teleconsulta (7-14d pos alta) | Geralda automatico | Sim |

### 3.2 Servico de Agendamento

```python
class ConsultationService:
    """Gerencia agendamento e ciclo de vida de consultas."""

    def __init__(
        self,
        jitsi_token_generator: JitsiTokenGenerator,
        notification_engine: NotificationEngine,
        fhir_sync: FHIRSync,
        consultation_repo: ConsultationRepository,
    ):
        ...

    async def schedule(
        self,
        patient_id: str,
        consultation_type: str,
        specialist: str,
        scheduled_datetime: datetime,
        unit_id: str,
        is_teleconsult: bool = False,
        professional_id: str = None,
        duration_minutes: int = 30,
        notes: Optional[str] = None,
    ) -> Consultation:
        """
        Agenda consulta.

        Fluxo:
        1. Criar registro da consulta
        2. Se teleconsulta:
           a. Gerar room_id unico (intellicare-{uuid_short})
           b. Gerar JWT para profissional (moderador=True)
           c. Gerar JWT para paciente (moderador=False)
           d. Montar link completo: https://meet.gsi.srv.br/{room_id}
        3. Criar registro FHIR Appointment
        4. Agendar lembretes (D-7, D-3, D-1, D-0)
        5. Agendar envio do link (D-0, 30min antes)
        6. Emitir evento operational.consultation_scheduled
        7. Notificar profissional via Rocket.Chat
        """

    async def cancel(
        self,
        consultation_id: str,
        reason: str,
        cancelled_by: str,
    ) -> None:
        """
        Cancela consulta.

        1. Atualizar status para 'cancelled'
        2. Cancelar lembretes agendados
        3. Cancelar envio de link
        4. Notificar paciente sobre cancelamento
        5. Notificar profissional
        6. Atualizar FHIR Appointment
        7. Emitir operational.consultation_cancelled
        """

    async def reschedule(
        self,
        consultation_id: str,
        new_datetime: datetime,
        reason: str,
    ) -> Consultation:
        """
        Reagenda consulta.

        1. Cancelar lembretes antigos
        2. Atualizar data/hora
        3. Regenerar JWTs (se teleconsulta)
        4. Criar novos lembretes
        5. Notificar paciente e profissional
        """

    async def complete(
        self,
        consultation_id: str,
        post_data: PostConsultationData,
    ) -> None:
        """
        Marca consulta como concluida.

        1. Atualizar status para 'completed'
        2. Criar FHIR Encounter com status=finished
        3. Registrar notas pos-consulta (EF-013)
        4. Criar follow-up tasks
        5. Agendar follow-up D+1, D+3, D+7
        """

    async def detect_no_show(
        self,
        consultation_id: str,
    ) -> None:
        """
        Detecta no-show automatico.

        Executado T+10min apos hora agendada.
        Se status ainda 'link_sent' ou 'reminder_sent':
        - Marcar como 'no_show'
        - Notificar equipe
        - Criar task para reagendamento
        - Emitir operational.consultation_missed
        """
```

### 3.3 Gerador de JWT Jitsi

```python
class JitsiTokenGenerator:
    """Gera JWT tokens para autenticacao no Jitsi Meet."""

    def __init__(
        self,
        app_id: str,       # ex: "jitsi-meet"
        app_secret: str,   # JWT_APP_SECRET do Jitsi
        domain: str,       # ex: "meet.gsi.srv.br"
        token_ttl: int = 3600,  # 1 hora
    ):
        ...

    def generate_professional_token(
        self,
        room_id: str,
        professional_id: str,
        professional_name: str,
        professional_email: str,
        enable_recording: bool = True,
    ) -> JitsiToken:
        """
        Gera JWT para profissional de saude (moderador).

        Payload:
        {
            "aud": "jitsi",
            "iss": "jitsi-meet",
            "sub": "meet.gsi.srv.br",
            "room": "intellicare-{room_id}",
            "exp": <timestamp + ttl>,
            "nbf": <timestamp>,
            "context": {
                "user": {
                    "id": "<professional_id>",
                    "name": "<professional_name>",
                    "email": "<professional_email>",
                    "avatar": "<url>",
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

    def generate_patient_token(
        self,
        room_id: str,
        patient_id: str,
        patient_name: str,
    ) -> JitsiToken:
        """
        Gera JWT para paciente (nao moderador).

        Payload similar, mas:
        - moderator: false
        - recording: false
        - screen-sharing: false
        """

    def generate_guest_token(
        self,
        room_id: str,
        guest_name: str,
    ) -> JitsiToken:
        """
        Gera JWT para acompanhante/familiar (guest).

        Moderador: false, sem gravacao.
        """

    def build_meeting_url(
        self,
        room_id: str,
        token: str,
    ) -> str:
        """
        Monta URL completa de entrada na reuniao.

        https://meet.gsi.srv.br/intellicare-{room_id}?jwt={token}
        """
```

### 3.4 Ciclo de Vida da Sessao

```
scheduled
    │
    ├─ D-7: Lembrete inicial
    │
    ├─ D-3: Checklist pre-consulta (EF-013)
    │
    ├─ D-1: Resumo + instrucoes ("O que levar")
    │
    ├─ D-0 T-30min: Enviar link de acesso
    │       └─ status → link_sent
    │
    ├─ Profissional entra
    │       └─ status → professional_joined
    │
    ├─ Paciente entra
    │       └─ status → patient_joined → in_progress
    │
    ├─ Consulta encerrada
    │       └─ status → completed
    │       └─ FHIR Encounter gerado
    │       └─ Follow-up iniciado (EF-013)
    │
    └─ T+10min sem entrada
            └─ status → no_show
            └─ Equipe notificada
```

### 3.5 Sala de Caso Multidisciplinar

```python
class CaseRoomService:
    """Gerencia salas de discussao de caso multidisciplinar."""

    async def create_case_room(
        self,
        patient_id: str,
        room_type: str,       # patient_review, team_meeting, incident_review
        participants: list[str],
        scheduled_at: datetime,
        recurrence: Optional[str] = None,   # weekly, biweekly, monthly
        agenda: Optional[str] = None,
    ) -> CaseRoom:
        """
        Cria sala multidisciplinar.

        Gera JWT para cada participante (todos moderadores).
        Cria link unico por sessao.
        """

    async def generate_meeting_minutes(
        self,
        case_room_id: str,
        recording_transcript: Optional[str] = None,
    ) -> str:
        """
        Gera ata da reuniao via LLM.

        Se transcript disponivel (via Jitsi gravacao):
        - LLM resume pontos discutidos
        - LLM extrai decisoes tomadas
        - LLM lista action items com responsaveis

        Se sem transcript:
        - Template de ata para preenchimento manual
        """

    async def post_minutes_to_rocketchat(
        self,
        case_room_id: str,
        minutes: str,
    ) -> None:
        """Publica ata no canal #caso-{patient_id} do Rocket.Chat."""
```

### 3.6 Tabela de Consultas

```sql
-- Consultas (presenciais e teleconsultas)
CREATE TABLE consultations (
    id BIGSERIAL PRIMARY KEY,
    consultation_id UUID UNIQUE NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    journey_id UUID,
    unit_id VARCHAR(64),
    professional_id VARCHAR(64),

    -- Detalhes
    consultation_type VARCHAR(30) NOT NULL,
    specialist VARCHAR(100),
    is_teleconsult BOOLEAN DEFAULT FALSE,
    duration_minutes INTEGER DEFAULT 30,
    scheduled_at TIMESTAMPTZ NOT NULL,
    notes TEXT,

    -- Status
    status VARCHAR(30) DEFAULT 'scheduled',
    -- scheduled, reminder_sent, link_sent,
    -- professional_joined, patient_joined, in_progress,
    -- completed, no_show, cancelled, rescheduled

    -- Jitsi
    jitsi_room_id VARCHAR(100),
    jitsi_professional_jwt TEXT,
    jitsi_patient_jwt TEXT,
    jitsi_meeting_url_professional VARCHAR(500),
    jitsi_meeting_url_patient VARCHAR(500),
    jwt_expires_at TIMESTAMPTZ,

    -- Pos-consulta
    completed_at TIMESTAMPTZ,
    fhir_encounter_id VARCHAR(100),

    -- Cancelamento/Reagendamento
    cancelled_at TIMESTAMPTZ,
    cancelled_by VARCHAR(100),
    cancel_reason TEXT,
    rescheduled_to UUID,

    -- Timestamps
    reminder_d7_sent_at TIMESTAMPTZ,
    reminder_d3_sent_at TIMESTAMPTZ,
    reminder_d1_sent_at TIMESTAMPTZ,
    link_sent_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_consultations_patient ON consultations(patient_id);
CREATE INDEX idx_consultations_scheduled ON consultations(scheduled_at);
CREATE INDEX idx_consultations_status ON consultations(status);
CREATE INDEX idx_consultations_pending_link ON consultations(scheduled_at, status)
    WHERE status IN ('scheduled', 'reminder_sent');

-- Salas multidisciplinares
CREATE TABLE case_rooms (
    id BIGSERIAL PRIMARY KEY,
    room_id UUID UNIQUE NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    room_type VARCHAR(30) NOT NULL,
    participants JSONB NOT NULL DEFAULT '[]',
    scheduled_at TIMESTAMPTZ NOT NULL,
    recurrence VARCHAR(20),
    agenda TEXT,
    status VARCHAR(20) DEFAULT 'scheduled',
    jitsi_room_id VARCHAR(100),
    meeting_minutes TEXT,
    rocketchat_posted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.7 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/consultations` | Agendar consulta |
| GET | `/api/v1/consultations/{id}` | Detalhes da consulta |
| GET | `/api/v1/consultations/{id}/link` | Link para paciente |
| PUT | `/api/v1/consultations/{id}/cancel` | Cancelar |
| PUT | `/api/v1/consultations/{id}/reschedule` | Reagendar |
| PUT | `/api/v1/consultations/{id}/complete` | Concluir |
| GET | `/api/v1/consultations/patient/{patient_id}` | Historico |
| GET | `/api/v1/consultations/upcoming` | Proximas consultas (equipe) |
| POST | `/api/v1/case-rooms` | Criar sala multidisciplinar |
| GET | `/api/v1/case-rooms/{id}/minutes` | Ata da reuniao |

### 3.8 Configuracao

```env
# Jitsi
INTELLICARE_JITSI_DOMAIN=meet.gsi.srv.br
INTELLICARE_JITSI_APP_ID=jitsi-meet
INTELLICARE_JITSI_APP_SECRET=<secret>
INTELLICARE_JITSI_TOKEN_TTL=3600

# Agendamento
INTELLICARE_CONSULTATION_REMINDER_D7=true
INTELLICARE_CONSULTATION_REMINDER_D3=true
INTELLICARE_CONSULTATION_REMINDER_D1=true
INTELLICARE_CONSULTATION_LINK_ADVANCE_MINUTES=30
INTELLICARE_CONSULTATION_NOSHOW_TIMEOUT_MINUTES=10
```

## 4. Testes

- ConsultationService: schedule, cancel, reschedule, complete (8 testes)
- JitsiTokenGenerator: professional, patient, guest, URL (6 testes)
- NoShowDetector: sem no-show, com no-show, teleconsult (4 testes)
- CaseRoomService: create, minutes, rocketchat (4 testes)
- Lifecycle scheduler: lembretes, link, no-show detection (6 testes)
- FHIR Encounter: geracao, sincronizacao (3 testes)
- Endpoints: todos 10 (6 testes)
- Integracao: agendar → lembretes → link → concluir → follow-up (3 testes)
- **Total**: 40+ testes

## 5. Criterios de Aceitacao

- [ ] Agendamento de consultas presenciais e teleconsultas
- [ ] JWT Jitsi para profissional (moderador) e paciente (guest)
- [ ] Link de teleconsulta enviado T-30min automaticamente
- [ ] Ciclo de vida completo (scheduled → completed / no_show)
- [ ] Deteccao de no-show T+10min
- [ ] Cancelamento e reagendamento com notificacoes
- [ ] Sala multidisciplinar com geracao de ata via LLM
- [ ] FHIR Encounter criado ao concluir
- [ ] Follow-up automatico pos-consulta (EF-013)
- [ ] 10 endpoints funcionais
- [ ] 40+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~5 (api, scheduler, notification_engine, fhir_sync, docker)
- **Linhas estimadas**: ~1.800
- **Testes novos**: ~40
