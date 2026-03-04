"""Bot context store — persists per-user conversation context in Redis (EF-W012)."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_KEY_PREFIX = "wanda:bot:context"
_DEFAULT_TTL = 1800  # 30 minutes


class BotContextStore:
    """Stores and retrieves bot conversation context per user/channel.

    Key: wanda:bot:context:{user_id}:{channel_id}
    Value: JSON dict with last patient_id, last command, etc.
    Falls back to in-memory dict when Redis is unavailable.
    """

    def __init__(self, redis_client: Optional[Any] = None, ttl_seconds: int = _DEFAULT_TTL) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds
        self._memory: dict[str, dict[str, Any]] = {}

    def _key(self, tenant_id: str, user_id: str, channel_id: str) -> str:
        return f"{_KEY_PREFIX}:{tenant_id}:{user_id}:{channel_id}"

    async def get(self, tenant_id: str, user_id: str, channel_id: str) -> dict[str, Any]:
        key = self._key(tenant_id, user_id, channel_id)
        if self._redis is not None:
            try:
                raw = await self._redis.get(key)
                return json.loads(raw) if raw else {}
            except Exception as exc:
                logger.warning("ContextStore.get Redis error: %s", exc)
        return self._memory.get(key, {})

    async def set(self, tenant_id: str, user_id: str, channel_id: str, data: dict[str, Any]) -> None:
        key = self._key(tenant_id, user_id, channel_id)
        if self._redis is not None:
            try:
                await self._redis.set(key, json.dumps(data), ex=self._ttl)
                return
            except Exception as exc:
                logger.warning("ContextStore.set Redis error: %s", exc)
        self._memory[key] = data

    async def update(self, tenant_id: str, user_id: str, channel_id: str, updates: dict[str, Any]) -> None:
        ctx = await self.get(tenant_id, user_id, channel_id)
        ctx.update(updates)
        await self.set(tenant_id, user_id, channel_id, ctx)

    async def clear(self, tenant_id: str, user_id: str, channel_id: str) -> None:
        key = self._key(tenant_id, user_id, channel_id)
        if self._redis is not None:
            try:
                await self._redis.delete(key)
                return
            except Exception as exc:
                logger.warning("ContextStore.clear Redis error: %s", exc)
        self._memory.pop(key, None)
