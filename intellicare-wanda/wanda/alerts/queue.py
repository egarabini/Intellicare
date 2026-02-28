"""Alert queue — manages pending/acknowledged/resolved state (EF-W007)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AlertQueue:
    """In-process alert queue backed by SQLAlchemy (via AlertStore).

    Provides semantics: get_pending → acknowledge → resolve.
    Works without DB (memory-only mode) when no db session is provided.
    """

    def __init__(self, db_session_factory: Optional[Any] = None) -> None:
        self._db_factory = db_session_factory
        # In-memory fallback: {alert_id: status_dict}
        self._memory: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Add
    # ------------------------------------------------------------------

    def enqueue(
        self,
        alert_id: str,
        patient_id: str,
        severity: str,
        priority_score: int,
        title: str,
        source_agent: str,
        alert_type: str,
    ) -> None:
        """Add an alert to the in-memory queue (DB persistence via AlertStore/hub)."""
        self._memory[alert_id] = {
            "alert_id": alert_id,
            "patient_id": patient_id,
            "severity": severity,
            "priority_score": priority_score,
            "title": title,
            "source_agent": source_agent,
            "alert_type": alert_type,
            "status": "pending",
            "acknowledged_by": None,
            "resolved_by": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.debug("Queued alert %s (score=%d)", alert_id, priority_score)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_pending(
        self,
        limit: int = 50,
        patient_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Return pending alerts sorted by priority_score descending."""
        pending = [
            v for v in self._memory.values()
            if v["status"] == "pending"
            and (patient_id is None or v["patient_id"] == patient_id)
        ]
        return sorted(pending, key=lambda x: x["priority_score"], reverse=True)[:limit]

    def get_by_patient(self, patient_id: str) -> list[dict[str, Any]]:
        return [v for v in self._memory.values() if v["patient_id"] == patient_id]

    def get_alert(self, alert_id: str) -> Optional[dict[str, Any]]:
        return self._memory.get(alert_id)

    def get_stats(self) -> dict[str, int]:
        counts: dict[str, int] = {"pending": 0, "acknowledged": 0, "resolved": 0}
        for v in self._memory.values():
            s = v.get("status", "pending")
            counts[s] = counts.get(s, 0) + 1
        return counts

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def acknowledge(self, alert_id: str, acknowledged_by: str) -> bool:
        """Mark alert as acknowledged. Returns False if not found."""
        if alert_id not in self._memory:
            return False
        self._memory[alert_id]["status"] = "acknowledged"
        self._memory[alert_id]["acknowledged_by"] = acknowledged_by
        logger.info("Alert %s acknowledged by %s", alert_id, acknowledged_by)
        return True

    def resolve(
        self, alert_id: str, resolved_by: str, resolution_notes: str = ""
    ) -> bool:
        """Mark alert as resolved. Returns False if not found."""
        if alert_id not in self._memory:
            return False
        self._memory[alert_id]["status"] = "resolved"
        self._memory[alert_id]["resolved_by"] = resolved_by
        self._memory[alert_id]["resolution_notes"] = resolution_notes
        logger.info("Alert %s resolved by %s", alert_id, resolved_by)
        return True

    def expire(self, alert_id: str) -> bool:
        if alert_id not in self._memory:
            return False
        self._memory[alert_id]["status"] = "expired"
        return True
