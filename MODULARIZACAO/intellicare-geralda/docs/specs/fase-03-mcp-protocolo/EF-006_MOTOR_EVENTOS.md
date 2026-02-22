# EF-006 — Motor de Eventos da Jornada do Paciente

> Sistema de eventos que captura, normaliza e processa mudancas na jornada do paciente.

## 1. Objetivo

Implementar o motor de eventos MCP (Model-Context-Protocol) dentro da Geralda, responsavel por:
- Capturar eventos da jornada do paciente (clinicos, digitais, operacionais)
- Normalizar eventos em formato padrao IntelliCare
- Garantir idempotencia (evento duplicado nao gera acao duplicada)
- Enriquecer eventos com dados do paciente (Model)
- Acionar contextos e protocolos automaticamente
- Gerar evidencias auditaveis (FHIR AuditEvent)

## 2. Justificativa

- **Reatividade**: Geralda precisa agir automaticamente quando algo muda na jornada
- **Rastreabilidade**: Todo evento e registrado com timestamp, origem e resultado
- **Desacoplamento**: Emissores de eventos nao conhecem os consumidores
- **Auditoria**: Regulatorio (LGPD, ANS) exige registro de acoes automatizadas
- **Escalabilidade**: Novos eventos/handlers podem ser adicionados sem reescrever logica

## 3. Escopo

### 3.1 Pipeline de Processamento (7 Estagios)

```
(1) Recepcao       → Recebe evento bruto (HTTP, Redis, interno)
        |
(2) Normalizacao   → Converte para formato IntelliCareEvent padrao
        |
(3) Idempotencia   → Verifica se evento ja foi processado (dedup)
        |
(4) Enriquecimento → Carrega dados do paciente (Model)
        |
(5) Interpretacao  → Identifica qual contexto de jornada ativar (Context)
        |
(6) Execucao       → Aplica protocolo correspondente (Protocol)
        |
(7) Evidencia      → Gera registro auditavel (FHIR AuditEvent)
```

### 3.2 Estrutura de Arquivos

```
geralda/mcp/
  __init__.py
  events/
    __init__.py
    event_types.py          # Enum + dataclass de tipos de evento
    event_pipeline.py       # Pipeline de 7 estagios
    event_normalizer.py     # Normalizacao de formatos
    event_deduplicator.py   # Idempotencia via Redis/DB
    event_enricher.py       # Enriquecimento com dados do paciente
    event_store.py          # Persistencia de eventos
    event_publisher.py      # Publicacao para consumidores
    event_consumer.py       # Consumidor de eventos externos
```

### 3.3 Formato Padrao de Evento

```python
@dataclass
class IntelliCareEvent:
    """Evento padrao da jornada do paciente."""
    event_id: str                    # UUID unico
    event_type: str                  # ex: "care_plan.created", "medication.taken"
    source: str                      # ex: "geralda", "oswaldo", "florence", "manual"
    patient_id: str                  # ID do paciente
    timestamp: datetime              # Quando ocorreu
    payload: dict                    # Dados especificos do evento
    correlation_id: Optional[str]    # Para rastrear cadeia de eventos
    idempotency_key: str             # Chave para deduplicacao
    metadata: dict                   # Informacoes extras (user_id, ip, etc.)
```

### 3.4 Catalogo de Tipos de Evento

#### Eventos Clinicos (Prefixo: `clinical.`)
| Tipo | Descricao | Origem Tipica |
|------|-----------|---------------|
| `clinical.admission` | Paciente internado | FHIR/Hospital |
| `clinical.discharge` | Alta clinica | FHIR/Hospital |
| `clinical.condition_diagnosed` | Nova condicao diagnosticada | Florence/FHIR |
| `clinical.condition_worsened` | Piora de condicao | Oswaldo |
| `clinical.condition_improved` | Melhora de condicao | Oswaldo |
| `clinical.exam_result` | Resultado de exame disponivel | Florence |
| `clinical.medication_changed` | Medicamento alterado | FHIR |
| `clinical.vital_sign_alert` | Sinal vital fora do normal | Dispositivo/Manual |

#### Eventos de Cuidado (Prefixo: `care.`)
| Tipo | Descricao | Origem Tipica |
|------|-----------|---------------|
| `care.plan_created` | Plano de cuidado criado | Geralda |
| `care.plan_updated` | Plano de cuidado atualizado | Geralda |
| `care.task_completed` | Tarefa do plano concluida | Paciente |
| `care.task_missed` | Tarefa nao realizada no prazo | Timer |
| `care.adherence_low` | Adesao abaixo do limiar | Geralda |
| `care.adherence_improved` | Adesao melhorou | Geralda |
| `care.reminder_sent` | Lembrete enviado | Geralda |
| `care.reminder_acknowledged` | Lembrete confirmado | Paciente |

