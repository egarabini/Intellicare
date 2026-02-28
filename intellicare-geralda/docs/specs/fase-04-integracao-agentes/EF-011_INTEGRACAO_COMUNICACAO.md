# EF-011 — Integracao com Modulo de Comunicacao

> Integrar Geralda ao intellicare-comunicacao para envio de mensagens, notificacoes e interacao com pacientes via Synapse/Matrix.

## 1. Objetivo

Conectar a Geralda ao modulo de comunicacao (intellicare-comunicacao) para:
- Enviar mensagens ao paciente via canal preferido (Synapse, WhatsApp, SMS, email)
- Receber mensagens do paciente (inbound) e processar via LLM
- Utilizar o bot Geralda no Matrix/Element como interface
- Disparar notificacoes baseadas em eventos do MCP
- Respeitar preferencias LGPD do paciente (opt-in, horarios, canal)

## 2. Justificativa

- **Canal direto**: Paciente precisa receber orientacoes no canal que ele usa
- **Tempo real**: Alertas criticos devem chegar imediatamente
- **Interatividade**: Paciente pode tirar duvidas via chat
- **LGPD**: Respeitar preferencias e consentimento do paciente
- **Automacao**: Mensagens de protocolo disparam automaticamente

## 3. Escopo

### 3.1 Canais Suportados

| Canal | Biblioteca | Status no Comunicacao | Uso Geralda |
|-------|-----------|----------------------|-------------|
| Matrix/Synapse | `matrix-nio` | Operacional | Chat paciente-equipe |
| Rocket.Chat | API REST | Operacional | Alertas para equipe |
| WhatsApp | API (planejado) | Nao implementado | Lembretes, orientacoes |
| SMS | Gateway (planejado) | Nao implementado | Alertas criticos |
| Email | SMTP (planejado) | Nao implementado | Resumos, educacao |
| Push | FCM/APNS (planejado) | Nao implementado | Alertas mobile |

### 3.2 Arquitetura de Integracao

```
                    ┌──────────────────────┐
                    │   Geralda            │
                    │   (Motor de Cuidado) │
                    └────────┬─────────────┘
                             │
                    ┌────────▼─────────────┐
                    │  CommunicationClient  │
                    │  (Abstrai canais)     │
                    └────────┬─────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
     │ Matrix/Synapse │ │Rocket.   │ │ Routing     │
     │ (Paciente)     │ │Chat      │ │ Engine      │
     │                │ │(Equipe)  │ │(Multi-canal)│
     └────────────────┘ └──────────┘ └─────────────┘
              ▲                              │
              │                    ┌─────────┼─────────┐
     Paciente responde             WhatsApp  SMS  Email
     via Element
```

### 3.3 Cliente de Comunicacao

```python
class CommunicationClient:
    """Cliente unificado para envio de mensagens via intellicare-comunicacao."""

    def __init__(self, comunicacao_url: str, timeout: int = 30):
        self._url = comunicacao_url  # ex: "http://comunicacao:8005"
        self._timeout = timeout

    async def send_message(
        self,
        patient_id: str,
        message: str,
        channel: str = "preferred",     # preferred, matrix, whatsapp, sms, email
        severity: str = "medium",       # low, medium, high, critical
        template_id: Optional[str] = None,
        template_vars: Optional[dict] = None,
        respect_quiet_hours: bool = True,
    ) -> MessageResult:
        """
        Envia mensagem ao paciente via routing engine do Comunicacao.

        POST {comunicacao_url}/api/v1/routing/send
        {
            "patient_id": "patient-123",
            "message": "Ola Joao, lembre-se de tomar...",
            "channel": "preferred",
            "severity": "medium",
            "source": "geralda",
            "template_id": "medication_reminder",
            "template_vars": {"medication": "Losartana", "time": "08:00"},
            "respect_quiet_hours": true,
        }

        Returns:
            MessageResult com status (sent, queued, blocked, failed)
        """

    async def send_to_team(
        self,
        unit_id: str,
        message: str,
        channel: str = "rocketchat",
        room: Optional[str] = None,     # Se None, usa #equipe-{unit_id}
        severity: str = "medium",
        mentions: Optional[list[str]] = None,
    ) -> MessageResult:
        """
        Envia mensagem para equipe de saude.

        Canais de equipe:
        - #equipe-{unit_id}: Canal da unidade
        - #alertas-clinicos: Canal de alertas
        - #caso-{patient_id}: Discussao de caso especifico
        """

    async def send_batch(
        self,
        messages: list[dict],
    ) -> list[MessageResult]:
        """
        Envio em lote (max 100 mensagens).

        Usado para: lembretes diarios, notificacoes de protocolo.
        POST {comunicacao_url}/api/v1/routing/send-batch
        """

    async def get_patient_preferences(
        self,
        patient_id: str,
    ) -> PatientCommPreferences:
        """
        Busca preferencias de comunicacao do paciente.

        GET {comunicacao_url}/api/v1/preferences/{patient_id}

        Returns:
            PatientCommPreferences:
              - preferred_channel: "whatsapp"
              - quiet_hours: {"start": "22:00", "end": "07:00"}
              - opted_in_channels: ["whatsapp", "sms", "email"]
              - opted_out_channels: ["push"]
              - language: "pt-BR"
        """
```

