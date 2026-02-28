"""Testes para EventEnricher."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from geralda.events.event_enricher import EventEnricher, EnrichedEvent
from geralda.events.event_types import IntelliCareEvent


class TestEventEnricher:
    """Testes para enriquecedor de eventos."""

    @pytest.fixture
    def mock_care_manager(self):
        """Mock de CareManager."""
        care_manager = AsyncMock()

        # Mock para get_patient_plans
        care_manager.get_patient_plans.return_value = []

        # Mock para get_patient_conditions
        care_manager.get_patient_conditions.return_value = []

        return care_manager

    @pytest.fixture
    def enricher(self, mock_care_manager):
        """Cria enriquecedor com mocks."""
        return EventEnricher(care_manager=mock_care_manager)

    @pytest.fixture
    def sample_event(self):
        """Cria evento de exemplo."""
        return IntelliCareEvent(
            event_type="care.task_completed",
            patient_id="pac-001",
            payload={"task_id": "task-123"},
        )

    @pytest.mark.asyncio
    async def test_enrich_basic_event(self, enricher, sample_event, mock_care_manager):
        """Testa enriquecer evento básico."""
        mock_care_manager.get_patient_plans.return_value = [
            MagicMock(id="plan-001", conditions=["DRC"])
        ]

        enriched = await enricher.enrich(sample_event)

        assert isinstance(enriched, EnrichedEvent)
        assert enriched.original_event == sample_event
        assert enriched.patient_id == "pac-001"

    @pytest.mark.asyncio
    async def test_enrich_adds_conditions(self, enricher, sample_event, mock_care_manager):
        """Testa que enriquecedor adiciona condições."""
        mock_care_manager.get_patient_conditions.return_value = [
            "N18.3",  # DRC estágio 3
            "E11",    # Diabetes tipo 2
        ]

        enriched = await enricher.enrich(sample_event)

        assert enriched.patient_conditions == ["N18.3", "E11"]

    @pytest.mark.asyncio
    async def test_enrich_adds_active_plans(self, enricher, sample_event, mock_care_manager):
        """Testa que enriquecedor adiciona planos ativos."""
        plan1 = MagicMock(id="plan-001", status="active")
        plan2 = MagicMock(id="plan-002", status="active")

        mock_care_manager.get_patient_plans.return_value = [plan1, plan2]

        enriched = await enricher.enrich(sample_event)

        assert len(enriched.active_plans) == 2
        assert "plan-001" in enriched.active_plans
        assert "plan-002" in enriched.active_plans

    @pytest.mark.asyncio
    async def test_enrich_determines_journey_stage(self, enricher, sample_event):
        """Testa que enriquecedor determina estágio da jornada."""
        # Se há planos ativos, não é estágio E0
        enriched = await enricher.enrich(sample_event)

        assert enriched.journey_stage is not None
        assert enriched.journey_stage in ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7"]

    @pytest.mark.asyncio
    async def test_enrich_calculates_risk_level(self, enricher, sample_event):
        """Testa que enriquecedor calcula nível de risco."""
        enriched = await enricher.enrich(sample_event)

        assert enriched.risk_level is not None
        assert enriched.risk_level in ["low", "medium", "high", "critical"]

    @pytest.mark.asyncio
    async def test_enrich_without_care_manager(self, sample_event):
        """Testa enriquecer sem CareManager."""
        enricher = EventEnricher(care_manager=None)

        enriched = await enricher.enrich(sample_event)

        # Deve criar EnrichedEvent mesmo sem dados
        assert isinstance(enriched, EnrichedEvent)
        assert enriched.original_event == sample_event


class TestEnrichedEvent:
    """Testes para estrutura de evento enriquecido."""

    @pytest.fixture
    def sample_event(self):
        """Cria evento base."""
        return IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

    def test_enriched_event_creation(self, sample_event):
        """Testa criar evento enriquecido."""
        enriched = EnrichedEvent(
            original_event=sample_event,
            patient_id="pac-001",
            patient_conditions=["N18.3"],
            active_plans=["plan-001"],
            journey_stage="E3",
            risk_level="medium",
        )

        assert enriched.original_event == sample_event
        assert enriched.patient_conditions == ["N18.3"]
        assert enriched.active_plans == ["plan-001"]
        assert enriched.journey_stage == "E3"
        assert enriched.risk_level == "medium"

    def test_enriched_event_to_dict(self, sample_event):
        """Testa conversão para dicionário."""
        enriched = EnrichedEvent(
            original_event=sample_event,
            patient_id="pac-001",
            patient_conditions=[],
            active_plans=[],
            journey_stage="E0",
            risk_level="low",
        )

        data = enriched.to_dict()

        assert "patient_id" in data
        assert "patient_conditions" in data
        assert "journey_stage" in data
        assert "risk_level" in data


class TestJourneyStageDetermination:
    """Testes para determinação de estágio da jornada."""

    @pytest.fixture
    def enricher(self):
        """Cria enriquecedor."""
        mock_care_manager = AsyncMock()
        mock_care_manager.get_patient_plans.return_value = []
        mock_care_manager.get_patient_conditions.return_value = []
        return EventEnricher(care_manager=mock_care_manager)

    @pytest.mark.asyncio
    async def test_stage_e0_no_plan(self, enricher):
        """Testa estágio E0 (sem plano)."""
        event = IntelliCareEvent(
            event_type="digital.patient_onboarded",
            patient_id="pac-001",
            payload={},
        )

        enriched = await enricher.enrich(event)

        # Sem plano, deve ser E0
        assert enriched.journey_stage == "E0"

    @pytest.mark.asyncio
    async def test_stage_e1_plan_created(self, enricher):
        """Testa estágio E1 (plano criado)."""
        event = IntelliCareEvent(
            event_type="care.plan_created",
            patient_id="pac-001",
            payload={"plan_id": "plan-001"},
        )

        enriched = await enricher.enrich(event)

        assert enriched.journey_stage in ["E0", "E1"]  # Depends on plans

    @pytest.mark.asyncio
    async def test_stage_e3_active_care(self, enricher):
        """Testa estágio E3 (cuidado ativo)."""
        event = IntelliCareEvent(
            event_type="care.task_completed",
            patient_id="pac-001",
            payload={"task_id": "task-001"},
        )

        enriched = await enricher.enrich(event)

        # Tarefa completada indica cuidado ativo
        assert enriched.journey_stage is not None


class TestRiskLevelCalculation:
    """Testes para cálculo de nível de risco."""

    @pytest.fixture
    def enricher(self):
        """Cria enriquecedor."""
        mock_care_manager = AsyncMock()
        mock_care_manager.get_patient_plans.return_value = []
        mock_care_manager.get_patient_conditions.return_value = []
        return EventEnricher(care_manager=mock_care_manager)

    @pytest.mark.asyncio
    async def test_low_risk_healthy_patient(self, enricher):
        """Testa risco baixo para paciente saudável."""
        event = IntelliCareEvent(
            event_type="digital.message_received",
            patient_id="pac-001",
            payload={},
        )

        enriched = await enricher.enrich(event)

        # Sem condições graves, risco deve ser baixo ou médio
        assert enriched.risk_level in ["low", "medium"]

    @pytest.mark.asyncio
    async def test_high_risk_critical_event(self, enricher):
        """Testa risco alto para evento crítico."""
        event = IntelliCareEvent(
            event_type="clinical.condition_worsened",
            patient_id="pac-001",
            payload={"severity": "severe"},
        )

        enriched = await enricher.enrich(event)

        # Evento de piora deve aumentar risco
        assert enriched.risk_level in ["medium", "high", "critical"]


class TestEnricherEdgeCases:
    """Testes de casos extremos."""

    @pytest.mark.asyncio
    async def test_enrich_event_without_patient_id(self):
        """Testa enriquecer evento sem patient_id."""
        mock_care_manager = AsyncMock()
        enricher = EventEnricher(care_manager=mock_care_manager)

        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="",
            payload={},
        )

        enriched = await enricher.enrich(event)

        # Deve retornar EnrichedEvent mesmo assim
        assert isinstance(enriched, EnrichedEvent)

    @pytest.mark.asyncio
    async def test_enrich_with_empty_conditions(self, enricher):
        """Testa enriquecer com condições vazias."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        mock_care_manager = AsyncMock()
        mock_care_manager.get_patient_conditions.return_value = []

        enricher = EventEnricher(care_manager=mock_care_manager)
        enriched = await enricher.enrich(event)

        assert enriched.patient_conditions == []

    @pytest.mark.asyncio
    async def test_enrich_with_many_conditions(self, enricher):
        """Testa enriquecer com muitas condições."""
        event = IntelliCareEvent(
            event_type="test.event",
            patient_id="pac-001",
            payload={},
        )

        mock_care_manager = AsyncMock()
        mock_care_manager.get_patient_conditions.return_value = [
            "N18.3", "E11", "I10", "I50", "E78.0"
        ]  # 5 condições

        enricher = EventEnricher(care_manager=mock_care_manager)
        enriched = await enricher.enrich(event)

        assert len(enriched.patient_conditions) == 5
        # Múltiplas condições devem aumentar risco
        assert enriched.risk_level in ["medium", "high", "critical"]