#### Eventos Digitais (Prefixo: `digital.`)
| Tipo | Descricao | Origem Tipica |
|------|-----------|---------------|
| `digital.patient_onboarded` | Paciente engajado digitalmente | Comunicacao |
| `digital.message_received` | Mensagem do paciente | Synapse |
| `digital.message_read` | Paciente leu mensagem | Synapse |
| `digital.consent_given` | Consentimento digital dado | Portal |
| `digital.preference_updated` | Preferencia atualizada | Portal |
| `digital.education_completed` | Material educativo lido | Geralda |
| `digital.quiz_completed` | Quiz de compreensao feito | Geralda |

#### Eventos Operacionais (Prefixo: `operational.`)
| Tipo | Descricao | Origem Tipica |
|------|-----------|---------------|
| `operational.consultation_scheduled` | Consulta agendada | Agenda |
| `operational.consultation_completed` | Consulta realizada | Profissional |
| `operational.consultation_missed` | Paciente faltou | Timer |
| `operational.teleconsult_scheduled` | Teleconsulta agendada | Comunicacao |
| `operational.teleconsult_completed` | Teleconsulta realizada | Jitsi |
| `operational.discharge_planned` | Alta programada | Equipe |
| `operational.referral_made` | Encaminhamento feito | Profissional |

### 3.5 Normalizador de Eventos

```python
class EventNormalizer:
    """Converte eventos de diversas fontes para formato padrao."""

    def normalize_fhir_event(self, fhir_resource: dict) -> IntelliCareEvent:
        """
        Converte recurso FHIR em evento IntelliCare.

        Ex: FHIR Encounter com status=finished → clinical.discharge
        Ex: FHIR MedicationRequest → clinical.medication_changed
        """

    def normalize_synapse_event(self, matrix_event: dict) -> IntelliCareEvent:
        """
        Converte evento Matrix/Synapse em evento IntelliCare.

        Ex: m.room.message do paciente → digital.message_received
        """

    def normalize_agent_event(self, agent: str, event_data: dict) -> IntelliCareEvent:
        """
        Converte evento de outro agente (Oswaldo, Florence) em evento IntelliCare.

        Ex: Oswaldo alerta piora → clinical.condition_worsened
        """

    def normalize_internal_event(self, event_data: dict) -> IntelliCareEvent:
        """
        Normaliza evento interno da propria Geralda.

        Ex: Calculo de adesao detectou queda → care.adherence_low
        """
```

### 3.6 Deduplicador (Idempotencia)

```python
class EventDeduplicator:
    """Garante que um evento nao seja processado mais de uma vez."""

    def __init__(self, redis_client, ttl_hours: int = 48):
        self._redis = redis_client
        self._ttl = ttl_hours * 3600

    async def is_duplicate(self, event: IntelliCareEvent) -> bool:
        """
        Verifica se idempotency_key ja existe no cache.

        Estrategia:
        - Chave: f"evt:dedup:{event.idempotency_key}"
        - TTL: 48 horas (configuravel)
        - Se existir: evento duplicado
        - Se nao existir: marcar como processado e retornar False
        """

    async def mark_processed(self, event: IntelliCareEvent) -> None:
        """Marca evento como processado no cache."""
```

### 3.7 Enriquecedor de Eventos

```python
class EventEnricher:
    """Enriquece evento com dados do paciente (camada Model do MCP)."""

    def __init__(self, patient_repo, care_plan_repo, fhir_client):
        self._patient_repo = patient_repo
        self._care_plan_repo = care_plan_repo
        self._fhir_client = fhir_client

    async def enrich(self, event: IntelliCareEvent) -> EnrichedEvent:
        """
        Adiciona ao evento:
        - Condicoes ativas do paciente (ICD-10)
        - Planos de cuidado ativos
        - Estagio da jornada (E0-E7)
        - Nivel de risco atual
        - Preferencias do paciente (idioma, canal, horario)
        - Historico recente de eventos (ultimos 30 dias)
        """
```

### 3.8 Tabela de Eventos

```sql
CREATE TABLE journey_events (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID UNIQUE NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(50) NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    correlation_id UUID,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    metadata JSONB DEFAULT '{}',

    -- Resultado do processamento
    processing_status VARCHAR(20) DEFAULT 'received',  -- received, processing, processed, failed, skipped
    context_activated VARCHAR(20),                       -- Qual contexto MCP foi ativado
    protocol_executed VARCHAR(50),                       -- Qual protocolo foi executado
    actions_taken JSONB DEFAULT '[]',                    -- Lista de acoes executadas
    error_message TEXT,                                  -- Se falhou, qual erro

    -- Auditoria
    processed_at TIMESTAMPTZ,
    processing_duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_patient ON journey_events(patient_id);
CREATE INDEX idx_events_type ON journey_events(event_type);
CREATE INDEX idx_events_timestamp ON journey_events(timestamp);
CREATE INDEX idx_events_correlation ON journey_events(correlation_id);
CREATE INDEX idx_events_status ON journey_events(processing_status);

-- Particao por mes para performance (opcional em v2.0, obrigatorio em producao)
-- CREATE TABLE journey_events_2026_02 PARTITION OF journey_events
--     FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
```

### 3.9 Publicador e Consumidor

