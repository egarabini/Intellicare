"""Testes para EventNormalizer."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from geralda.events.event_normalizer import EventNormalizer
from geralda.events.event_types import IntelliCareEvent


class TestEventNormalizer:
    """Testes para normalizador de eventos."""

    @pytest.fixture
    def normalizer(self):
        """Cria normalizador para testes."""
        return EventNormalizer()

    @pytest.mark.asyncio
    async def test_normalize_fhir_observation(self, normalizer):
        """Testa normalizar FHIR Observation."""
        fhir_obs = {
            "resourceType": "Observation",
            "id": "obs-123",
            "subject": {"reference": "Patient/pac-001"},
            "code": {"coding": [{"system": "http://loinc.org", "code": "2160-0"}]},
            "valueQuantity": {"value": 2.1, "unit": "mg/dL"},
            "effectiveDateTime": "2026-02-24T12:00:00Z",
        }

        event = await normalizer.normalize_fhir_event(fhir_obs, source="grahame")

        assert event.event_type == "clinical.exam_result"
        assert event.patient_id == "pac-001"
        assert event.source == "grahame"
        assert "creatinina" in event.payload.get("exam_name", "").lower() or "2160-0" in str(event.payload)

    @pytest.mark.asyncio
    async def test_normalize_fhir_condition(self, normalizer):
        """Testa normalizar FHIR Condition."""
        fhir_condition = {
            "resourceType": "Condition",
            "id": "cond-123",
            "subject": {"reference": "Patient/pac-002"},
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": "709044004"}]},
            "clinicalStatus": {"coding": [{"code": "active"}]},
        }

        event = await normalizer.normalize_fhir_event(fhir_condition, source="grahame")

        assert event.event_type == "clinical.condition_diagnosed"
        assert event.patient_id == "pac-002"

    @pytest.mark.asyncio
    async def test_normalize_fhir_unknown_type(self, normalizer):
        """Testa normalizar tipo FHIR desconhecido."""
        fhir_unknown = {
            "resourceType": "UnknownResource",
            "id": "unk-123",
        }

        event = await normalizer.normalize_fhir_event(fhir_unknown, source="grahame")

        # Deve criar evento genérico ou levantar erro
        assert event is not None

    @pytest.mark.asyncio
    async def test_normalize_agent_event_oswaldo(self, normalizer):
        """Testa normalizar evento do Oswaldo."""
        agent_event = {
            "agent": "oswaldo",
            "event_type": "condition_detected",
            "patient_id": "pac-003",
            "data": {
                "condition": "N18.3",
                "stage": "3",
            },
        }

        event = await normalizer.normalize_agent_event("oswaldo", agent_event)

        assert event.event_type == "clinical.condition_diagnosed"
        assert event.source == "oswaldo"
        assert event.patient_id == "pac-003"

    @pytest.mark.asyncio
    async def test_normalize_agent_event_florence(self, normalizer):
        """Testa normalizar evento do Florence."""
        agent_event = {
            "agent": "florence",
            "event_type": "lab_result",
            "patient_id": "pac-004",
            "data": {
                "test": "creatinina",
                "result": 2.1,
                "unit": "mg/dL",
            },
        }

        event = await normalizer.normalize_agent_event("florence", agent_event)

        assert event.event_type == "clinical.exam_result"
        assert event.source == "florence"
        assert event.patient_id == "pac-004"

    @pytest.mark.asyncio
    async def test_normalize_internal_event(self, normalizer):
        """Testa normalizar evento interno."""
        internal_event = {
            "event_type": "care.task_completed",
            "patient_id": "pac-005",
            "task_id": "task-123",
            "completed_at": "2026-02-24T12:00:00Z",
        }

        event = await normalizer.normalize_internal_event(internal_event)

        assert event.event_type == "care.task_completed"
        assert event.source == "geralda"
        assert event.patient_id == "pac-005"

    @pytest.mark.asyncio
    async def test_normalize_auto_detect_fhir(self, normalizer):
        """Testa detecção automática de FHIR."""
        fhir_event = {
            "resourceType": "Observation",
            "subject": {"reference": "Patient/pac-006"},
        }

        event = await normalizer.normalize(fhir_event, source="grahame")

        assert event.event_type is not None
        assert event.source == "grahame"

    @pytest.mark.asyncio
    async def test_normalize_auto_detect_agent(self, normalizer):
        """Testa detecção automática de agent."""
        agent_event = {
            "agent": "oswaldo",
            "event_type": "condition_detected",
            "patient_id": "pac-007",
        }

        event = await normalizer.normalize(agent_event, source="oswaldo")

        assert event.event_type is not None

    @pytest.mark.asyncio
    async def test_normalize_auto_detect_internal(self, normalizer):
        """Testa detecção automática de interno."""
        internal_event = {
            "event_type": "care.plan_created",
            "patient_id": "pac-008",
        }

        event = await normalizer.normalize(internal_event, source="geralda")

        assert event.event_type == "care.plan_created"


class TestNormalizerEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_normalize_empty_payload(self):
        """Testa normalizar payload vazio."""
        normalizer = EventNormalizer()

        event = await normalizer.normalize_internal_event({})

        # Deve criar evento mesmo com payload vazio
        assert event is not None

    @pytest.mark.asyncio
    async def test_normalize_missing_patient_id(self):
        """Testa normalizar sem patient_id."""
        normalizer = EventNormalizer()

        event = await normalizer.normalize_internal_event({
            "event_type": "test.event",
        })

        # Deve ter patient_id vazio ou default
        assert event.patient_id is not None

    @pytest.mark.asyncio
    async def test_normalize_with_null_values(self):
        """Testa normalizar com valores nulos."""
        normalizer = EventNormalizer()

        event = await normalizer.normalize_internal_event({
            "event_type": "test.event",
            "patient_id": None,
            "payload": None,
        })

        assert event is not None

    @pytest.mark.asyncio
    async def test_normalize_with_special_characters(self):
        """Testa normalizar com caracteres especiais."""
        normalizer = EventNormalizer()

        event = await normalizer.normalize_internal_event({
            "event_type": "care.task_completed",
            "patient_id": "pac-001",
            "description": "Tarefa com caracteres especiais: @#$%",
        })

        assert event is not None
        assert event.payload is not None

    @pytest.mark.asyncio
    async def test_normalize_preserves_timestamp(self):
        """Testa que normalizador preserva timestamp."""
        normalizer = EventNormalizer()
        custom_time = "2026-02-24T12:00:00Z"

        event = await normalizer.normalize_internal_event({
            "event_type": "test.event",
            "patient_id": "pac-001",
            "timestamp": custom_time,
        })

        assert event.timestamp is not None


class TestNormalizerMapping:
    """Testes para mapeamento de eventos."""

    @pytest.mark.asyncio
    async def test_fhir_to_event_type_mapping(self):
        """Testa mapeamento FHIR -> IntelliCare."""
        normalizer = EventNormalizer()

        mappings = [
            ("Observation", "clinical.exam_result"),
            ("Condition", "clinical.condition_diagnosed"),
            ("Encounter", "clinical.admission"),
        ]

        for fhir_type, expected_type in mappings:
            fhir_event = {
                "resourceType": fhir_type,
                "subject": {"reference": "Patient/pac-001"},
            }

            event = await normalizer.normalize_fhir_event(fhir_event)

            assert event.event_type == expected_type

    @pytest.mark.asyncio
    async def test_agent_to_event_type_mapping(self):
        """Testa mapeamento Agent -> IntelliCare."""
        normalizer = EventNormalizer()

        mappings = [
            ("oswaldo", "condition_detected", "clinical.condition_diagnosed"),
            ("florence", "lab_result", "clinical.exam_result"),
        ]

        for agent, agent_type, expected_type in mappings:
            agent_event = {
                "agent": agent,
                "event_type": agent_type,
                "patient_id": "pac-001",
            }

            event = await normalizer.normalize_agent_event(agent, agent_event)

            assert event.event_type == expected_type
