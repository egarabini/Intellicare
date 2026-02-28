"""Event coordinator — maps event types to agent notifications and workflows (EF-W006)."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from wanda.events.deduplicator import EventDeduplicator
from wanda.events.models import (
    CoordinationResult,
    EventCoordinationStatus,
    IntelliCareEvent,
)

logger = logging.getLogger(__name__)

# Maps event_type → {agents to notify, optional workflow to trigger}
EVENT_COORDINATION_MAP: dict[str, dict[str, Any]] = {
    "lab_result_critical": {
        "agents": ["intellicare-florence", "intellicare-oswaldo"],
        "workflow": "critical_alert",
        "alert_severity": "critical",
    },
    "vital_sign_alert": {
        "agents": ["intellicare-florence"],
        "workflow": "clinical_analysis",
        "alert_severity": "high",
    },
    "adherence_missed": {
        "agents": ["intellicare-geralda", "intellicare-oswaldo"],
        "workflow": None,
        "alert_severity": "medium",
    },
    "condition_worsened": {
        "agents": ["intellicare-florence", "intellicare-oswaldo", "intellicare-geralda"],
        "workflow": "critical_alert",
        "alert_severity": "high",
    },
    "medication_schedule": {
        "agents": ["intellicare-geralda"],
        "workflow": None,
        "alert_severity": "low",
    },
    "appointment_reminder": {
        "agents": ["intellicare-geralda"],
        "workflow": None,
        "alert_severity": "low",
    },
}


class EventCoordinator:
    """Coordinates IntelliCare events: dedup → notify agents → trigger workflow.

    Module URLs are resolved from the module_registry at runtime.
    """

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        http_client: Optional[Any] = None,
        alert_hub: Optional[Any] = None,
        workflow_executor: Optional[Any] = None,
    ) -> None:
        self._deduplicator = EventDeduplicator(redis_client)
        self._http = http_client
        self._alert_hub = alert_hub
        self._workflow_executor = workflow_executor
        self._module_urls: dict[str, str] = {}

    def update_module_urls(self, urls: dict[str, str]) -> None:
        self._module_urls = urls

    async def coordinate(self, event: IntelliCareEvent) -> CoordinationResult:
        """Full coordination pipeline for one event."""
        start = time.monotonic()

        if await self._deduplicator.is_duplicate(event):
            logger.debug("Event %s is duplicate — skipped", event.event_id)
            return CoordinationResult(
                event_id=event.event_id,
                event_type=event.event_type,
                status=EventCoordinationStatus.SKIPPED,
                coordination_time_ms=0,
            )

        mapping = EVENT_COORDINATION_MAP.get(event.event_type)
        if mapping is None:
            logger.info("Unknown event type: %s", event.event_type)
            await self._deduplicator.mark_processed(event)
            return CoordinationResult(
                event_id=event.event_id,
                event_type=event.event_type,
                status=EventCoordinationStatus.SKIPPED,
                error=f"Tipo de evento desconhecido: {event.event_type}",
            )

        notified: list[str] = []
        failed: list[str] = []
        workflow_triggered: Optional[str] = None

        # 1. Notify agents via AlertHub
        if self._alert_hub is not None and mapping.get("alert_severity"):
            try:
                from wanda.alerts.models import ClinicalAlert  # noqa: PLC0415

                alert = ClinicalAlert(
                    patient_id=event.patient_id,
                    source_agent=event.source_module,
                    alert_type=event.event_type,
                    severity=mapping["alert_severity"],
                    title=f"Evento: {event.event_type} ({event.source_module})",
                    clinical_data=event.payload,
                )
                await self._alert_hub.receive_alert(alert)
                notified.extend(mapping.get("agents", []))
            except Exception as exc:
                logger.error("AlertHub notification failed for event %s: %s", event.event_id, exc)
                failed.extend(mapping.get("agents", []))
        else:
            # Fallback: direct HTTP notification
            notified, failed = await self._broadcast_event(event, mapping.get("agents", []))

        # 2. Trigger workflow if applicable
        wf_name = mapping.get("workflow")
        if wf_name and self._workflow_executor is not None:
            try:
                result = await self._workflow_executor.execute(
                    workflow_name=wf_name,
                    query=f"Evento {event.event_type} para paciente {event.patient_id}",
                    patient_id=event.patient_id,
                    extra={"event": event.payload},
                )
                workflow_triggered = wf_name if result.success else None
            except Exception as exc:
                logger.error("Workflow %s failed for event %s: %s", wf_name, event.event_id, exc)

        await self._deduplicator.mark_processed(event)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        status = (
            EventCoordinationStatus.SUCCESS
            if not failed
            else (EventCoordinationStatus.PARTIAL if notified else EventCoordinationStatus.FAILED)
        )
        return CoordinationResult(
            event_id=event.event_id,
            event_type=event.event_type,
            status=status,
            agents_notified=notified,
            agents_failed=failed,
            workflow_triggered=workflow_triggered,
            coordination_time_ms=elapsed_ms,
        )

    async def _broadcast_event(
        self, event: IntelliCareEvent, agents: list[str]
    ) -> tuple[list[str], list[str]]:
        """Send event payload to agent HTTP endpoints."""
        notified: list[str] = []
        failed: list[str] = []

        if self._http is None:
            return notified, agents  # all failed without HTTP client

        import asyncio  # noqa: PLC0415

        async def _notify(agent: str) -> None:
            url = self._module_urls.get(agent)
            if not url:
                failed.append(agent)
                return
            try:
                resp = await self._http.post(
                    f"{url}/api/v1/events/receive",
                    json={
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "patient_id": event.patient_id,
                        "source_module": event.source_module,
                        "payload": event.payload,
                        "priority": event.priority,
                    },
                    timeout=5.0,
                )
                if resp.status_code < 300:
                    notified.append(agent)
                else:
                    failed.append(agent)
            except Exception as exc:
                logger.warning("Failed to notify %s: %s", agent, exc)
                failed.append(agent)

        await asyncio.gather(*[_notify(a) for a in agents])
        return notified, failed
