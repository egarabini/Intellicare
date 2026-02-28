"""Redis-based checkpoint storage for LangGraph workflows (EF-W005).

Stores workflow state as JSON with configurable TTL.
Falls back to in-memory dict if Redis is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CHECKPOINT_TTL = 3600  # 1 hour


class WorkflowCheckpointer:
    """Saves and restores LangGraph workflow checkpoints in Redis.

    Used for long-running workflows that may need to be resumed
    or inspected after completion.
    """

    def __init__(
        self,
        redis_client: Any = None,
        ttl_seconds: int = _CHECKPOINT_TTL,
    ) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds
        self._memory: dict[str, str] = {}  # in-memory fallback

    def _key(self, execution_id: str) -> str:
        return f"wanda:workflow:checkpoint:{execution_id}"

    async def save(self, execution_id: str, state: dict[str, Any]) -> None:
        """Persist workflow state for the given execution ID."""
        # Strip injected callables before serializing
        safe = {k: v for k, v in state.items() if not k.startswith("_")}
        payload = json.dumps(safe, default=str)

        if self._redis is not None:
            try:
                await self._redis.set(self._key(execution_id), payload, ex=self._ttl)
                return
            except Exception as e:
                logger.warning("Redis checkpoint save failed: %s — using memory", e)

        self._memory[execution_id] = payload

    async def restore(self, execution_id: str) -> Optional[dict[str, Any]]:
        """Restore workflow state for the given execution ID."""
        if self._redis is not None:
            try:
                raw = await self._redis.get(self._key(execution_id))
                if raw:
                    return json.loads(raw)  # type: ignore[no-any-return]
            except Exception as e:
                logger.warning("Redis checkpoint restore failed: %s", e)

        raw_mem = self._memory.get(execution_id)
        if raw_mem:
            return json.loads(raw_mem)  # type: ignore[no-any-return]
        return None

    async def delete(self, execution_id: str) -> None:
        """Remove checkpoint after workflow completes successfully."""
        self._memory.pop(execution_id, None)
        if self._redis is not None:
            try:
                await self._redis.delete(self._key(execution_id))
            except Exception:
                pass
