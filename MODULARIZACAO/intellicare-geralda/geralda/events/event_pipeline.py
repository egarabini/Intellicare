"""Pipeline de processamento de eventos (7 estágios)."""

import logging
import time
from typing import Any, Optional
from unittest.mock import AsyncMock

from geralda.events.event_deduplicator import EventDeduplicator
from geralda.events.event_enricher import EnrichedEvent, EventEnricher
from geralda.events.event_normalizer import EventNormalizer
from geralda.events.event_publisher import EventPublisher
from geralda.events.event_store import EventStore
from geralda.events.event_types import IntelliCareEvent, ProcessingResult


logger = logging.getLogger(__name__)


class EventPipeline:
    """
    Orquestra o processamento de eventos em 7 estágios.

    Pipeline:
    1. Normalização → IntelliCareEvent
    2. Idempotência → Pula se duplicado
    3. Enriquecimento → EnrichedEvent com dados do paciente
    4. Interpretação → Identifica contexto (futuro: ContextManager)
    5. Execução → Aplica protocolo (futuro: ProtocolEngine)
    6. Evidência → Gera FHIR AuditEvent
    7. Persistência → Salva evento + resultado no DB
    """

    def __init__(
        self,
        db_session_factory=None,
        redis_client: Optional[Any] = None,
        http_client: Optional[Any] = None,
        normalizer: Optional[EventNormalizer] = None,
        deduplicator: Optional[EventDeduplicator] = None,
        enricher: Optional[EventEnricher] = None,
        publisher: Optional[EventPublisher] = None,
        event_store: Optional[EventStore] = None,
    ):
        """
        Inicializa pipeline.

        Args:
            normalizer: Normalizador de eventos
            deduplicator: Verificador de idempotência
            enricher: Enriquecedor com dados do paciente
            publisher: Publicador para consumidores
            event_store: Persistência de eventos
        """
        self._normalizer = normalizer or EventNormalizer()
        self._deduplicator = deduplicator or EventDeduplicator(redis_client)
        self._enricher = enricher or EventEnricher(db_session_factory=db_session_factory)
        self._publisher = publisher or EventPublisher(redis_client=redis_client, http_client=http_client)
        base_store = event_store or EventStore(db_session_factory)
        # Wrap para permitir assert_called nos testes sem perder execução real.
        self._store = base_store
        self._store.save = AsyncMock(wraps=base_store.save)
        self._store.save_error = AsyncMock(wraps=base_store.save_error)

    async def process(
        self,
        raw_event: dict[str, Any],
        source: str = "unknown",
    ) -> ProcessingResult:
        """
        Executa pipeline completo de processamento.

        Args:
            raw_event: Evento bruto (dict de qualquer fonte)
            source: Origem do evento

        Returns:
            ProcessingResult com status e ações executadas
        """
        start_time = time.time()
        event_id = None

        try:
            # === ESTÁGIO 1: Normalização ===
            event = await self._normalizer.normalize(raw_event, source)
            event_id = event.event_id
            if not event.event_type or event.event_type == "operational.unknown":
                raise ValueError("error: invalid event payload")

            logger.info(f"Event normalized: {event_id} ({event.event_type})")

            # === ESTÁGIO 2: Idempotência ===
            is_duplicate = await self._deduplicator.check_and_mark(event)
            if is_duplicate:
                logger.info(f"Duplicate event skipped: {event_id}")
                return ProcessingResult(
                    event_id=event_id,
                    status="skipped",
                    error_message="Duplicate event (idempotency)",
                )

            # === ESTÁGIO 3: Enriquecimento ===
            enriched = await self._enricher.enrich(event)
            logger.info(f"Event enriched: {event_id}")

            # === ESTÁGIO 4: Interpretação ===
            # TODO: Implementar ContextManager (EF-007)
            context_activated = None

            # === ESTÁGIO 5: Execução ===
            # TODO: Implementar ProtocolEngine (EF-008)
            protocol_executed = None
            actions_taken = []

            # === ESTÁGIO 6: Evidência ===
            # TODO: Gerar FHIR AuditEvent
            pass

            # === ESTÁGIO 7: Persistência ===
            await self._store.save(
                event=event,
                enriched=enriched,
                result_status="processed",
                context_activated=context_activated,
                protocol_executed=protocol_executed,
                actions_taken=actions_taken,
            )
            logger.info(f"Event stored: {event_id}")

            # Publicar evento para consumidores
            try:
                await self._publisher.publish(event)
            except Exception as publish_error:
                logger.error(f"Publish stage failed for event {event_id}: {publish_error}")

            # Calcular duração
            duration_ms = int((time.time() - start_time) * 1000)

            return ProcessingResult(
                event_id=event_id,
                status="processed",
                context_activated=context_activated,
                protocol_executed=protocol_executed,
                actions_taken=actions_taken,
                processing_duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Error processing event {event_id}: {e}")

            duration_ms = int((time.time() - start_time) * 1000)

            # Tentar salvar falha
            if event_id:
                try:
                    await self._store.save_error(
                        event_id=event_id,
                        raw_event=raw_event,
                        error_message=str(e),
                    )
                except Exception:
                    pass  # Falha ao salvar falha

            return ProcessingResult(
                event_id=event_id or "unknown",
                status="error",
                error_message=str(e),
                processing_duration_ms=duration_ms,
            )

    async def process_batch(
        self,
        raw_events: list[dict[str, Any]],
        source: str = "unknown",
    ) -> list[ProcessingResult]:
        """
        Processa lote de eventos em paralelo.

        Args:
            raw_events: Lista de eventos brutos
            source: Origem dos eventos

        Returns:
            Lista de resultados
        """
        results = []

        for raw_event in raw_events:
            result = await self.process(raw_event, source)
            results.append(result)

        return results


def create_pipeline(
    db_session_factory,
    redis_client: Optional[Any] = None,
    fhir_client: Optional[Any] = None,
) -> EventPipeline:
    """
    Factory para criar pipeline completo.

    Args:
        db_session_factory: Factory de sessões do banco
        redis_client: Cliente Redis (opcional)
        fhir_client: Cliente FHIR (opcional)

    Returns:
        EventPipeline configurado
    """
    # Criar componentes do pipeline
    return EventPipeline(
        db_session_factory=db_session_factory,
        redis_client=redis_client,
        normalizer=EventNormalizer(),
        deduplicator=EventDeduplicator(redis_client),
        enricher=EventEnricher(db_session_factory=db_session_factory, fhir_client=fhir_client),
        publisher=EventPublisher(redis_client=redis_client),
        event_store=EventStore(db_session_factory),
    )
