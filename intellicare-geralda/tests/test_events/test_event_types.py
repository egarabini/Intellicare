"""Testes para tipos de evento."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from geralda.events.event_types import (
    IntelliCareEvent,
    EventType,
    validate_event_type,
    get_event_category,
    EVENT_CATALOG,
)


class TestIntelliCareEvent:
    """Testes para estrutura de evento."""

    def test_create_event_minimal(self):
        """Testa criar evento com dados mínimos."""
        event = IntelliCareEvent(
            event_type="care.plan_created",
            patient_id="pac-001",
            payload={"plan_id": "plan-123"},
        )

        assert event.event_type == "care.plan_created"
        assert event.patient_id == "pac-001"
        assert event.payload["plan_id"] == "plan-123"
        assert event.event_id is not None
        assert event.idempotency_key is not None

    def test_create_event_full(self):
        """Testa criar evento com todos os campos."""
        event = IntelliCareEvent(
            event_type="clinical.condition_diagnosed",
            source="oswaldo",
            patient_id="pac-002",
            timestamp=datetime.now(timezone.utc),
            payload={"condition": "N18.3"},
            correlation_id="corr-123",
            metadata={"priority": "high"},
        )

        assert event.source == "oswaldo"
        assert event.correlation_id == "corr-123"
        assert event.metadata["priority"] == "high"

    def test_event_generates_unique_id(self):
        """Testa que cada evento tem ID único."""
        event1 = IntelliCareEvent(
            event_type="care.task_completed",
            patient_id="pac-001",
            payload={},
        )
        event2 = IntelliCareEvent(
            event_type="care.task_completed",
            patient_id="pac-001",
            payload={},
        )

        assert event1.event_id != event2.event_id

    def test_event_generates_idempotency_key(self):
        """Testa geração de chave de idempotência."""
        event = IntelliCareEvent(
            event_type="care.plan_created",
            patient_id="pac-001",
            payload={"plan_id": "plan-123"},
        )

        assert event.idempotency_key is not None
        assert len(event.idempotency_key) > 0

    def test_event_to_dict(self):
        """Testa conversão para dicionário."""
        event = IntelliCareEvent(
            event_type="digital.message_received",
            source="comunicacao",
            patient_id="pac-003",
            payload={"message": "Olá"},
        )

        data = event.to_dict()

        assert data["event_type"] == "digital.message_received"
        assert data["source"] == "comunicacao"
        assert data["patient_id"] == "pac-003"
        assert "timestamp" in data

    def test_event_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {
            "event_id": "evt-123",
            "event_type": "operational.consultation_scheduled",
            "source": "geralda",
            "patient_id": "pac-004",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": {"appointment_id": "apt-123"},
            "idempotency_key": "key-123",
        }

        event = IntelliCareEvent.from_dict(data)

        assert event.event_id == "evt-123"
        assert event.event_type == "operational.consultation_scheduled"


class TestEventTypeValidation:
    """Testes para validação de tipos de evento."""

    def test_validate_valid_event_type(self):
        """Testa validação de tipo válido."""
        result = validate_event_type("care.plan_created")

        assert result is True

    def test_validate_invalid_event_type(self):
        """Testa validação de tipo inválido."""
        result = validate_event_type("invalid.event.type")

        assert result is False

    def test_validate_case_sensitive(self):
        """Testa que validação é case-sensitive."""
        result = validate_event_type("Care.Plan_Created")

        assert result is False  # Não existe com maiúsculas

    def test_get_event_category(self):
        """Testa obter categoria do evento."""
        category = get_event_category("care.plan_created")

        assert category == "care"

    def test_get_event_category_clinical(self):
        """Testa categoria clínica."""
        events = [
            "clinical.admission",
            "clinical.condition_diagnosed",
            "clinical.exam_result",
        ]

        for event_type in events:
            category = get_event_category(event_type)
            assert category == "clinical"

    def test_get_event_category_digital(self):
        """Testa categoria digital."""
        events = [
            "digital.patient_onboarded",
            "digital.message_received",
            "digital.preference_updated",
        ]

        for event_type in events:
            category = get_event_category(event_type)
            assert category == "digital"

    def test_get_event_category_invalid(self):
        """Testa categoria para tipo inválido."""
        category = get_event_category("invalid.type")

        assert category is None


class TestEventCatalog:
    """Testes para catálogo de eventos."""

    def test_catalog_exists(self):
        """Testa que catálogo está definido."""
        assert EVENT_CATALOG is not None
        assert len(EVENT_CATALOG) > 0

    def test_catalog_has_minimum_events(self):
        """Testa que catálogo tem pelo menos 30 eventos."""
        assert len(EVENT_CATALOG) >= 30

    def test_catalog_has_all_categories(self):
        """Testa que catálogo tem todas as categorias."""
        categories = set()

        for event_type, info in EVENT_CATALOG.items():
            category = get_event_category(event_type)
            if category:
                categories.add(category)

        # Deve ter pelo menos 4 categorias
        assert len(categories) >= 4
        assert "clinical" in categories
        assert "care" in categories
        assert "digital" in categories
        assert "operational" in categories

    def test_catalog_events_have_descriptions(self):
        """Testa que eventos têm descrições."""
        for event_type, info in EVENT_CATALOG.items():
            assert "description" in info
            assert len(info["description"]) > 0

    def test_catalog_clinical_events(self):
        """Testa eventos clínicos."""
        clinical_events = [k for k in EVENT_CATALOG.keys() if k.startswith("clinical.")]

        assert len(clinical_events) >= 8

    def test_catalog_care_events(self):
        """Testa eventos de cuidado."""
        care_events = [k for k in EVENT_CATALOG.keys() if k.startswith("care.")]

        assert len(care_events) >= 7

    def test_catalog_digital_events(self):
        """Testa eventos digitais."""
        digital_events = [k for k in EVENT_CATALOG.keys() if k.startswith("digital.")]

        assert len(digital_events) >= 5

    def test_catalog_operational_events(self):
        """Testa eventos operacionais."""
        operational_events = [k for k in EVENT_CATALOG.keys() if k.startswith("operational.")]

        assert len(operational_events) >= 6


class TestEventPayloads:
    """Testes para payloads de eventos."""

    def test_event_payload_accepts_various_types(self):
        """Testa que payload aceita vários tipos."""
        payloads = [
            {"string": "value"},
            {"number": 123},
            {"bool": True},
            {"list": [1, 2, 3]},
            {"nested": {"key": "value"}},
        ]

        for payload in payloads:
            event = IntelliCareEvent(
                event_type="test.event",
                patient_id="pac-001",
                payload=payload,
            )

            assert event.payload == payload

    def test_event_payload_empty(self):
        """Testa payload vazio."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        assert event.payload == {}

    def test_event_payload_none(self):
        """Testa payload None."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload=None,
        )

        assert event.payload is None or event.payload == {}


class TestEventTimestamps:
    """Testes para timestamps."""

    def test_event_has_timestamp(self):
        """Testa que evento tem timestamp."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)

    def test_event_custom_timestamp(self):
        """Testa timestamp customizado."""
        custom_time = datetime(2026, 2, 24, 12, 0, 0, tzinfo=timezone.utc)

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
            timestamp=custom_time,
        )

        assert event.timestamp == custom_time

    def test_event_timestamp_utc(self):
        """Testa que timestamp usa UTC."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        # Timestamp deve ter timezone info
        assert event.timestamp.tzinfo is not None


class TestEventCorrelation:
    """Testes para correlação de eventos."""

    def test_events_with_correlation_id(self):
        """Testa eventos correlacionados."""
        correlation_id = str(uuid4())

        event1 = IntelliCareEvent(
            event_type="care.plan_created",
            patient_id="pac-001",
            payload={},
            correlation_id=correlation_id,
        )

        event2 = IntelliCareEvent(
            event_type="care.task_created",
            patient_id="pac-001",
            payload={},
            correlation_id=correlation_id,
        )

        assert event1.correlation_id == event2.correlation_id
        assert event1.correlation_id == correlation_id

    def test_events_without_correlation_id(self):
        """Testa eventos sem correlação."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        assert event.correlation_id is None