### 3.4 Receptor de Mensagens (Inbound)

```python
class InboundMessageHandler:
    """Processa mensagens recebidas do paciente via Synapse."""

    def __init__(
        self,
        llm_agent,              # GeraldaAgent (EF-003)
        context_manager,        # ContextManager (EF-007)
        event_pipeline,         # EventPipeline (EF-006)
    ):
        ...

    async def handle_patient_message(
        self,
        patient_id: str,
        message: str,
        channel: str,
        metadata: dict,
    ) -> str:
        """
        Processa mensagem do paciente.

        Fluxo:
        1. Emite evento digital.message_received (EF-006)
        2. Ativa contexto C12 (Conversa Inbound) se necessario
        3. Carrega contexto da jornada do paciente
        4. Envia para GeraldaAgent (LLM) com contexto completo
        5. LLM gera resposta usando tools disponiveis
        6. Retorna resposta ao paciente

        Exemplos de interacao:
        - "O que devo fazer hoje?" → get_daily_schedule tool
        - "Ja tomei meu remedio" → complete_task tool
        - "Nao entendi minha doenca" → search_education tool
        - "Quando e minha proxima consulta?" → get_next_appointment
        - "Estou me sentindo mal" → escalate (notifica equipe)
        """

    async def detect_urgency(
        self,
        message: str,
        patient_context: dict,
    ) -> str:
        """
        Detecta urgencia na mensagem do paciente via LLM.

        Niveis:
        - "normal": Duvida comum, responder normalmente
        - "attention": Pode indicar problema, monitorar
        - "urgent": Requer atencao profissional, escalar
        - "emergency": Possivel emergencia, orientar pronto-socorro

        Palavras-chave de emergencia:
        "dor forte", "sangue", "desmaio", "falta de ar",
        "nao consigo respirar", "inchaço subito", "convulsão"
        """
```

### 3.5 Bot Geralda no Matrix/Element

O bot Geralda no Matrix recebe comandos e mensagens dos pacientes:

```python
class GeraldaBot:
    """Bot Geralda para interacao via Matrix/Element."""

    COMMANDS = {
        "!ajuda": "Lista de comandos disponiveis",
        "!status": "Meu estado de saude atual",
        "!hoje": "O que devo fazer hoje",
        "!lembretes": "Meus lembretes ativos",
        "!plano": "Meu plano de cuidado",
        "!material": "Materiais educativos para mim",
        "!consulta": "Proxima consulta agendada",
        "!adesao": "Como esta minha adesao",
    }

    async def handle_command(
        self,
        command: str,
        patient_id: str,
        room_id: str,
    ) -> str:
        """
        Processa comando do paciente.

        Cada comando mapeia para uma capability da Geralda.
        """

    async def handle_free_text(
        self,
        message: str,
        patient_id: str,
        room_id: str,
    ) -> str:
        """
        Processa mensagem livre do paciente via LLM.

        Delega para InboundMessageHandler.handle_patient_message()
        """
```

### 3.6 Templates de Mensagem

Templates usados pela Geralda ao enviar mensagens via Comunicacao:

| Template ID | Descricao | Canais | Variaveis |
|-------------|-----------|--------|-----------|
| `medication_reminder` | Lembrete de medicamento | WhatsApp, SMS | medication, time, dosage |
| `appointment_reminder` | Lembrete de consulta | WhatsApp, SMS, Push | date, time, doctor, location |
| `education_material` | Material educativo | WhatsApp, Email | title, summary, link |
| `adherence_alert` | Alerta de adesao baixa | Matrix, Push | score, tips |
| `exam_result_ready` | Resultado de exame | WhatsApp, Push | exam_name, summary |
| `care_plan_update` | Plano atualizado | Matrix, Email | changes_summary |
| `welcome_patient` | Boas-vindas | WhatsApp, Matrix | patient_name, unit_name |
| `teleconsult_invite` | Convite teleconsulta | WhatsApp, SMS, Email | date, time, link, doctor |
| `discharge_instructions` | Orientacoes de alta | WhatsApp, Email | instructions, medications |
| `clinical_alert_team` | Alerta para equipe | Rocket.Chat | patient_name, alert_type, severity |

