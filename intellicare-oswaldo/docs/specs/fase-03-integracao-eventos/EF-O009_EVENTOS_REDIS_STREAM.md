# EF-O009 — Publicacao de Eventos (Redis Stream)

> Publicar alertas criticos e mudancas de estadio no Redis Stream para consumo pela Wanda, Geralda e Comunicacao, completando o ciclo de eventos do ecossistema IntelliCare.

## 1. Objetivo

Implementar publicacao de eventos no Redis Stream sempre que o Oswaldo:
- Gera um alerta de severidade CRITICAL ou WARNING
- Detecta mudanca de estadio em uma doenca cronica
- Identifica progressao acelerada (slope acima do threshold)
- Produz recomendacao de urgencia IMMEDIATE ou HIGH

Estes eventos sao consumidos por:
- **Wanda**: para roteamento proativo e alertas consolidados
- **Geralda**: para atualizar a jornada do paciente e acoes de acompanhamento
- **Comunicacao**: para notificacoes ao profissional de saude responsavel

## 2. Justificativa

- Atualmente alertas sao gerados mas ficam "presos" no Oswaldo — ninguem sabe
- O codigo legacy (`src/oswaldo/integrations/`) tinha RabbitMQ mas nao foi portado para o core
- EF-W006 (Wanda Orquestracao Proativa) espera eventos no stream `intellicare:clinical`
- EF-G006 (Geralda Motor de Eventos) consome stream `intellicare:clinical`
- Sem eventos, o ecossistema nao reage automaticamente a pioras clinicas

## 3. Escopo

### 3.1 Eventos Publicados

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OswaldoEvent:
    """
    Evento publicado pelo Oswaldo no Redis Stream.
    Formato compativel com o protocolo de eventos do ecossistema IntelliCare.
    """
    event_id: str                    # UUID
    event_type: str                  # Ver OSWALDO_EVENT_TYPES abaixo
    source: str = "oswaldo"
    version: str = "1.0"

    patient_id: str = ""
    disease_id: Optional[str] = None  # "ckd", "dm2", etc.

    # Dados do evento
    payload: dict = field(default_factory=dict)
    severity: str = "info"            # "info", "warning", "critical"

    # Metadados
    timestamp: str = ""              # ISO 8601
    correlation_id: Optional[str] = None  # ID da analise que gerou o evento


# Tipos de evento do Oswaldo
OSWALDO_EVENT_TYPES = {
    # Alertas clinicos
    "clinical.alert.critical": "Alerta critico gerado (valor absoluto)",
    "clinical.alert.warning": "Alerta de atencao gerado",

    # Estadiamento
    "clinical.staging.changed": "Mudanca de estadio detectada",
    "clinical.staging.calculated": "Estadiamento calculado (periodico)",

    # Progressao
    "clinical.progression.accelerated": "Progressao acelerada detectada",
    "clinical.progression.stable": "Progressao estavel (rotina)",

    # Recomendacoes urgentes
    "clinical.recommendation.urgent": "Recomendacao urgente (immediate/high)",
}
```

### 3.2 OswaldoEventPublisher

```python
class OswaldoEventPublisher:
    """
    Publica eventos no Redis Stream 'intellicare:clinical'.

    Stream: intellicare:clinical
    Consumer groups: wanda, geralda, comunicacao

    Retencao: Redis Stream com MAXLEN 10.000 (FIFO, remove mais antigos)
    Timeout: 2s para publicacao (nao bloqueia o fluxo principal)
    """

    STREAM_NAME = "intellicare:clinical"
    MAX_STREAM_LENGTH = 10_000
    PUBLISH_TIMEOUT_S = 2.0

    def __init__(self, redis_client):
        self._redis = redis_client

    async def publish_alert(
        self,
        alert: Alert,
        patient_id: str,
        disease_id: str,
        correlation_id: Optional[str] = None,
    ) -> bool:
        """
        Publica alerta critico ou warning no stream.

        So publica WARNING e CRITICAL — INFO e silencioso.
        Retorna True se publicado, False se falhou (nao lanca excecao).
        """
        if alert.severity == SeverityLevel.INFO:
            return False

        event = OswaldoEvent(
            event_id=str(uuid4()),
            event_type=f"clinical.alert.{alert.severity.value}",
            patient_id=patient_id,
            disease_id=disease_id,
            severity=alert.severity.value,
            payload={
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "observation_id": alert.observation_id,
                "current_value": alert.metadata.get("current_value"),
                "threshold": alert.metadata.get("threshold"),
            },
            correlation_id=correlation_id,
        )
        return await self._publish(event)

    async def publish_stage_change(
        self,
        patient_id: str,
        disease_id: str,
        previous_stage: str,
        new_stage: str,
        staging_result: StagingResult,
    ) -> bool:
        """
        Publica mudanca de estadio.
        Sempre publica (independente da severidade) — mudanca e clinicamente relevante.
        """
        event = OswaldoEvent(
            event_type="clinical.staging.changed",
            patient_id=patient_id,
            disease_id=disease_id,
            severity=staging_result.severity.value,
            payload={
                "previous_stage": previous_stage,
                "new_stage": new_stage,
                "stage_label": staging_result.stage_label,
                "confidence_score": staging_result.confidence_score,
                "key_values": staging_result.axes,
            },
        )
        return await self._publish(event)

    async def publish_urgent_recommendation(
        self,
        patient_id: str,
        disease_id: str,
        recommendation: ClinicalRecommendation,
    ) -> bool:
        """
        Publica recomendacao urgente (IMMEDIATE ou HIGH).
        """
        if recommendation.urgency not in (
            RecommendationUrgency.IMMEDIATE,
            RecommendationUrgency.HIGH
        ):
            return False

        event = OswaldoEvent(
            event_type="clinical.recommendation.urgent",
            patient_id=patient_id,
            disease_id=disease_id,
            severity="critical" if recommendation.urgency == RecommendationUrgency.IMMEDIATE else "warning",
            payload={
                "rec_id": recommendation.rec_id,
                "title": recommendation.title,
                "category": recommendation.category,
                "urgency": recommendation.urgency.value,
                "guideline": recommendation.guideline_id,
                "evidence_level": recommendation.evidence_level.value,
            },
        )
        return await self._publish(event)

    async def _publish(
        self,
        event: OswaldoEvent,
    ) -> bool:
        """
        Publica no Redis Stream com timeout e tratamento de erro.

        Formato Redis Stream: {field: value, ...}
        Nunca lanca excecao — retorna False em falha.
        """
        try:
            event_dict = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "source": event.source,
                "patient_id": event.patient_id,
                "disease_id": event.disease_id or "",
                "severity": event.severity,
                "payload": json.dumps(event.payload),
                "timestamp": event.timestamp,
            }
            await asyncio.wait_for(
                self._redis.xadd(
                    self.STREAM_NAME,
                    event_dict,
                    maxlen=self.MAX_STREAM_LENGTH,
                ),
                timeout=self.PUBLISH_TIMEOUT_S,
            )
            return True
        except Exception:
            # Log mas nao propaga — publicacao de evento nao pode derrubar o servico
            logger.warning(f"Failed to publish event {event.event_id} to Redis Stream")
            return False
