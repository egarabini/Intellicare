# EF-015 — Notificacoes em Tempo Real

> Sistema de notificacoes push baseado em eventos MCP com roteamento multi-canal e prioridade.

## 1. Objetivo

Implementar o sistema de notificacoes em tempo real da Geralda, responsavel por:
- Enviar notificacoes ao paciente e equipe baseadas em eventos do MCP
- Rotear por canal correto (Matrix/Synapse, push, SMS, email) conforme urgencia
- Respeitar preferencias LGPD (opt-in, quiet_hours, limites diarios)
- Garantir entrega de notificacoes criticas independente de preferencias
- Rastrear entrega, leitura e acao do destinatario

## 2. Justificativa

- **Proatividade**: Geralda age antes de ser chamada (push, nao pull)
- **Canal certo**: Urgente vai para SMS; educativo vai para email
- **LGPD**: Consentimento explicitamente granular por tipo de notificacao
- **Rastreabilidade**: Saber se o paciente recebeu/leu a informacao
- **Escalacao**: Se nao lido em X minutos (critico), escala automaticamente

## 3. Escopo

### 3.1 Tipos de Notificacao

| Tipo | Severidade | Canal Padrao | Quiet Hours? | Override Critico? |
|------|-----------|--------------|:------------:|:-----------------:|
| Lembrete de medicamento | Medio | WhatsApp | Sim | Nao |
| Lembrete de consulta | Medio | WhatsApp + Push | Sim | Nao |
| Resultado de exame | Medio | WhatsApp | Sim | Nao |
| Material educativo | Baixo | WhatsApp / Email | Sim | Nao |
| Conquista de adesao | Baixo | Matrix / Push | Sim | Nao |
| Orientacao pos-consulta | Medio | WhatsApp | Sim | Nao |
| Alerta de adesao baixa | Alto | Matrix + Push | Nao | Sim |
| Sinal de alerta clinico | Alto | Matrix + SMS | Nao | Sim |
| Alerta equipe — paciente critico | Critico | Rocket.Chat + SMS | Nao | Sim |
| Sinal de reinternacao iminente | Critico | Rocket.Chat + SMS | Nao | Sim |

### 3.2 Motor de Notificacoes

```python
class NotificationEngine:
    """Motor central de notificacoes da Geralda."""

    def __init__(
        self,
        communication_client: CommunicationClient,
        preference_store: PreferenceStore,
        notification_store: NotificationStore,
        escalation_engine: EscalationEngine,
    ):
        ...

    async def notify(
        self,
        notification: NotificationRequest,
    ) -> NotificationResult:
        """
        Processa e envia notificacao.

        Fluxo:
        1. Verificar preferencias do destinatario
        2. Verificar consentimento para o tipo
        3. Verificar quiet_hours (exceto CRITICAL)
        4. Verificar limite diario (exceto CRITICAL)
        5. Selecionar canal(is) de envio
        6. Renderizar template (se aplicavel)
        7. Enviar via CommunicationClient (EF-011)
        8. Registrar intent
        9. Agendar verificacao de entrega/leitura
        """

    async def notify_patient(
        self,
        patient_id: str,
        notification_type: str,
        content: str,
        severity: str = "medium",
        template_id: Optional[str] = None,
        template_vars: Optional[dict] = None,
        schedule_for: Optional[datetime] = None,  # None = imediato
    ) -> NotificationResult:
        """Envia notificacao para o paciente."""

    async def notify_team(
        self,
        unit_id: str,
        notification_type: str,
        content: str,
        severity: str = "medium",
        patient_id: Optional[str] = None,
        channel: str = "rocketchat",
    ) -> NotificationResult:
        """Envia notificacao para a equipe de saude."""

    async def schedule_notification(
        self,
        notification: NotificationRequest,
        scheduled_at: datetime,
    ) -> str:
        """
        Agenda notificacao futura.

        Armazenada em notification_queue para processamento pelo scheduler.
        Retorna scheduled_notification_id.
        """

    async def cancel_scheduled(
        self,
        scheduled_notification_id: str,
    ) -> None:
        """Cancela notificacao agendada (ex: consulta cancelada)."""
```

### 3.3 Roteamento por Severidade e Canal

```python
class NotificationRouter:
    """Define rota de envio baseado em severidade e preferencias."""

    # Regras de roteamento
    ROUTING_RULES = {
        "critical": {
            "channels": ["matrix", "sms", "push"],
            "respect_quiet_hours": False,
            "bypass_daily_limit": True,
            "escalation_timeout_minutes": 5,
        },
        "high": {
            "channels": ["matrix", "push"],
            "respect_quiet_hours": False,
            "bypass_daily_limit": False,
            "escalation_timeout_minutes": 15,
        },
        "medium": {
            "channels": ["preferred"],          # Canal preferido do paciente
            "respect_quiet_hours": True,
            "bypass_daily_limit": False,
            "escalation_timeout_minutes": None,  # Sem escalacao
        },
        "low": {
            "channels": ["preferred_async"],     # Email ou WhatsApp nao urgente
            "respect_quiet_hours": True,
            "bypass_daily_limit": False,
            "escalation_timeout_minutes": None,
        },
    }

    async def route(
        self,
        notification: NotificationRequest,
        preferences: PatientCommPreferences,
    ) -> list[str]:
        """
        Determina canais de envio.

        Considera:
        1. Severidade → regras base
        2. Preferencias do paciente → personaliza
        3. Disponibilidade do canal → fallback
        4. Quiet hours → adia ou ignora
        """
```

