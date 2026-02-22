# Domínio 5 — Eventos e Consolidação
## Especificação Funcional Detalhada

**Identificadores**: EF-COM-040, EF-COM-041  
**Prioridade Global**: ALTA  
**Sprint**: S3–S4 (paralelo com D3)  
**Dependências**: D1 (RoutingEngine para disparar comunicações)  
**Dependentes**: D6 (auditoria), D7 (métricas consolidadas)

---

## 1. OBJETIVO

Implementar o consumidor de eventos Redis Streams e a camada de consolidação analítica, responsáveis por:

1. **Consumir eventos** de todos os módulos IntelliCare via Redis Streams (XREADGROUP)
2. **Classificar e transformar** eventos em `CommunicationIntent` (D1)
3. **Rotear automaticamente** comunicações baseadas nos eventos
4. **Consolidar dados** no schema analítico para dashboards e relatórios
5. **Garantir idempotência** e resiliência (at-least-once delivery)

**Estado Atual**: Infraestrutura Redis 7 operacional. Módulos publicam eventos, mas nenhum consumer está ativo no `intellicare-comunicacao`. O schema `comunicacao_analitico` não existe.

---

## 2. CONTEXTO ARQUITETURAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             MÓDULOS INTELLICARE                             │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Oswaldo  │  │ Florence │  │ Geralda  │  │Donabedian│  │  Zilda   │    │
│  │ (alertas)│  │ (exames) │  │ (planos) │  │(qualidade│  │ (dados)  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │              │              │              │              │          │
│       ▼              ▼              ▼              ▼              ▼          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         REDIS STREAMS                                │   │
│  │                                                                     │   │
│  │  stream:alerts    stream:labs    stream:care    stream:quality      │   │
│  │  stream:teleconsult  stream:communication  stream:patients          │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │ XREADGROUP
┌───────────────────────────────────┼─────────────────────────────────────────┐
│                       intellicare-comunicacao                               │
│                                   │                                         │
│  ┌────────────────────────────────┴───────────────────────────────────┐     │
│  │                    MultiEventConsumer                              │     │
│  │                                                                   │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐       │     │
│  │  │AlertHandler  │  │LabHandler    │  │CarePlanHandler   │       │     │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────────┘       │     │
│  │         │                 │                  │                    │     │
│  │         ▼                 ▼                  ▼                    │     │
│  │  ┌────────────────────────────────────────────────────────┐      │     │
│  │  │              EventRouter                                │      │     │
│  │  │  Evento → CommunicationIntent → RoutingEngine (D1)     │      │     │
│  │  └────────────────────────────────────────────────────────┘      │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                   ConsolidationService                            │     │
│  │                                                                   │     │
│  │  comunicacao_operacional → comunicacao_analitico                   │     │
│  │  (delivery_results, intents) → (comm_analytics, daily_metrics)    │     │
│  └───────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. EF-COM-040 — Multi-Event Consumer

### 3.1 Streams e Eventos Consumidos

| Stream | Evento | Descrição | Ação Comunicação |
|---|---|---|---|
| `stream:alerts` | `alert.created` | Novo alerta clínico | Notificar profissional(is) responsável(is) |
| `stream:alerts` | `alert.escalated` | Alerta escalado | Notificar coordenador + equipe ampliada |
| `stream:alerts` | `alert.resolved` | Alerta resolvido | Notificar resolução (baixa prioridade) |
| `stream:labs` | `lab.interpreted` | Resultado interpretado | Notificar médico + canal do paciente |
| `stream:labs` | `lab.critical` | Resultado crítico | Alerta imediato (CRITICAL) |
| `stream:care` | `care_plan.updated` | Plano atualizado | Notificar equipe |
| `stream:care` | `care_plan.task_due` | Tarefa vencendo | Lembrete ao responsável |
| `stream:care` | `care_plan.task_overdue` | Tarefa atrasada | Alerta ao coordenador |
| `stream:quality` | `quality.threshold_breach` | Indicador abaixo do limiar | Notificar coordenador + gestores |
| `stream:patients` | `patient.reclassified` | Paciente mudou de risco | Notificar equipe de cuidado |
| `stream:patients` | `patient.admitted` | Paciente internado | Notificar equipe |
| `stream:patients` | `patient.discharged` | Paciente com alta | Agendar follow-up |
| `stream:teleconsult` | `teleconsult.scheduled` | Teleconsulta agendada | (interno — já tratado por D3) |
| `stream:teleconsult` | `teleconsult.no_show` | No-show detectado | Notificar coordenador |
| `stream:communication` | `message.failed` | Entrega falhou | Retry ou canal alternativo |
| `stream:communication` | `message.escalated` | Mensagem não lida | Escalar para canal seguinte |

### 3.2 MultiEventConsumer

```python
import asyncio
import redis.asyncio as redis
from typing import Dict, List, Callable, Optional
from datetime import datetime
import json

class MultiEventConsumer:
    """
    Consumidor multi-stream com XREADGROUP.
    
    Implementa consumer group para garantir:
    - At-least-once delivery (XACK após processamento)
    - Distribuição de carga (N consumers no mesmo grupo)
    - Retry automático (pending entries list)
    - Idempotência (deduplicação por event_id)
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        config: ConsumerConfig,
        handlers: Dict[str, EventHandler],
        event_router: EventRouter,
        dedup_store: DeduplicationStore,
    ):
        self._redis = redis_client
        self._config = config
        self._handlers = handlers
        self._router = event_router
        self._dedup = dedup_store
        self._running = False
        self._stats = ConsumerStats()
    
    async def start(self) -> None:
        """
        Inicia o consumer loop.
        
        Fluxo principal:
        1. Criar consumer groups em cada stream (XGROUP CREATE)
        2. Primeiro: processar mensagens pendentes (PEL — Pending Entries List)
        3. Depois: ler novas mensagens (XREADGROUP … > )
        4. Para cada mensagem:
           a. Verificar deduplicação (event_id já processado?)
           b. Deserializar evento
           c. Rotear para handler correto
           d. Handler converte em CommunicationIntent
           e. EventRouter envia para RoutingEngine (D1)
           f. XACK (confirma processamento)
        5. Periodicamente: reclamar mensagens pegadas por consumers mortos
        """
        self._running = True
        
        # 1. Garantir que consumer groups existem
        await self._ensure_consumer_groups()
        
        # 2. Processar pending entries primeiro
        await self._process_pending()
        
        # 3. Loop principal
        while self._running:
            try:
                # XREADGROUP em múltiplos streams
                entries = await self._redis.xreadgroup(
                    groupname=self._config.group_name,
                    consumername=self._config.consumer_name,
                    streams={
                        stream: ">" for stream in self._config.streams
                    },
                    count=self._config.batch_size,
                    block=self._config.block_ms,
                )
                
                if entries:
                    for stream_name, messages in entries:
                        for msg_id, data in messages:
                            await self._process_message(stream_name, msg_id, data)
                
                # Periodicamente reclamar mensagens órfãs
                if self._should_reclaim():
                    await self._reclaim_pending()
                    
            except Exception as e:
                logger.error(f"Consumer error: {e}", exc_info=True)
                self._stats.errors += 1
                await asyncio.sleep(self._config.error_backoff_ms / 1000)
    
    async def stop(self) -> None:
        """Para o consumer graciosamente."""
        self._running = False
    
    async def _process_message(self, stream: str, msg_id: str, data: Dict) -> None:
        """
        Processa uma mensagem individual.
        
        Fluxo:
        1. Deserializar: event = Event.from_redis(data)
        2. Dedup: se event.id já processado → XACK e skip
        3. Buscar handler: handler = self._handlers[event.type]
        4. Processar: intent = await handler.handle(event)
        5. Se intent != None: await self._router.route(intent)
        6. XACK
        7. Registrar dedup
        8. Atualizar stats
        """
        try:
            event = Event.from_redis(data)
            
            # Deduplicação
            if await self._dedup.is_processed(event.id):
                await self._redis.xack(stream, self._config.group_name, msg_id)
                self._stats.duplicates += 1
                return
            
            # Buscar handler
            handler = self._handlers.get(event.type)
            if not handler:
                logger.warning(f"No handler for event type: {event.type}")
                await self._redis.xack(stream, self._config.group_name, msg_id)
                self._stats.unhandled += 1
                return
            
            # Processar
            intent = await handler.handle(event)
            
            if intent:
                await self._router.route(intent)
                self._stats.routed += 1
            
            # ACK e dedup
            await self._redis.xack(stream, self._config.group_name, msg_id)
            await self._dedup.mark_processed(event.id)
            self._stats.processed += 1
            
        except Exception as e:
            logger.error(f"Error processing {msg_id} from {stream}: {e}", exc_info=True)
            self._stats.errors += 1
            # NÃO faz XACK → mensagem permanece pendente para retry
    
    async def _ensure_consumer_groups(self):
        """Cria consumer groups em cada stream, ignorando se já existem."""
        for stream in self._config.streams:
            try:
                await self._redis.xgroup_create(
                    name=stream,
                    groupname=self._config.group_name,
                    id="0",          # Ler desde o início
                    mkstream=True    # Criar stream se não existir
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    pass  # Grupo já existe
                else:
                    raise
    
    async def _process_pending(self):
        """Processa mensagens pendentes (não ACK'd) de sessões anteriores."""
        for stream in self._config.streams:
            pending = await self._redis.xpending_range(
                name=stream,
                groupname=self._config.group_name,
                min="-",
                max="+",
                count=100,
                consumername=self._config.consumer_name,
            )
            for entry in pending:
                msg_id = entry["message_id"]
                messages = await self._redis.xrange(stream, min=msg_id, max=msg_id)
                for mid, data in messages:
                    await self._process_message(stream, mid, data)
    
    async def _reclaim_pending(self):
        """Reclama mensagens de consumers mortos (idle > threshold)."""
        for stream in self._config.streams:
            claimed = await self._redis.xautoclaim(
                name=stream,
                groupname=self._config.group_name,
                consumername=self._config.consumer_name,
                min_idle_time=self._config.reclaim_idle_ms,
                start_id="0",
                count=50,
            )
            if claimed and claimed[1]:
                for msg_id, data in claimed[1]:
                    await self._process_message(stream, msg_id, data)
    
    def get_stats(self) -> ConsumerStats:
        """Retorna estatísticas do consumer."""
        return self._stats


class ConsumerConfig(BaseModel):
    """Configuração do consumer."""
    
    group_name: str = "comunicacao-group"
    consumer_name: str = "comunicacao-consumer-1"   # Único por instância
    
    streams: List[str] = [
        "stream:alerts",
        "stream:labs",
        "stream:care",
        "stream:quality",
        "stream:patients",
        "stream:teleconsult",
        "stream:communication",
    ]
    
    batch_size: int = 10               # Mensagens por leitura
    block_ms: int = 5000               # Bloquear por 5s se sem mensagens
    error_backoff_ms: int = 3000       # Espera após erro
    reclaim_idle_ms: int = 60000       # Reclamar msgs idle > 60s
    reclaim_interval_ms: int = 30000   # Verificar reclaim a cada 30s
    
    # Deduplicação
    dedup_ttl_seconds: int = 86400     # Guardar IDs processados por 24h


class ConsumerStats(BaseModel):
    """Estatísticas do consumer."""
    started_at: datetime = Field(default_factory=datetime.utcnow)
    processed: int = 0
    routed: int = 0
    duplicates: int = 0
    unhandled: int = 0
    errors: int = 0
    last_processed_at: Optional[datetime] = None
```

### 3.3 Event Model

```python
class Event(BaseModel):
    """Evento recebido de um Redis Stream."""
    
    id: str                           # ID único do evento
    type: str                         # "alert.created", "lab.interpreted", etc.
    source: str                       # Módulo de origem: "oswaldo", "florence", etc.
    timestamp: datetime               # Quando o evento ocorreu
    data: Dict                        # Payload específico do evento
    
    # Metadata
    correlation_id: Optional[str]     # Para rastreamento cross-module
    patient_id: Optional[str]         # Se evento é sobre um paciente
    user_id: Optional[str]            # Se evento é gerado por um usuário
    
    @classmethod
    def from_redis(cls, data: Dict[bytes, bytes]) -> "Event":
        """Deserializa de formato Redis Stream (bytes → dict)."""
        decoded = {k.decode(): v.decode() for k, v in data.items()}
        
        # O campo "data" é JSON serializado
        if "data" in decoded and isinstance(decoded["data"], str):
            decoded["data"] = json.loads(decoded["data"])
        
        return cls(
            id=decoded.get("id", str(uuid4())),
            type=decoded["type"],
            source=decoded.get("source", "unknown"),
            timestamp=datetime.fromisoformat(decoded.get("timestamp", datetime.utcnow().isoformat())),
            data=decoded.get("data", {}),
            correlation_id=decoded.get("correlation_id"),
            patient_id=decoded.get("patient_id"),
            user_id=decoded.get("user_id"),
        )
```

### 3.4 Event Handlers

```python
class EventHandler(ABC):
    """Interface base para handlers de eventos."""
    
    @property
    @abstractmethod
    def handled_event_types(self) -> List[str]:
        """Lista de tipos de evento que este handler processa."""
    
    @abstractmethod
    async def handle(self, event: Event) -> Optional[CommunicationIntent]:
        """
        Processa evento e retorna CommunicationIntent para roteamento.
        Retorna None se evento não requer comunicação.
        """


class AlertCreatedHandler(EventHandler):
    """Handler para alert.created."""
    
    @property
    def handled_event_types(self) -> List[str]:
        return ["alert.created"]
    
    async def handle(self, event: Event) -> Optional[CommunicationIntent]:
        """
        Converte alerta clínico em CommunicationIntent.
        
        Dados esperados:
        event.data = {
            "alert_id": "ALR-001",
            "patient_id": "P001",
            "patient_name": "Maria Santos",
            "severity": "CRITICAL",        # CRITICAL | HIGH | MEDIUM | LOW
            "type": "egfr_decline",
            "description": "eGFR < 30 ml/min (28.5)",
            "value": 28.5,
            "threshold": 30.0,
            "unit": "ml/min",
            "professional_id": "PROF-001",  # Médico responsável
            "team_id": "EQUIPE-UBS-CENTRO"
        }
        
        Lógica:
        1. Mapear severity → CommunicationSeverity
        2. Se CRITICAL/HIGH → recipients: doctor + coordinator + team channel
        3. Se MEDIUM → recipients: doctor + team channel
        4. Se LOW → recipients: team channel apenas
        5. Montar CommunicationIntent com template "clinical_alert_generic"
        """
        severity = SeverityLevel(event.data["severity"])
        
        channels = self._channels_for_severity(severity)
        
        return CommunicationIntent(
            intent_type=IntentType.CLINICAL_ALERT,
            recipient_type=RecipientType.PROFESSIONAL,
            recipient_id=event.data.get("professional_id"),
            severity=severity,
            channels=channels,
            template_name="clinical_alert_generic",
            payload={
                "alert_id": event.data["alert_id"],
                "patient_id": event.data["patient_id"],
                "patient_name": event.data["patient_name"],
                "description": event.data["description"],
                "value": str(event.data.get("value", "")),
                "threshold": str(event.data.get("threshold", "")),
                "unit": event.data.get("unit", ""),
                "severity": event.data["severity"],
            },
            source_module=event.source,
            source_event_id=event.id,
            patient_id=event.data.get("patient_id"),
        )
    
    def _channels_for_severity(self, severity: SeverityLevel) -> List[ChannelType]:
        mapping = {
            SeverityLevel.CRITICAL: [ChannelType.PUSH, ChannelType.ROCKETCHAT, ChannelType.WHATSAPP, ChannelType.SMS],
            SeverityLevel.HIGH: [ChannelType.PUSH, ChannelType.ROCKETCHAT, ChannelType.WHATSAPP],
            SeverityLevel.MEDIUM: [ChannelType.ROCKETCHAT, ChannelType.EMAIL],
            SeverityLevel.LOW: [ChannelType.ROCKETCHAT],
        }
        return mapping.get(severity, [ChannelType.ROCKETCHAT])


class LabInterpretedHandler(EventHandler):
    """Handler para lab.interpreted e lab.critical."""
    
    @property
    def handled_event_types(self) -> List[str]:
        return ["lab.interpreted", "lab.critical"]
    
    async def handle(self, event: Event) -> Optional[CommunicationIntent]:
        """
        Converte resultado de exame em CommunicationIntent.
        
        Dados esperados:
        event.data = {
            "lab_result_id": "LAB-001",
            "patient_id": "P001",
            "patient_name": "Maria Santos",
            "exams": [
                {"name": "eGFR", "value": 28.5, "reference": "> 60", "status": "critical"},
                {"name": "Creatinina", "value": 2.1, "reference": "0.7-1.2", "status": "high"},
            ],
            "interpretation": "Padrão nefrotóxico detectado...",
            "professional_id": "PROF-001"
        }
        """
        is_critical = event.type == "lab.critical"
        
        return CommunicationIntent(
            intent_type=IntentType.LAB_RESULT,
            recipient_type=RecipientType.PROFESSIONAL,
            recipient_id=event.data["professional_id"],
            severity=SeverityLevel.CRITICAL if is_critical else SeverityLevel.HIGH,
            channels=[ChannelType.ROCKETCHAT, ChannelType.PUSH] if is_critical else [ChannelType.ROCKETCHAT],
            template_name="lab_result_notification",
            payload=event.data,
            source_module="florence",
            source_event_id=event.id,
            patient_id=event.data.get("patient_id"),
        )


class CarePlanHandler(EventHandler):
    """Handler para eventos de plano de cuidado."""
    
    @property
    def handled_event_types(self) -> List[str]:
        return ["care_plan.updated", "care_plan.task_due", "care_plan.task_overdue"]
    
    async def handle(self, event: Event) -> Optional[CommunicationIntent]:
        """
        Converte eventos de plano de cuidado em CommunicationIntent.
        
        care_plan.updated → notificar equipe (MEDIUM)
        care_plan.task_due → lembrete ao responsável (HIGH)
        care_plan.task_overdue → alerta ao coordenador (HIGH)
        """
        if event.type == "care_plan.task_overdue":
            return CommunicationIntent(
                intent_type=IntentType.ESCALATION,
                recipient_type=RecipientType.CARE_COORDINATOR,
                recipient_id=event.data.get("coordinator_id"),
                severity=SeverityLevel.HIGH,
                channels=[ChannelType.ROCKETCHAT, ChannelType.PUSH],
                template_name="task_overdue_alert",
                payload=event.data,
                source_module="geralda",
                source_event_id=event.id,
                patient_id=event.data.get("patient_id"),
            )
        elif event.type == "care_plan.task_due":
            return CommunicationIntent(
                intent_type=IntentType.TASK_REMINDER,
                recipient_type=RecipientType.PROFESSIONAL,
                recipient_id=event.data.get("assigned_to"),
                severity=SeverityLevel.MEDIUM,
                channels=[ChannelType.ROCKETCHAT],
                template_name="task_due_reminder",
                payload=event.data,
                source_module="geralda",
                source_event_id=event.id,
                patient_id=event.data.get("patient_id"),
            )
        else:  # care_plan.updated
            return CommunicationIntent(
                intent_type=IntentType.CARE_PLAN_UPDATE,
                recipient_type=RecipientType.TEAM,
                recipient_id=event.data.get("team_id"),
                severity=SeverityLevel.LOW,
                channels=[ChannelType.ROCKETCHAT],
                template_name="care_plan_update",
                payload=event.data,
                source_module="geralda",
                source_event_id=event.id,
                patient_id=event.data.get("patient_id"),
            )


class QualityThresholdHandler(EventHandler):
    """Handler para quality.threshold_breach."""
    
    @property
    def handled_event_types(self) -> List[str]:
        return ["quality.threshold_breach"]
    
    async def handle(self, event: Event) -> Optional[CommunicationIntent]:
        return CommunicationIntent(
            intent_type=IntentType.QUALITY_ALERT,
            recipient_type=RecipientType.CARE_COORDINATOR,
            recipient_id=event.data.get("coordinator_id"),
            severity=SeverityLevel.HIGH,
            channels=[ChannelType.ROCKETCHAT, ChannelType.EMAIL],
            template_name="quality_threshold_alert",
            payload=event.data,
            source_module="donabedian",
            source_event_id=event.id,
        )


class PatientReclassifiedHandler(EventHandler):
    """Handler para patient.reclassified."""
    
    @property
    def handled_event_types(self) -> List[str]:
        return ["patient.reclassified", "patient.admitted", "patient.discharged"]
    
    async def handle(self, event: Event) -> Optional[CommunicationIntent]:
        if event.type == "patient.reclassified":
            return CommunicationIntent(
                intent_type=IntentType.PATIENT_STATUS_CHANGE,
                recipient_type=RecipientType.TEAM,
                recipient_id=event.data.get("team_id"),
                severity=SeverityLevel.MEDIUM,
                channels=[ChannelType.ROCKETCHAT],
                template_name="patient_reclassification",
                payload=event.data,
                source_module="zilda",
                source_event_id=event.id,
                patient_id=event.data.get("patient_id"),
            )
        elif event.type == "patient.discharged":
            # Agendar follow-up
            return CommunicationIntent(
                intent_type=IntentType.FOLLOW_UP_SCHEDULE,
                recipient_type=RecipientType.PROFESSIONAL,
                recipient_id=event.data.get("professional_id"),
                severity=SeverityLevel.MEDIUM,
                channels=[ChannelType.ROCKETCHAT],
                template_name="patient_discharged_followup",
                payload=event.data,
                source_module="zilda",
                source_event_id=event.id,
                patient_id=event.data.get("patient_id"),
            )
        return None  # patient.admitted → tratado por outro handler


class MessageFailedHandler(EventHandler):
    """Handler para message.failed — retry ou fallback."""
    
    @property
    def handled_event_types(self) -> List[str]:
        return ["message.failed", "message.escalated"]
    
    async def handle(self, event: Event) -> Optional[CommunicationIntent]:
        """
        Quando uma mensagem falha ou não é lida:
        
        1. message.failed:
           - Se dentro do retry count → reenviar pelo mesmo canal
           - Se esgotou retries → tentar próximo canal (cascading)
        
        2. message.escalated:
           - Mensagem não lida dentro do TTL
           - Escalar para próximo canal da cadeia
        """
        # O RoutingEngine já implementa cascading (D1)
        # Este handler registra o evento e pode disparar notificação ao admin
        return None  # Cascading é tratado internamente pelo RoutingEngine
```

### 3.5 EventRouter

```python
class EventRouter:
    """
    Conecta handlers de evento ao RoutingEngine (D1).
    Responsável por transformar CommunicationIntent em chamada ao RoutingEngine.
    """
    
    def __init__(self, routing_engine: RoutingEngine):
        self._engine = routing_engine
    
    async def route(self, intent: CommunicationIntent) -> Optional[str]:
        """
        Envia intent para o RoutingEngine.
        
        Retorna: intent_id se roteado com sucesso, None se falhou.
        """
        try:
            result = await self._engine.route(intent)
            logger.info(
                f"Event routed: {intent.intent_type} → "
                f"channels={[c.value for c in intent.channels]}, "
                f"severity={intent.severity}"
            )
            return result.intent_id
        except Exception as e:
            logger.error(f"Failed to route event: {e}", exc_info=True)
            return None
```

### 3.6 DeduplicationStore

```python
class DeduplicationStore:
    """Armazena IDs de eventos processados para deduplicação."""
    
    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 86400):
        self._redis = redis_client
        self._ttl = ttl_seconds
        self._prefix = "dedup:event:"
    
    async def is_processed(self, event_id: str) -> bool:
        """Verifica se evento já foi processado."""
        return await self._redis.exists(f"{self._prefix}{event_id}")
    
    async def mark_processed(self, event_id: str) -> None:
        """Marca evento como processado (com TTL)."""
        await self._redis.setex(
            f"{self._prefix}{event_id}",
            self._ttl,
            "1"
        )
```

---

## 4. EF-COM-041 — Consolidação Analítica

### 4.1 Descrição Funcional

O serviço de consolidação transfere dados do schema operacional para o analítico, criando visualizações agregadas para dashboards e relatórios. Opera em dois modos:

1. **Real-time**: Incrementa contadores a cada delivery processado
2. **Batch**: Job periódico (a cada 1 hora) que consolida métricas completas

### 4.2 Schema Analítico

```sql
-- Migration: 2026_02_15_0005_create_analytics_schema.py
-- Schema: comunicacao_analitico

CREATE SCHEMA IF NOT EXISTS comunicacao_analitico;

-- Tabela principal de analytics de comunicação
CREATE TABLE comunicacao_analitico.comm_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Dimensões temporais
    event_date DATE NOT NULL,
    event_hour INT NOT NULL,              -- 0-23
    
    -- Dimensões de comunicação
    intent_type VARCHAR(50) NOT NULL,     -- "clinical_alert", "lab_result", etc.
    channel VARCHAR(20) NOT NULL,         -- "rocketchat", "push", "whatsapp", etc.
    severity VARCHAR(20) NOT NULL,        -- "CRITICAL", "HIGH", "MEDIUM", "LOW"
    
    -- Dimensões organizacionais
    source_module VARCHAR(50),            -- "oswaldo", "florence", etc.
    team_id VARCHAR(200),
    
    -- Métricas
    total_sent INT NOT NULL DEFAULT 0,
    total_delivered INT NOT NULL DEFAULT 0,
    total_read INT NOT NULL DEFAULT 0,
    total_failed INT NOT NULL DEFAULT 0,
    
    -- Tempos (em segundos)
    avg_delivery_time_seconds FLOAT,
    avg_read_time_seconds FLOAT,
    min_delivery_time_seconds FLOAT,
    max_delivery_time_seconds FLOAT,
    
    -- Percentuais
    delivery_rate FLOAT,                  -- delivered / sent
    read_rate FLOAT,                      -- read / delivered
    failure_rate FLOAT,                   -- failed / sent
    
    -- Metadata
    consolidated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(event_date, event_hour, intent_type, channel, severity, source_module, team_id)
);

CREATE INDEX idx_comm_analytics_date ON comunicacao_analitico.comm_analytics(event_date);
CREATE INDEX idx_comm_analytics_channel ON comunicacao_analitico.comm_analytics(channel);
CREATE INDEX idx_comm_analytics_severity ON comunicacao_analitico.comm_analytics(severity);
CREATE INDEX idx_comm_analytics_module ON comunicacao_analitico.comm_analytics(source_module);

-- Métricas diárias agregadas
CREATE TABLE comunicacao_analitico.daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    metric_date DATE NOT NULL,
    
    -- Volume
    total_intents INT NOT NULL DEFAULT 0,
    total_deliveries INT NOT NULL DEFAULT 0,
    total_unique_patients INT NOT NULL DEFAULT 0,
    total_unique_professionals INT NOT NULL DEFAULT 0,
    
    -- Por canal
    rocketchat_sent INT DEFAULT 0,
    rocketchat_delivered INT DEFAULT 0,
    push_sent INT DEFAULT 0,
    push_delivered INT DEFAULT 0,
    whatsapp_sent INT DEFAULT 0,
    whatsapp_delivered INT DEFAULT 0,
    whatsapp_read INT DEFAULT 0,
    sms_sent INT DEFAULT 0,
    sms_delivered INT DEFAULT 0,
    email_sent INT DEFAULT 0,
    email_delivered INT DEFAULT 0,
    
    -- Por severidade
    critical_count INT DEFAULT 0,
    high_count INT DEFAULT 0,
    medium_count INT DEFAULT 0,
    low_count INT DEFAULT 0,
    
    -- Performance
    avg_delivery_seconds FLOAT,
    avg_read_seconds FLOAT,
    overall_delivery_rate FLOAT,
    overall_read_rate FLOAT,
    overall_failure_rate FLOAT,
    
    -- Teleconsulta
    teleconsults_scheduled INT DEFAULT 0,
    teleconsults_completed INT DEFAULT 0,
    teleconsults_no_show INT DEFAULT 0,
    teleconsults_avg_duration_min FLOAT,
    
    -- Eventos processados
    events_processed INT DEFAULT 0,
    events_errors INT DEFAULT 0,
    
    consolidated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(metric_date)
);

CREATE INDEX idx_daily_metrics_date ON comunicacao_analitico.daily_metrics(metric_date);

-- Top alertas (mais frequentes)
CREATE TABLE comunicacao_analitico.top_alert_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL,
    alert_type VARCHAR(200) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    count INT NOT NULL DEFAULT 0,
    avg_response_time_seconds FLOAT,
    
    UNIQUE(metric_date, alert_type, severity)
);

-- SLA de comunicação por equipe
CREATE TABLE comunicacao_analitico.team_communication_sla (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL,
    team_id VARCHAR(200) NOT NULL,
    team_name VARCHAR(300),
    
    -- SLA: % de alertas CRITICAL respondidos em < 15 min
    critical_within_sla INT DEFAULT 0,
    critical_outside_sla INT DEFAULT 0,
    critical_sla_rate FLOAT,
    
    -- SLA: % de alertas HIGH respondidos em < 60 min
    high_within_sla INT DEFAULT 0,
    high_outside_sla INT DEFAULT 0,
    high_sla_rate FLOAT,
    
    -- Geral
    total_communications INT DEFAULT 0,
    avg_response_seconds FLOAT,
    
    UNIQUE(metric_date, team_id)
);

CREATE INDEX idx_team_sla_date ON comunicacao_analitico.team_communication_sla(metric_date);
CREATE INDEX idx_team_sla_team ON comunicacao_analitico.team_communication_sla(team_id);
```

### 4.3 ConsolidationService

```python
class ConsolidationService:
    """
    Consolida dados operacionais → analíticos.
    
    Dois modos:
    1. Real-time: chamado após cada delivery
    2. Batch: job periódico que recalcula
    """
    
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self._db = db
        self._redis = redis_client
    
    async def on_delivery_completed(self, delivery: DeliveryResult) -> None:
        """
        Modo real-time: incrementa contadores após cada delivery.
        
        Usa UPSERT no PostgreSQL (INSERT ... ON CONFLICT DO UPDATE).
        """
        date = delivery.created_at.date()
        hour = delivery.created_at.hour
        
        await self._db.execute(text("""
            INSERT INTO comunicacao_analitico.comm_analytics 
                (event_date, event_hour, intent_type, channel, severity, source_module, team_id,
                 total_sent, total_delivered, total_read, total_failed)
            VALUES (:date, :hour, :intent, :channel, :severity, :source, :team,
                    :sent, :delivered, :read, :failed)
            ON CONFLICT (event_date, event_hour, intent_type, channel, severity, source_module, team_id)
            DO UPDATE SET
                total_sent = comm_analytics.total_sent + :sent,
                total_delivered = comm_analytics.total_delivered + :delivered,
                total_read = comm_analytics.total_read + :read,
                total_failed = comm_analytics.total_failed + :failed,
                consolidated_at = NOW()
        """), {
            "date": date,
            "hour": hour,
            "intent": delivery.intent_type,
            "channel": delivery.channel,
            "severity": delivery.severity,
            "source": delivery.source_module,
            "team": delivery.team_id,
            "sent": 1 if delivery.status in ["sent", "delivered", "read"] else 0,
            "delivered": 1 if delivery.status in ["delivered", "read"] else 0,
            "read": 1 if delivery.status == "read" else 0,
            "failed": 1 if delivery.status == "failed" else 0,
        })
    
    async def consolidate_daily(self, date: Optional[datetime] = None) -> Dict:
        """
        Modo batch: consolida métricas diárias completas.
        
        Roda a cada 1 hora (ou sob demanda).
        
        Fluxo:
        1. Buscar todos os delivery_results do dia
        2. Agrupar por canal, severidade, equipe
        3. Calcular métricas: taxas, médias, SLA
        4. UPSERT em daily_metrics
        5. UPSERT em top_alert_types
        6. UPSERT em team_communication_sla
        7. Retornar resumo
        """
        target_date = date or datetime.utcnow().date()
        
        # 1. Buscar dados operacionais
        results = await self._db.execute(text("""
            SELECT 
                dr.channel,
                dr.status,
                dr.severity,
                dr.intent_type,
                dr.source_module,
                dr.team_id,
                dr.created_at,
                dr.delivered_at,
                dr.read_at,
                ci.patient_id
            FROM comunicacao_operacional.delivery_results dr
            JOIN comunicacao_operacional.communication_intents ci ON dr.intent_id = ci.id
            WHERE DATE(dr.created_at AT TIME ZONE 'America/Sao_Paulo') = :date
        """), {"date": target_date})
        
        rows = results.fetchall()
        
        # 2. Calcular métricas
        metrics = self._calculate_metrics(rows, target_date)
        
        # 3. UPSERT daily_metrics
        await self._upsert_daily_metrics(metrics)
        
        # 4. UPSERT top_alert_types
        await self._upsert_top_alerts(rows, target_date)
        
        # 5. UPSERT team_communication_sla
        await self._upsert_team_sla(rows, target_date)
        
        return {
            "date": str(target_date),
            "total_deliveries": len(rows),
            "metrics_consolidated": True
        }
    
    def _calculate_metrics(self, rows, date) -> Dict:
        """Calcula todas as métricas diárias a partir dos rows."""
        metrics = {
            "metric_date": date,
            "total_intents": len(set(r.intent_id for r in rows)),
            "total_deliveries": len(rows),
            "total_unique_patients": len(set(r.patient_id for r in rows if r.patient_id)),
            "total_unique_professionals": len(set(r.user_id for r in rows if r.user_id)),
        }
        
        # Por canal
        for channel in ["rocketchat", "push", "whatsapp", "sms", "email"]:
            channel_rows = [r for r in rows if r.channel == channel]
            metrics[f"{channel}_sent"] = len(channel_rows)
            metrics[f"{channel}_delivered"] = len([r for r in channel_rows if r.status in ["delivered", "read"]])
            if channel == "whatsapp":
                metrics["whatsapp_read"] = len([r for r in channel_rows if r.status == "read"])
        
        # Por severidade
        for sev in ["critical", "high", "medium", "low"]:
            metrics[f"{sev}_count"] = len([r for r in rows if r.severity.lower() == sev])
        
        # Taxas
        total = len(rows) or 1
        delivered = len([r for r in rows if r.status in ["delivered", "read"]])
        read = len([r for r in rows if r.status == "read"])
        failed = len([r for r in rows if r.status == "failed"])
        
        metrics["overall_delivery_rate"] = delivered / total
        metrics["overall_read_rate"] = read / (delivered or 1)
        metrics["overall_failure_rate"] = failed / total
        
        return metrics
```

### 4.4 API Endpoints

```yaml
# ── Consumer ──
GET /api/v1/events/consumer/status
  Description: Status do consumer de eventos
  Auth: Keycloak (admin)
  Response 200: {
    running: bool,
    stats: ConsumerStats,
    streams: List[{ name, pending_count, last_processed }]
  }

POST /api/v1/events/consumer/restart
  Description: Reinicia o consumer
  Auth: Keycloak (admin)
  Response 200: { restarted: true }

# ── Consolidação ──
POST /api/v1/analytics/consolidate
  Description: Força consolidação diária
  Auth: Keycloak (admin)
  Body: { date: Optional[str] }  # Default: hoje
  Response 200: { date: str, total_deliveries: int, metrics_consolidated: true }

GET /api/v1/analytics/daily/{date}
  Description: Métricas diárias consolidadas
  Auth: Keycloak (admin, care_coordinator)
  Response 200: DailyMetrics

GET /api/v1/analytics/hourly
  Description: Métricas horárias (comm_analytics)
  Auth: Keycloak (admin)
  Query: date, channel, severity, source_module
  Response 200: List[CommAnalytics]

GET /api/v1/analytics/team-sla
  Description: SLA por equipe
  Auth: Keycloak (admin, care_coordinator)
  Query: date, team_id
  Response 200: List[TeamCommunicationSLA]

GET /api/v1/analytics/top-alerts
  Description: Top alertas por tipo
  Auth: Keycloak (admin)
  Query: date, limit (default: 10)
  Response 200: List[TopAlertType]

GET /api/v1/analytics/range
  Description: Métricas de um período
  Auth: Keycloak (admin, care_coordinator)
  Query: start_date, end_date, group_by (day|week|month)
  Response 200: List[DailyMetrics]
```

---

## 5. TESTES ESPERADOS

```
test_events/
├── test_consumer.py
│   ├── test_consumer_starts_and_reads_messages
│   ├── test_consumer_creates_consumer_groups
│   ├── test_consumer_processes_pending_on_start
│   ├── test_consumer_acks_after_processing
│   ├── test_consumer_deduplicates_events
│   ├── test_consumer_handles_error_gracefully
│   ├── test_consumer_reclaims_orphaned_messages
│   ├── test_consumer_stops_gracefully
│   └── test_consumer_stats_accurate
├── test_handlers/
│   ├── test_alert_handler.py
│   │   ├── test_critical_alert_maps_to_all_channels
│   │   ├── test_high_alert_maps_to_push_rc_wa
│   │   ├── test_medium_alert_maps_to_rc_email
│   │   ├── test_low_alert_maps_to_rc_only
│   │   └── test_alert_intent_has_correct_template
│   ├── test_lab_handler.py
│   │   ├── test_lab_critical_has_critical_severity
│   │   ├── test_lab_interpreted_has_high_severity
│   │   └── test_lab_intent_contains_exams
│   ├── test_care_plan_handler.py
│   │   ├── test_task_overdue_escalates
│   │   ├── test_task_due_reminds
│   │   └── test_plan_updated_low_priority
│   ├── test_quality_handler.py
│   │   └── test_threshold_breach_notifies_coordinator
│   ├── test_patient_handler.py
│   │   ├── test_reclassified_notifies_team
│   │   └── test_discharged_schedules_followup
│   └── test_message_failed_handler.py
│       └── test_failed_message_logged
├── test_event_router.py
│   ├── test_route_to_routing_engine
│   ├── test_route_returns_intent_id
│   └── test_route_handles_engine_error
└── test_dedup.py
    ├── test_mark_and_check_processed
    ├── test_ttl_expires
    └── test_unprocessed_returns_false

test_consolidation/
├── test_realtime.py
│   ├── test_on_delivery_increments_sent
│   ├── test_on_delivery_increments_delivered
│   ├── test_on_delivery_increments_failed
│   └── test_upsert_is_idempotent
├── test_batch.py
│   ├── test_consolidate_daily_creates_metrics
│   ├── test_consolidate_calculates_rates
│   ├── test_consolidate_counts_unique_patients
│   ├── test_consolidate_updates_top_alerts
│   └── test_consolidate_updates_team_sla
└── test_api.py
    ├── test_consumer_status_endpoint
    ├── test_consolidate_endpoint
    ├── test_daily_metrics_endpoint
    └── test_team_sla_endpoint
```

---

## 6. ESTRUTURA DE CÓDIGO

```
comunicacao/
├── events/
│   ├── __init__.py
│   ├── consumer.py                    # MultiEventConsumer
│   ├── config.py                      # ConsumerConfig
│   ├── models.py                      # Event, ConsumerStats
│   ├── router.py                      # EventRouter
│   ├── dedup.py                       # DeduplicationStore
│   └── handlers/
│       ├── __init__.py
│       ├── base.py                    # EventHandler ABC
│       ├── alert_handler.py           # AlertCreatedHandler
│       ├── lab_handler.py             # LabInterpretedHandler
│       ├── care_plan_handler.py       # CarePlanHandler
│       ├── quality_handler.py         # QualityThresholdHandler
│       ├── patient_handler.py         # PatientReclassifiedHandler
│       └── message_handler.py         # MessageFailedHandler
├── consolidation/
│   ├── __init__.py
│   ├── service.py                     # ConsolidationService
│   ├── daily_job.py                   # Job scheduler (APScheduler)
│   └── models.py                      # DailyMetrics, CommAnalytics, TeamSLA
├── api/
│   ├── events_routes.py
│   └── analytics_routes.py
└── tests/
    ├── test_events/
    └── test_consolidation/
```

---

## 7. CONFIGURAÇÃO

```bash
# Redis
REDIS_URL=redis://redis:6379/0
REDIS_STREAMS_DB=0

# Consumer
EVENT_CONSUMER_GROUP=comunicacao-group
EVENT_CONSUMER_NAME=comunicacao-consumer-1
EVENT_CONSUMER_BATCH_SIZE=10
EVENT_CONSUMER_BLOCK_MS=5000
EVENT_DEDUP_TTL_SECONDS=86400

# Consolidation
CONSOLIDATION_INTERVAL_MINUTES=60
CONSOLIDATION_TIMEZONE=America/Sao_Paulo
```

---

## 8. ENTREGÁVEIS DO DEV

1. **Especificação Técnica**: Diagramas de fluxo dos consumers
2. **Plano de Implementação**: Consumer → Handlers → Router → Consolidation
3. **Código**: Consumer + 6 handlers + consolidation com testes ≥ 85%
4. **Migrations**: Schema analítico completo
5. **Scripts de teste**: Publicar eventos fake nos streams para teste
6. **Monitoring**: Exportar métricas do consumer para Prometheus (D7)
7. **Documentação**: README + formato de eventos esperados

**Prazo estimado**: 1.5 sprints (S3 parcial + S4 parcial)
