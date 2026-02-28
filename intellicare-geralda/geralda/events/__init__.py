"""Motor de eventos da jornada do paciente."""

from geralda.events.event_pipeline import EventPipeline, create_pipeline
from geralda.events.event_deduplicator import EventDeduplicator
from geralda.events.event_enricher import EventEnricher, EnrichedEvent
from geralda.events.event_normalizer import EventNormalizer
from geralda.events.event_publisher import EventPublisher
from geralda.events.event_store import EventStore
from geralda.events.event_types import (
    IntelliCareEvent,
    ProcessingResult,
    EventType,
    create_idempotency_key,
    emit_event,
)

__all__ = [
    "EventPipeline",
    "create_pipeline",
    "EventDeduplicator",
    "EventEnricher",
    "EnrichedEvent",
    "EventNormalizer",
    "EventPublisher",
    "EventStore",
    "IntelliCareEvent",
    "ProcessingResult",
    "EventType",
    "create_idempotency_key",
    "emit_event",
]