### 3.4 Motor de Escalacao

```python
class EscalationEngine:
    """Gerencia escalacao de notificacoes nao lidas."""

    async def schedule_escalation_check(
        self,
        notification_id: str,
        patient_id: str,
        severity: str,
        timeout_minutes: int,
    ) -> None:
        """
        Agenda verificacao de leitura.

        Se timeout expirar sem confirmacao de leitura:
        - HIGH: Reenviar por canal alternativo
        - CRITICAL: Notificar equipe + reenviar
        """

    async def check_and_escalate(
        self,
        notification_id: str,
    ) -> None:
        """
        Verifica se notificacao foi lida e escala se necessario.

        Logica:
        1. Foi lida? → OK, sem acao
        2. Nao foi lida + timeout:
           - HIGH: Tenta SMS se ainda nao enviou
           - CRITICAL: Notifica equipe via Rocket.Chat
        """
```

### 3.5 Fila de Notificacoes Agendadas

```python
class NotificationQueue:
    """Processa fila de notificacoes agendadas."""

    # Executar a cada minuto (scheduler)
    async def process_due_notifications(self) -> None:
        """
        Busca notificacoes com scheduled_at <= now e status=pending.
        Processa ate 100 por ciclo.
        Marca como processing antes de enviar (idempotencia).
        """

    # Agendamentos padrao criados pelo ReminderEngine (EF-001/v1)
    # Notificacoes da jornada (pre-consulta D-7, D-3, D-1, pos-alta D+1, etc.)
    # Lembretes de medicamento (hora especifica do dia)
    # Materiais educativos (config: X dias apos onboarding)
```

### 3.6 Tabelas

```sql
-- Notificacoes
CREATE TABLE notifications (
    id BIGSERIAL PRIMARY KEY,
    notification_id UUID UNIQUE NOT NULL,
    patient_id VARCHAR(64),
    unit_id VARCHAR(64),
    recipient_type VARCHAR(20) NOT NULL,    -- patient, team
    notification_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    title VARCHAR(200),
    content TEXT NOT NULL,
    template_id VARCHAR(50),
    template_vars JSONB DEFAULT '{}',

    -- Status
    status VARCHAR(20) DEFAULT 'pending',   -- pending, sent, delivered, read, failed
    channel VARCHAR(50),                    -- Canal efetivo usado
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    failed_reason TEXT,

    -- Agendamento
    scheduled_for TIMESTAMPTZ,             -- NULL = enviar agora

    -- Escalacao
    escalation_checked BOOLEAN DEFAULT FALSE,
    escalated BOOLEAN DEFAULT FALSE,
    escalated_at TIMESTAMPTZ,

    -- Rastreabilidade
    trigger_event_id UUID,
    care_plan_id UUID,
    created_by VARCHAR(100) DEFAULT 'geralda',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_patient ON notifications(patient_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_for)
    WHERE status = 'pending' AND scheduled_for IS NOT NULL;
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_date ON notifications(created_at);
```

### 3.7 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/notifications/send` | Enviar notificacao |
| POST | `/api/v1/notifications/schedule` | Agendar notificacao |
| DELETE | `/api/v1/notifications/scheduled/{id}` | Cancelar agendada |
| GET | `/api/v1/notifications/patient/{patient_id}` | Historico paciente |
| GET | `/api/v1/notifications/patient/{patient_id}/pending` | Pendentes |
| PUT | `/api/v1/notifications/{id}/read` | Marcar como lida |
| GET | `/api/v1/notifications/stats` | Metricas de entrega |

### 3.8 Metricas

```python
# Taxa de entrega por canal
delivery_rate = Counter("geralda_notifications_delivery_total", "Total entregues", ["channel", "type"])
delivery_failures = Counter("geralda_notifications_failures_total", "Total falhas", ["channel", "reason"])

# Taxa de leitura
read_rate = Histogram("geralda_notifications_read_rate", "Taxa de leitura por tipo", ["type"])

# Tempo ate leitura
read_latency = Histogram("geralda_notification_read_latency_seconds", "Tempo ate leitura", ["severity"])

# Escalacoes
escalations_total = Counter("geralda_notifications_escalated_total", "Total escalados", ["severity"])
```

## 4. Testes

- NotificationEngine: notify, notify_team, schedule, cancel (8 testes)
- NotificationRouter: cada severidade, quiet_hours, fallback (8 testes)
- EscalationEngine: sem escalacao, escalacao HIGH, escalacao CRITICAL (5 testes)
- NotificationQueue: process_due, idempotencia, max_batch (4 testes)
- LGPD rules: consent, quiet_hours, daily_limit, critical_bypass (5 testes)
- Endpoints: todos 7 (5 testes)
- Integracao: evento MCP → notificacao → entrega → escalacao (3 testes)
- **Total**: 38+ testes

## 5. Criterios de Aceitacao

- [ ] 10+ tipos de notificacao catalogados
- [ ] Roteamento por severidade (critical, high, medium, low)
- [ ] Quiet hours respeitadas (exceto CRITICAL)
- [ ] Limite diario de mensagens respeitado
- [ ] Override CRITICAL sempre envia
- [ ] Motor de escalacao funcional (5min/15min)
- [ ] Fila agendada processada a cada minuto
- [ ] Rastreamento de status (sent, delivered, read)
- [ ] Metricas Prometheus
- [ ] 7 endpoints funcionais
- [ ] 38+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~3 (api, scheduler, docker)
- **Linhas estimadas**: ~1.600
- **Testes novos**: ~38
