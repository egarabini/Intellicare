"""State store adapters for circuit breaker persistence."""

from __future__ import annotations

from typing import Optional


class InMemoryCircuitStateStore:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        return self._data.get(key)

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        _ = ttl_seconds
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class RedisCircuitStateStore:
    def __init__(self, redis_client) -> None:
        self._redis = redis_client

    def get(self, key: str) -> Optional[str]:
        try:
            value = self._redis.get(key)
            if value is None:
                return None
            if isinstance(value, bytes):
                return value.decode("utf-8")
            return str(value)
        except Exception:
            return None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            self._redis.setex(key, max(1, int(ttl_seconds)), value)
        except Exception:
            return

    def delete(self, key: str) -> None:
        try:
            self._redis.delete(key)
        except Exception:
            return
