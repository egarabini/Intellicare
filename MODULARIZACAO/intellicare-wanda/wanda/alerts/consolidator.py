"""Alert consolidator — groups simultaneous alerts into a single entry (EF-W007)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from wanda.alerts.models import ClinicalAlert, ConsolidatedAlert

logger = logging.getLogger(__name__)

_CONSOLIDATION_WINDOW_DEFAULT = timedelta(minutes=5)


class AlertConsolidator:
    """Groups concurrent alerts for the same patient within a time window.

    Only alerts of the same type and severity are merged.
    The first alert received becomes the primary; subsequent ones are listed
    in `merged_ids`.
    """

    def __init__(self, window_seconds: int = 300) -> None:
        self._window = timedelta(seconds=window_seconds)
        # {(patient_id, alert_type, severity): (primary_alert, [merged_ids], window_end)}
        self._buffer: dict[tuple[str, str, str], tuple[ClinicalAlert, list[str], datetime]] = {}

    def _key(self, alert: ClinicalAlert) -> tuple[str, str, str]:
        return (alert.patient_id, alert.alert_type, alert.severity)

    def _purge_expired(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [k for k, (_, _, end) in self._buffer.items() if now > end]
        for k in expired:
            del self._buffer[k]

    def try_consolidate(self, alert: ClinicalAlert) -> Optional[ConsolidatedAlert]:
        """Attempt to consolidate the alert into an existing group.

        Returns `ConsolidatedAlert` if merged, or `None` if this is the primary
        (starts a new consolidation window).
        """
        self._purge_expired()
        key = self._key(alert)
        now = datetime.now(timezone.utc)

        if key in self._buffer:
            primary, merged_ids, window_end = self._buffer[key]
            if now <= window_end:
                merged_ids.append(alert.alert_id)
                logger.debug(
                    "Alert %s consolidated with primary %s (%d merged)",
                    alert.alert_id, primary.alert_id, len(merged_ids),
                )
                return ConsolidatedAlert(primary_alert=primary, merged_ids=list(merged_ids))

        # Start a new consolidation window
        window_end = now + self._window
        self._buffer[key] = (alert, [], window_end)
        logger.debug("Alert %s starts new consolidation window", alert.alert_id)
        return None

    def get_consolidated(self, alert: ClinicalAlert) -> Optional[ConsolidatedAlert]:
        """Return the current consolidation group for this alert type, if any."""
        key = self._key(alert)
        if key not in self._buffer:
            return None
        primary, merged_ids, _ = self._buffer[key]
        if not merged_ids:
            return None
        return ConsolidatedAlert(primary_alert=primary, merged_ids=list(merged_ids))
