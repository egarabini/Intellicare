"""Persistencia em memoria para intents e resultados de entrega."""

from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from comunicacao.routing.models import CommunicationIntentRecord, DeliveryResultRecord


class RoutingStore(Protocol):
    def save_intent(self, intent: CommunicationIntentRecord) -> None: ...

    def get_intent(self, intent_id: str) -> CommunicationIntentRecord | None: ...

    def list_intents(self) -> list[CommunicationIntentRecord]: ...

    def update_intent(self, intent: CommunicationIntentRecord) -> None: ...

    def append_delivery(self, delivery: DeliveryResultRecord) -> None: ...

    def get_deliveries(self, intent_id: str) -> list[DeliveryResultRecord]: ...

    def find_by_source_event(self, source_module: str, source_event_id: str) -> CommunicationIntentRecord | None: ...


class InMemoryRoutingStore:
    """Store inicial para evolucao incremental do D1."""

    def __init__(self) -> None:
        self._intents: dict[str, CommunicationIntentRecord] = {}
        self._deliveries: dict[str, list[DeliveryResultRecord]] = defaultdict(list)
        self._idempotency_index: dict[tuple[str, str], str] = {}

    def save_intent(self, intent: CommunicationIntentRecord) -> None:
        self._intents[str(intent.id)] = intent
        if intent.source_event_id:
            self._idempotency_index[(intent.source_module, intent.source_event_id)] = str(intent.id)

    def get_intent(self, intent_id: str) -> CommunicationIntentRecord | None:
        return self._intents.get(intent_id)

    def list_intents(self) -> list[CommunicationIntentRecord]:
        return sorted(self._intents.values(), key=lambda x: x.created_at, reverse=True)

    def update_intent(self, intent: CommunicationIntentRecord) -> None:
        self._intents[str(intent.id)] = intent

    def append_delivery(self, delivery: DeliveryResultRecord) -> None:
        self._deliveries[str(delivery.intent_id)].append(delivery)

    def get_deliveries(self, intent_id: str) -> list[DeliveryResultRecord]:
        return list(self._deliveries.get(intent_id, []))

    def find_by_source_event(self, source_module: str, source_event_id: str) -> CommunicationIntentRecord | None:
        intent_id = self._idempotency_index.get((source_module, source_event_id))
        if intent_id is None:
            return None
        return self._intents.get(intent_id)
