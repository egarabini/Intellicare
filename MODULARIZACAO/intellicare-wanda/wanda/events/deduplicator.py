"""Event deduplicator — prevents double-processing the same Redis Stream event (EF-W006)."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Optional

from wanda.events.models import IntelliCareEvent

logger = logging.getLogger(__name__)

_EVENT_DEDUP_TTL = timedelta(hours=1)


class EventDeduplicator:
    """Redis-backed event deduplication using event_id as key.

    Falls back to in-memory set when Redis is unavailable.
    """

    def __init__(self, redis_client: Optional[Any] = None) -> None:
        self._redis = redis_client
        self._seen: set[str] = set()

    def _key(self, event: IntelliCareEvent) -> str:
        return f"wanda:event:dedup:{event.event_id}"

    async def is_duplicate(self, event: IntelliCareEvent) -> bool:
        key = self._key(event)
        if self._redis is not None:
            try:
                return bool(await self._redis.exists(key))
            except Exception as exc:
                logger.warning("Redis event dedup check failed: %s — using memory", exc)
        return key in self._seen

    async def mark_processed(self, event: IntelliCareEvent) -> None:
        key = self._key(event)
        ttl = int(_EVENT_DEDUP_TTL.total_seconds())
        if self._redis is not None:
            try:
                await self._redis.set(key, "1", ex=ttl)
                return
            except Exception as exc:
                logger.warning("Redis event dedup mark failed: %s — using memory", exc)
        self._seen.add(key)
