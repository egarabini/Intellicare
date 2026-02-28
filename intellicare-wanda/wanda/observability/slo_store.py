"""Persistent store adapters for SLO history snapshots."""

from __future__ import annotations

import json
from typing import Optional


class InMemorySLOHistoryStore:
    def __init__(self, max_items: int = 200) -> None:
        self._max_items = max(10, int(max_items))
        self._items: list[dict[str, object]] = []

    def append(self, snapshot: dict[str, object]) -> None:
        self._items.append(snapshot)
        self._items = self._items[-self._max_items :]

    def list(self, limit: int = 50) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, self._max_items))
        return self._items[-safe_limit:]


class RedisSLOHistoryStore:
    def __init__(self, redis_client, key: str = "wanda:metrics:slo_history", max_items: int = 200) -> None:
        self._redis = redis_client
        self._key = key
        self._max_items = max(10, int(max_items))

    def append(self, snapshot: dict[str, object]) -> None:
        try:
            payload = json.dumps(snapshot)
            self._redis.rpush(self._key, payload)
            self._redis.ltrim(self._key, -self._max_items, -1)
        except Exception:
            return

    def list(self, limit: int = 50) -> list[dict[str, object]]:
        safe_limit = max(1, min(limit, self._max_items))
        try:
            items = self._redis.lrange(self._key, -safe_limit, -1)
            parsed: list[dict[str, object]] = []
            for raw in items:
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                parsed.append(json.loads(str(raw)))
            return parsed
        except Exception:
            return []