### 3.7 Regras de Envio

```python
class MessageRules:
    """Regras para envio de mensagens respeitando LGPD e preferencias."""

    async def can_send(
        self,
        patient_id: str,
        channel: str,
        severity: str,
        current_time: datetime,
    ) -> tuple[bool, str]:
        """
        Verifica se pode enviar mensagem.

        Regras:
        1. Paciente deu consentimento para o canal?
        2. Canal esta no opt-in do paciente?
        3. Estamos dentro do horario permitido (quiet_hours)?
        4. EXCECAO: severity=CRITICAL sempre envia (Art. 7, VII LGPD)
        5. Limite de mensagens diarias nao excedido?

        Returns:
            (can_send: bool, reason: str)
        """
```

### 3.8 Consumidor de Eventos de Comunicacao

```python
class CommunicationEventConsumer:
    """Consome eventos do modulo Comunicacao via Redis Streams."""

    STREAMS = [
        "intellicare:events:communication",  # Eventos de comunicacao
    ]

    async def handle_message_delivered(self, event: dict) -> None:
        """Mensagem entregue ao paciente — atualizar status."""

    async def handle_message_read(self, event: dict) -> None:
        """Paciente leu mensagem — emitir digital.message_read."""

    async def handle_message_failed(self, event: dict) -> None:
        """Falha na entrega — tentar canal alternativo ou escalar."""

    async def handle_patient_response(self, event: dict) -> None:
        """Paciente respondeu — processar via InboundMessageHandler."""
```

### 3.9 Arquitetura de Arquivos

```
geralda/integrations/
  comunicacao/
    __init__.py
    communication_client.py     # Cliente HTTP para Comunicacao
    inbound_handler.py          # Handler de mensagens inbound
    geralda_bot.py              # Bot Matrix/Element
    message_rules.py            # Regras LGPD de envio
    comm_event_consumer.py      # Consumidor de eventos
    templates.py                # Templates de mensagem
```

### 3.10 Configuracao

```env
# Comunicacao
INTELLICARE_COMUNICACAO_URL=http://comunicacao:8005
INTELLICARE_COMUNICACAO_TIMEOUT=30
INTELLICARE_COMUNICACAO_ENABLED=true

# Bot Matrix (conexao direta para inbound em tempo real)
INTELLICARE_MATRIX_HOMESERVER_URL=https://matrix.gsi.srv.br
INTELLICARE_MATRIX_BOT_USERNAME=@geralda:gsi.srv.br
INTELLICARE_MATRIX_BOT_PASSWORD=<secret>
INTELLICARE_MATRIX_BOT_DEVICE_ID=GERALDA_BOT

# Limites
INTELLICARE_MAX_MESSAGES_PER_DAY=20
INTELLICARE_QUIET_HOURS_START=22:00
INTELLICARE_QUIET_HOURS_END=07:00
```

## 4. Testes

- CommunicationClient: send, send_team, batch, preferences (8 testes)
- InboundMessageHandler: cada tipo de mensagem, urgencia (8 testes)
- GeraldaBot: cada comando, texto livre (8 testes)
- MessageRules: consent, quiet_hours, critical_override, limits (6 testes)
- CommunicationEventConsumer: delivered, read, failed, response (5 testes)
- Templates: renderizacao com variaveis (4 testes)
- Integracao: mensagem inbound → resposta outbound (3 testes)
- **Total**: 42+ testes

## 5. Criterios de Aceitacao

- [ ] CommunicationClient funcional (send, batch, preferences)
- [ ] InboundMessageHandler com processamento via LLM
- [ ] Deteccao de urgencia funcional
- [ ] Bot Geralda com 8 comandos no Matrix/Element
- [ ] 10 templates de mensagem definidos
- [ ] Regras LGPD respeitadas (consent, quiet_hours, opt-in)
- [ ] Override para mensagens CRITICAL
- [ ] Consumo de eventos de comunicacao via Redis
- [ ] Modo degradado quando Comunicacao indisponivel
- [ ] 42+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~8
- **Arquivos modificados**: ~4 (config, event_pipeline, api, docker)
- **Linhas estimadas**: ~1.600
- **Testes novos**: ~42
