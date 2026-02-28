"""AlertHub — central orchestrator for clinical alert coordination (EF-W007)."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Coroutine, Optional

from wanda.alerts.consolidator import AlertConsolidator
from wanda.alerts.deduplicator import AlertDeduplicator
from wanda.alerts.escalator import AlertEscalator
from wanda.alerts.models import AlertProcessingResult, ClinicalAlert
from wanda.alerts.prioritizer import AlertPrioritizer
from wanda.alerts.queue import AlertQueue
from wanda.alerts.store import AlertStore

logger = logging.getLogger(__name__)

DispatchCallback = Callable[[ClinicalAlert, int], Coroutine[Any, Any, None]]


class AlertHub:
    """Orchestrates the full alert pipeline:

    receive_alert() → dedup → prioritize → consolidate → dispatch → schedule_escalation

    All steps are optional/graceful:
    - No Redis → in-memory dedup
    - No DB → in-memory queue
    - No dispatch_callback → log-only
    """

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        session_factory: Optional[Any] = None,
        consolidation_window_seconds: int = 300,
        escalation_check_interval_seconds: int = 60,
        dispatch_callback: Optional[DispatchCallback] = None,
        metrics_registry: Optional[Any] = None,
    ) -> None:
        self._deduplicator = AlertDeduplicator(redis_client)
        self._prioritizer = AlertPrioritizer()
        self._consolidator = AlertConsolidator(consolidation_window_seconds)
        self._escalator = AlertEscalator(escalation_check_interval_seconds)
        self._queue = AlertQueue(session_factory)
        self._store = AlertStore(session_factory)
        self._dispatch = dispatch_callback
        self._metrics = metrics_registry
        self._received_at: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        await self._escalator.start()
        logger.info("AlertHub started")

    async def stop(self) -> None:
        await self._escalator.stop()
        logger.info("AlertHub stopped")

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    async def receive_alert(
        self,
        alert: ClinicalAlert,
        patient_context: Optional[dict[str, Any]] = None,
    ) -> AlertProcessingResult:
        """Process an incoming alert through the full pipeline."""
        self._record_alert_received(alert.source_agent, alert.severity)

        # 1. Deduplication
        if await self._deduplicator.is_duplicate(alert):
            logger.info("Alert %s is duplicate — suppressed", alert.alert_id)
            return AlertProcessingResult(
                alert_id=alert.alert_id,
                status="deduplicated",
                message="Alerta duplicado suprimido dentro da janela de deduplicacao",
            )

        # 2. Priority calculation
        priority = await self._prioritizer.calculate_priority(alert, patient_context)

        # Update severity if escalated by context
        if priority.adjusted_severity != alert.severity:
            alert = ClinicalAlert(
                patient_id=alert.patient_id,
                source_agent=alert.source_agent,
                alert_type=alert.alert_type,
                severity=priority.adjusted_severity,
                title=alert.title,
                description=alert.description,
                recommended_action=alert.recommended_action,
                clinical_data=alert.clinical_data,
                idempotency_key=alert.idempotency_key,
                alert_id=alert.alert_id,
                timestamp=alert.timestamp,
            )

        # 3. Consolidation
        consolidated = self._consolidator.try_consolidate(alert)
        if consolidated is not None:
            logger.info(
                "Alert %s consolidated with %d others under %s",
                alert.alert_id, len(consolidated.merged_ids), consolidated.primary_alert.alert_id,
            )
            return AlertProcessingResult(
                alert_id=alert.alert_id,
                status="consolidated",
                priority_score=priority.score,
                message=f"Consolidado com alerta principal {consolidated.primary_alert.alert_id}",
            )

        # 4. Enqueue (memory)
        self._queue.enqueue(
            alert_id=alert.alert_id,
            patient_id=alert.patient_id,
            severity=alert.severity,
            priority_score=priority.score,
            title=alert.title,
            source_agent=alert.source_agent,
            alert_type=alert.alert_type,
        )
        self._received_at[alert.alert_id] = time.monotonic()
        self._refresh_pending_metrics()

        # 5. Persist to DB
        await self._store.save_alert({
            "alert_id": alert.alert_id,
            "patient_id": alert.patient_id,
            "source_agent": alert.source_agent,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "adjusted_severity": priority.adjusted_severity,
            "title": alert.title,
            "description": alert.description,
            "recommended_action": alert.recommended_action,
            "clinical_data": alert.clinical_data,
            "priority_score": priority.score,
            "idempotency_key": alert.idempotency_key,
        })

        # 6. Mark as processed in dedup store
        await self._deduplicator.mark_processed(alert)

        # 7. Dispatch notification
        if self._dispatch is not None:
            try:
                await self._dispatch(alert, priority.score)
            except Exception as exc:
                logger.error("Dispatch callback failed for alert %s: %s", alert.alert_id, exc)

        # 8. Schedule escalation
        self._escalator.schedule(
            alert_id=alert.alert_id,
            severity=alert.severity,
            callback=self._escalation_callback,
        )

        logger.info(
            "Alert %s accepted: score=%d severity=%s factors=%s",
            alert.alert_id, priority.score, priority.adjusted_severity, priority.factors,
        )
        return AlertProcessingResult(
            alert_id=alert.alert_id,
            status="accepted",
            priority_score=priority.score,
            message=f"Alerta aceito com score {priority.score} ({priority.adjusted_severity})",
        )

    async def _escalation_callback(self, alert_id: str, severity: str) -> None:
        logger.warning(
            "ESCALATION: alert %s (%s) not acknowledged within SLA", alert_id, severity
        )
        # In a full system this would re-dispatch or notify a supervisor
        self._record_alert_escalated(severity)

    # ------------------------------------------------------------------
    # Queue operations (exposed for API routes)
    # ------------------------------------------------------------------

    def get_pending_alerts(
        self, limit: int = 50, patient_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        return self._queue.get_pending(limit=limit, patient_id=patient_id)

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        alert = self._queue.get_alert(alert_id)
        ok = self._queue.acknowledge(alert_id, acknowledged_by)
        if ok:
            self._escalator.cancel(alert_id)
            if alert is not None:
                started_at = self._received_at.pop(alert_id, None)
                if started_at is not None:
                    self._record_alert_ack(alert.get("severity", "high"), time.monotonic() - started_at)
            self._refresh_pending_metrics()
        return ok

    def resolve_alert(
        self, alert_id: str, resolved_by: str, notes: str = ""
    ) -> bool:
        ok = self._queue.resolve(alert_id, resolved_by, notes)
        if ok:
            self._escalator.cancel(alert_id)
            self._refresh_pending_metrics()
        return ok

    def get_stats(self) -> dict[str, Any]:
        stats = self._queue.get_stats()
        stats["pending_escalations"] = self._escalator.pending_count
        return stats

    def set_metrics_registry(self, metrics_registry: Optional[Any]) -> None:
        self._metrics = metrics_registry
        self._refresh_pending_metrics()

    def _record_alert_received(self, source_agent: str, severity: str) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.record_alert_received(source_agent=source_agent, severity=severity)
        except Exception:
            return

    def _record_alert_ack(self, severity: str, acknowledgment_seconds: float) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.record_alert_ack(
                severity=severity,
                acknowledgment_seconds=max(0.0, float(acknowledgment_seconds)),
            )
        except Exception:
            return

    def _record_alert_escalated(self, severity: str) -> None:
        if self._metrics is None:
            return
        try:
            self._metrics.record_alert_escalated(severity=severity)
        except Exception:
            return

    def _refresh_pending_metrics(self) -> None:
        if self._metrics is None:
            return
        try:
            pending = self._queue.get_pending(limit=1000)
            counts = {"low": 0.0, "medium": 0.0, "high": 0.0, "critical": 0.0}
            for alert in pending:
                severity = str(alert.get("severity", "low")).lower()
                if severity in counts:
                    counts[severity] += 1.0
            for severity, count in counts.items():
                self._metrics.set_alerts_pending(severity=severity, count=count)
        except Exception:
            return
