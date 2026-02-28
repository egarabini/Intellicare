"""Alert escalator — background task that re-notifies when alerts go unacknowledged (EF-W007)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)

# Time until unacknowledged alert triggers escalation
_ESCALATION_DELAYS: dict[str, timedelta] = {
    "critical": timedelta(minutes=5),
    "high": timedelta(minutes=15),
    "medium": timedelta(hours=2),
    "low": timedelta(hours=24),
}


class AlertEscalator:
    """Schedules and fires escalation callbacks for unacknowledged alerts.

    Usage:
        escalator = AlertEscalator(check_interval=60)
        escalator.schedule(alert, on_escalate_callback)
        await escalator.start()          # runs in background
        await escalator.stop()
    """

    EscalationCallback = Callable[[str, str], Coroutine[Any, Any, None]]

    def __init__(self, check_interval_seconds: int = 60) -> None:
        self._check_interval = check_interval_seconds
        # {alert_id: (severity, escalate_at, callback, escalated)}
        self._scheduled: dict[str, tuple[str, datetime, "AlertEscalator.EscalationCallback", bool]] = {}
        self._task: Optional[asyncio.Task[None]] = None
        self._running = False

    def schedule(
        self,
        alert_id: str,
        severity: str,
        callback: "AlertEscalator.EscalationCallback",
    ) -> datetime:
        """Register an alert for escalation. Returns the escalation datetime."""
        delay = _ESCALATION_DELAYS.get(severity, timedelta(hours=2))
        escalate_at = datetime.now(timezone.utc) + delay
        self._scheduled[alert_id] = (severity, escalate_at, callback, False)
        logger.debug("Escalation scheduled for alert %s at %s", alert_id, escalate_at.isoformat())
        return escalate_at

    def cancel(self, alert_id: str) -> None:
        """Cancel escalation (alert was acknowledged or resolved)."""
        if alert_id in self._scheduled:
            del self._scheduled[alert_id]
            logger.debug("Escalation cancelled for alert %s", alert_id)

    async def start(self) -> None:
        """Start background escalation checker."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AlertEscalator started (check_interval=%ds)", self._check_interval)

    async def stop(self) -> None:
        """Stop background checker gracefully."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AlertEscalator stopped")

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._check_escalations()
            except Exception as exc:
                logger.exception("Escalation check error: %s", exc)
            await asyncio.sleep(self._check_interval)

    async def _check_escalations(self) -> None:
        now = datetime.now(timezone.utc)
        to_escalate = [
            (aid, sev, escalate_at, cb)
            for aid, (sev, escalate_at, cb, done) in list(self._scheduled.items())
            if not done and now >= escalate_at
        ]
        for alert_id, severity, _, callback in to_escalate:
            try:
                logger.warning("Escalating unacknowledged %s alert %s", severity, alert_id)
                await callback(alert_id, severity)
                # Mark escalated — keep entry so it won't fire again
                sev, at, cb, _ = self._scheduled[alert_id]
                self._scheduled[alert_id] = (sev, at, cb, True)
            except Exception as exc:
                logger.error("Escalation callback failed for alert %s: %s", alert_id, exc)

    @property
    def pending_count(self) -> int:
        return sum(1 for _, _, _, done in self._scheduled.values() if not done)