```

### 3.3 Integracao no ChronicDiseaseEngine

```python
# Apos calcular alerts em generate_alerts():
for alert in alerts:
    asyncio.create_task(
        self._event_publisher.publish_alert(alert, patient_id, disease_id)
    )  # fire-and-forget: nao aguarda publicacao

# Apos calcular staging em calculate_staging():
if stage_changed:
    asyncio.create_task(
        self._event_publisher.publish_stage_change(
            patient_id, disease_id, prev_stage, new_stage, staging_result
        )
    )

# Apos gerar recommendations em generate_recommendations():
for rec in urgent_recs:
    asyncio.create_task(
        self._event_publisher.publish_urgent_recommendation(patient_id, disease_id, rec)
    )
```

### 3.4 Configuracao

```env
INTELLICARE_REDIS_URL=redis://redis:6379
INTELLICARE_REDIS_ENABLED=true
INTELLICARE_OSWALDO_EVENT_STREAM=intellicare:clinical
INTELLICARE_OSWALDO_EVENTS_ENABLED=true
INTELLICARE_OSWALDO_EVENT_TIMEOUT_MS=2000
```

### 3.5 Arquitetura de Arquivos

```
oswaldo/
  events/
    __init__.py
    publisher.py           # OswaldoEventPublisher
    models.py              # OswaldoEvent + OSWALDO_EVENT_TYPES
```

## 4. Testes

- OswaldoEventPublisher: publish_alert critico, warning, info (ignorado) (3 testes)
- publish_stage_change: mudanca real, mesmo estadio (2 testes)
- publish_urgent_recommendation: immediate, high, low (ignorado) (3 testes)
- Redis indisponivel: nao lanca excecao, retorna False (2 testes)
- Timeout: publicacao mais lenta que 2s (1 teste)
- Integracao ChronicDiseaseEngine: eventos disparados apos calculos (3 testes)
- **Total**: 14+ testes novos

## 5. Criterios de Aceitacao

- [ ] `OswaldoEventPublisher` com 3 metodos de publicacao
- [ ] Apenas WARNING e CRITICAL publicados para alertas (INFO silencioso)
- [ ] Mudancas de estadio sempre publicadas
- [ ] Recomendacoes IMMEDIATE e HIGH publicadas
- [ ] Redis indisponivel: graceful degradation (nao derruba servico)
- [ ] Timeout de 2s para publicacao (fire-and-forget)
- [ ] Stream `intellicare:clinical` com MAXLEN 10.000
- [ ] Formato de evento compativel com EF-W006 (Wanda)
- [ ] 98 testes v1.0 continuam passando
- [ ] 14+ testes novos
- [ ] Cobertura >= 83%

## 6. Estimativa de Complexidade

- **Arquivos novos**: `events/publisher.py`, `events/models.py`
- **Arquivos modificados**: `engine/core_logic.py` (fire-and-forget), `config.py`, `api/app.py` (inicializar Redis)
- **Linhas estimadas**: ~250
- **Testes novos**: ~14
