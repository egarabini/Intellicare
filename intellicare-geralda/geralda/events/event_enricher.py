"""Enriquecedor de eventos com dados do paciente."""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from geralda.events.event_types import IntelliCareEvent


logger = logging.getLogger(__name__)


@dataclass
class EnrichedEvent:
    """Evento enriquecido com dados do paciente."""

    original_event: IntelliCareEvent
    patient_id: str
    patient_conditions: list[Any] = field(default_factory=list)
    active_plans: list[Any] = field(default_factory=list)
    journey_stage: str = "unknown"  # E0-E7
    risk_level: str = "unknown"  # low, medium, high, critical
    preferences: dict[str, Any] = field(default_factory=dict)
    recent_events: list[dict] = field(default_factory=list)

    @property
    def original(self) -> IntelliCareEvent:
        """Compatibilidade retroativa com atributo antigo."""
        return self.original_event

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "patient_conditions": self.patient_conditions,
            "active_plans": self.active_plans,
            "journey_stage": self.journey_stage,
            "risk_level": self.risk_level,
            "preferences": self.preferences,
            "recent_events": self.recent_events,
        }


class EventEnricher:
    """
    Enriquece eventos com dados do paciente (camada Model do MCP).

    Adiciona contexto clínico, planos ativos, estágio da jornada,
    nível de risco e preferências do paciente.
    """

    def __init__(
        self,
        db_session_factory=None,
        care_manager: Optional[Any] = None,
        fhir_client: Optional[Any] = None,
    ):
        """
        Inicializa enriquecedor.

        Args:
            db_session_factory: Factory de sessões do banco
            fhir_client: Cliente FHIR opcional (Grahame)
        """
        self._session_factory = db_session_factory
        self._care_manager = care_manager
        self._fhir_client = fhir_client

    async def enrich(self, event: IntelliCareEvent) -> EnrichedEvent:
        """
        Enriquece evento com dados do paciente.

        Args:
            event: Evento a enriquecer

        Returns:
            Evento enriquecido com contexto do paciente
        """
        enriched = EnrichedEvent(original_event=event, patient_id=event.patient_id or "")

        if self._care_manager is not None:
            try:
                conditions = await self._care_manager.get_patient_conditions(event.patient_id)
                plans = await self._care_manager.get_patient_plans(event.patient_id)
                enriched.patient_conditions = conditions or []
                enriched.active_plans = [getattr(p, "id", p) for p in (plans or [])]
            except Exception as e:
                logger.error(f"Error enriching with care_manager: {e}")
        elif self._session_factory is not None:
            # Modo DB é opcional nesta fase; mantém fallback seguro.
            enriched.patient_conditions = []
            enriched.active_plans = []

        # Determinar estágio da jornada
        enriched.journey_stage = self._determine_journey_stage(enriched, event)

        # Calcular nível de risco
        enriched.risk_level = self._calculate_risk_level(enriched, event)

        # Preferências padrão
        enriched.preferences = {
            "reading_level": "basico",
            "preferred_language": "pt-BR",
            "preferred_channel": "app",
        }

        # Enriquecer com FHIR se disponível
        if self._fhir_client:
            enriched.recent_events = await self._get_recent_fhir_events(event.patient_id)

        return enriched

    def _determine_journey_stage(self, enriched: EnrichedEvent, event: IntelliCareEvent) -> str:
        """
        Determina estágio da jornada do paciente (E0-E7).

        Baseado em número de condições e planos ativos.
        """
        num_conditions = len(enriched.patient_conditions)
        num_plans = len(enriched.active_plans)

        if num_plans == 0:
            return "E0"  # Sem plano
        if event.event_type == "care.plan_created":
            return "E1"  # Condição única, cuidado básico
        if event.event_type.startswith("care.task_"):
            return "E3"
        if num_conditions >= 3:
            return "E4"
        return "E2"

    def _calculate_risk_level(self, enriched: EnrichedEvent, event: IntelliCareEvent) -> str:
        """
        Calcula nível de risco do paciente.

        Baseado em condições e adesão (simplificado).
        """
        num_conditions = len(enriched.patient_conditions)

        if event.event_type == "clinical.condition_worsened":
            severity = str(event.payload.get("severity", "")).lower()
            if severity in {"severe", "critical"}:
                return "critical"
            return "high"
        if num_conditions == 0:
            return "low"
        if num_conditions == 1:
            return "medium"
        if num_conditions == 2:
            return "high"
        return "critical"

    async def _get_recent_fhir_events(
        self,
        patient_id: str,
        limit: int = 10,
    ) -> list[dict]:
        """Busca eventos FHIR recentes."""
        # TODO: Implementar busca em tabela journey_events
        return []
