"""Normalizador de eventos de múltiplas fontes."""

import logging
from typing import Any, Optional

from geralda.events.event_types import IntelliCareEvent, EventType


logger = logging.getLogger(__name__)


class EventNormalizer:
    """
    Converte eventos de diversas fontes para formato IntelliCareEvent.

    Suporta:
    - Eventos FHIR (de Grahame)
    - Eventos de agentes (Oswaldo, Florence)
    - Eventos internos da própria Geralda
    """

    async def normalize_fhir_event(
        self,
        fhir_resource: dict[str, Any],
        source: str = "grahame",
    ) -> IntelliCareEvent:
        """
        Converte recurso FHIR em evento IntelliCare.

        Args:
            fhir_resource: Recurso FHIR (Encounter, Condition, MedicationRequest, etc.)
            source: Origem do evento

        Returns:
            IntelliCareEvent normalizado
        """
        resource_type = fhir_resource.get("resourceType", "")
        patient_ref = fhir_resource.get("subject", {}).get("reference", "")
        patient_id = patient_ref.split("/")[-1] if "/" in patient_ref else patient_ref

        # Mapeamento de tipos FHIR → IntelliCare
        fhir_to_intellicare = {
            "Encounter": {
                "finished": EventType.DISCHARGE,
                "in-progress": EventType.ADMISSION,
            },
            "Condition": {
                "active": EventType.CONDITION_DIAGNOSED,
            },
            "MedicationRequest": {
                "active": EventType.MEDICATION_CHANGED,
            },
            "Observation": {
                "final": EventType.EXAM_RESULT,
            },
        }

        # Determinar tipo de evento
        event_type = EventType.EXAM_RESULT  # Default
        status = fhir_resource.get("status", "")
        clinical_status = (
            fhir_resource.get("clinicalStatus", {})
            .get("coding", [{}])[0]
            .get("code", "")
        )

        if resource_type in fhir_to_intellicare:
            status_map = fhir_to_intellicare[resource_type]
            event_type = status_map.get(status, status_map.get(clinical_status, event_type))

        if resource_type == "Condition" and event_type == EventType.EXAM_RESULT:
            event_type = EventType.CONDITION_DIAGNOSED
        if resource_type == "Encounter" and event_type == EventType.EXAM_RESULT:
            event_type = EventType.ADMISSION

        # Payload específico do recurso
        payload = {
            "resource_type": resource_type,
            "fhir_id": fhir_resource.get("id"),
            "status": status,
        }

        # Extrair dados específicos por tipo
        if resource_type == "Condition":
            code = fhir_resource.get("code", {})
            payload["condition_code"] = code.get("coding", [{}])[0].get("code", "")
            payload["condition_name"] = code.get("text", code.get("coding", [{}])[0].get("display", ""))

        elif resource_type == "Observation":
            code = fhir_resource.get("code", {})
            payload["exam_code"] = code.get("coding", [{}])[0].get("code", "")
            payload["exam_name"] = code.get("text", code.get("coding", [{}])[0].get("display", ""))
            payload["value_quantity"] = fhir_resource.get("valueQuantity", {})
            payload["reference_range"] = fhir_resource.get("referenceRange", [{}])[0]

        return IntelliCareEvent(
            event_type=event_type,
            patient_id=patient_id,
            payload=payload,
            source=source,
            metadata={"original_format": "fhir"},
        )

    async def normalize_agent_event(
        self,
        agent: str,
        event_data: dict[str, Any],
    ) -> IntelliCareEvent:
        """
        Converte evento de outro agente (Oswaldo, Florence) em evento IntelliCare.

        Args:
            agent: Nome do agente ("oswaldo", "florence")
            event_data: Dados do evento

        Returns:
            IntelliCareEvent normalizado
        """
        # Extrair dados comuns
        patient_id = event_data.get("patient_id", "")
        raw_event_type = event_data.get("event_type", "")
        payload = event_data.get("payload") or event_data.get("data", {})

        if agent == "oswaldo" and raw_event_type == "condition_detected":
            event_type = EventType.CONDITION_DIAGNOSED
        elif agent == "florence" and raw_event_type == "lab_result":
            event_type = EventType.EXAM_RESULT
        elif raw_event_type in (
            EventType.CONDITION_WORSENED,
            EventType.CONDITION_IMPROVED,
            EventType.VITAL_SIGN_ALERT,
        ):
            event_type = raw_event_type
        else:
            logger.warning(f"Unknown agent event type: {raw_event_type}")
            event_type = EventType.VITAL_SIGN_ALERT

        return IntelliCareEvent(
            event_type=event_type,
            patient_id=patient_id,
            payload=payload,
            source=agent,
            metadata={"original_format": "agent"},
        )

    async def normalize_internal_event(
        self,
        event_data: dict[str, Any],
    ) -> IntelliCareEvent:
        """
        Normaliza evento interno da própria Geralda.

        Args:
            event_data: Dados do evento interno

        Returns:
            IntelliCareEvent normalizado
        """
        patient_id = event_data.get("patient_id") or ""
        event_type = event_data.get("event_type", "operational.unknown")
        payload = event_data.get("payload")
        if payload is None:
            payload = {k: v for k, v in event_data.items() if k not in {"event_type", "patient_id", "timestamp", "source", "format"}}

        return IntelliCareEvent(
            event_type=event_type,
            patient_id=patient_id,
            payload=payload,
            source="geralda",
            metadata={"original_format": "internal"},
        )

    async def normalize(
        self,
        raw_event: dict[str, Any],
        source: str = "unknown",
    ) -> IntelliCareEvent:
        """
        Normaliza evento detectando automaticamente o formato.

        Args:
            raw_event: Evento bruto
            source: Origem do evento

        Returns:
            IntelliCareEvent normalizado
        """
        # Detectar formato
        format_hint = raw_event.get("format", "")

        if format_hint == "fhir" or raw_event.get("resourceType"):
            return await self.normalize_fhir_event(raw_event, source)

        elif source in ("oswaldo", "florence", "zilda"):
            return await self.normalize_agent_event(source, raw_event)

        elif source == "geralda" or format_hint == "internal":
            return await self.normalize_internal_event(raw_event)

        else:
            # Default: tratar como interno
            return await self.normalize_internal_event(raw_event)