```python
class EventPublisher:
    """Publica eventos para consumidores internos e externos."""

    def __init__(self, redis_client):
        self._redis = redis_client

    async def publish(self, event: IntelliCareEvent) -> None:
        """
        Publica evento no Redis Stream.

        Stream: intellicare:events:{event.event_type.split('.')[0]}
        Ex: intellicare:events:clinical
        Ex: intellicare:events:care
        Ex: intellicare:events:digital
        """

    async def publish_to_wanda(self, event: IntelliCareEvent) -> None:
        """
        Notifica Wanda sobre evento importante.

        Usa HTTP POST para Wanda /api/v1/events com o evento.
        Wanda decide se precisa acionar outros agentes.
        """


class EventConsumer:
    """Consome eventos de fontes externas via Redis Streams."""

    def __init__(self, redis_client, event_pipeline):
        self._redis = redis_client
        self._pipeline = event_pipeline

    async def start_consuming(self, streams: list[str]) -> None:
        """
        Inicia consumo de eventos de streams Redis.

        Streams consumidos:
        - intellicare:events:clinical   (de Florence, Oswaldo, FHIR)
        - intellicare:events:operational (de agenda, comunicacao)
        - intellicare:events:digital    (de Synapse, Portal)

        Usa consumer group 'geralda' para consumo concorrente.
        """

    async def handle_event(self, raw_event: dict) -> None:
        """Normaliza e alimenta o pipeline."""
```

### 3.10 Pipeline Orquestrador

```python
class EventPipeline:
    """Orquestra o processamento de eventos em 7 estagios."""

    def __init__(
        self,
        normalizer: EventNormalizer,
        deduplicator: EventDeduplicator,
        enricher: EventEnricher,
        context_manager,    # EF-007
        protocol_engine,    # EF-008
        event_store: EventStore,
    ):
        ...

    async def process(self, raw_event: dict, source: str) -> ProcessingResult:
        """
        Executa pipeline completo:

        1. Normalizacao → IntelliCareEvent
        2. Idempotencia → Pula se duplicado
        3. Enriquecimento → EnrichedEvent com dados do paciente
        4. Interpretacao → ContextManager identifica contexto
        5. Execucao → ProtocolEngine executa protocolo
        6. Evidencia → Gera FHIR AuditEvent
        7. Persistencia → Salva evento + resultado no DB

        Returns:
            ProcessingResult com status, contexto ativado, acoes executadas
        """
```

### 3.11 Endpoints

| Metodo | Path | Descricao |
|--------|------|-----------|
| POST | `/api/v1/events` | Recebe evento externo (de outros agentes) |
| POST | `/api/v1/events/internal` | Emite evento interno (da propria Geralda) |
| GET | `/api/v1/events/{patient_id}` | Lista eventos do paciente |
| GET | `/api/v1/events/{patient_id}/timeline` | Timeline de eventos com contextos |
| GET | `/api/v1/events/{event_id}/trace` | Rastreamento completo de um evento |

### 3.12 Metricas Prometheus

```python
# Contadores
events_received_total = Counter("geralda_events_received_total", "Total de eventos recebidos", ["event_type", "source"])
events_processed_total = Counter("geralda_events_processed_total", "Total processados", ["event_type", "status"])
events_deduplicated_total = Counter("geralda_events_deduplicated_total", "Total duplicados ignorados")

# Histogramas
event_processing_duration = Histogram("geralda_event_processing_seconds", "Duracao do processamento")

# Gauges
events_pending = Gauge("geralda_events_pending", "Eventos pendentes na fila")
```

## 4. Testes

- EventNormalizer: FHIR, Synapse, agente, interno (8 testes)
- EventDeduplicator: duplicado, nao duplicado, TTL expirado (5 testes)
- EventEnricher: paciente com dados, sem dados, erro (5 testes)
- EventPipeline: fluxo completo, falha em cada estagio (8 testes)
- EventPublisher: Redis stream, notificacao Wanda (4 testes)
- EventConsumer: consumo, reconexao, erro (4 testes)
- EventStore: persistencia, consulta por paciente, timeline (5 testes)
- Endpoints: POST evento, GET timeline, GET trace (5 testes)
- **Total**: 44+ testes

## 5. Criterios de Aceitacao

- [ ] Pipeline de 7 estagios funcional end-to-end
- [ ] 30+ tipos de evento catalogados e normalizaveis
- [ ] Idempotencia garantida (Redis + DB)
- [ ] Enriquecimento com dados do paciente
- [ ] Publicacao/consumo via Redis Streams
- [ ] Notificacao de eventos importantes para Wanda
- [ ] Tabela journey_events com indices
- [ ] Timeline de eventos consultavel
- [ ] Trace completo de processamento
- [ ] Metricas Prometheus
- [ ] 44+ testes
- [ ] Cobertura >= 85%

## 6. Estimativa de Complexidade

- **Arquivos novos**: ~10
- **Arquivos modificados**: ~3 (config, api, docker)
- **Linhas estimadas**: ~2.000
- **Testes novos**: ~44
