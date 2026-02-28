"""Alert deduplicator — prevents repeated alerts for the same event (EF-W007)."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Optional

from wanda.alerts.models import ClinicalAlert

logger = logging.getLogger(__name__)

# Time window per alert type in which identical alerts are suppressed
DEDUP_WINDOWS: dict[str, timedelta] = {
    "vital_sign": timedelta(minutes=10),
    "lab_result": timedelta(hours=1),
    "condition_worsened": timedelta(hours=4),
    "adherence_low": timedelta(hours=24),
    "medication_missed": timedelta(hours=12),
}

_DEFAULT_WINDOW = timedelta(hours=1)


class AlertDeduplicator:
    """Redis-backed alert deduplication.

    Uses the alert's idempotency_key as the Redis key.
    Falls back to an in-memory set if Redis is unavailable.
    """

    def __init__(self, redis_client: Any = None) -> None:
        self._redis: Optional[Any] = redis_client
        self._seen: set[str] = set()  # in-memory fallback

    def _window_seconds(self, alert_type: str) -> int:
        return int(DEDUP_WINDOWS.get(alert_type, _DEFAULT_WINDOW).total_seconds())

    def _redis_key(self, alert: ClinicalAlert) -> str:
        return f"wanda:alert:dedup:{alert.idempotency_key}"

    async def is_duplicate(self, alert: ClinicalAlert) -> bool:
        """Return True if this alert was already processed within the dedup window."""
        key = self._redis_key(alert)

        if self._redis is not None:
            try:
                exists = await self._redis.exists(key)
                return bool(exists)
            except Exception as e:
                logger.warning("Redis dedup check failed: %s — using memory", e)

        return key in self._seen

    async def mark_processed(self, alert: ClinicalAlert) -> None:
        """Record the alert so future duplicates are suppressed."""
        key = self._redis_key(alert)
        ttl = self._window_seconds(alert.alert_type)

        if self._redis is not None:
            try:
                await self._redis.set(key, "1", ex=ttl)
                return
            except Exception as e:
                logger.warning("Redis dedup mark failed: %s — using memory", e)

        self._seen.add(key)
