"""Scheduler atrasado para timeouts e tarefas do roteador."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DelayedTask:
    run_at: datetime
    payload: dict[str, Any]


class DelayedScheduler(Protocol):
    async def enqueue(self, task: DelayedTask) -> None: ...

    async def pop_due(self, now: datetime) -> list[DelayedTask]: ...


class InMemoryDelayedScheduler:
    def __init__(self) -> None:
        self._items: list[DelayedTask] = []
        self._lock = asyncio.Lock()

    async def enqueue(self, task: DelayedTask) -> None:
        async with self._lock:
            self._items.append(task)
            self._items.sort(key=lambda item: item.run_at)

    async def pop_due(self, now: datetime) -> list[DelayedTask]:
        async with self._lock:
            due = [item for item in self._items if item.run_at <= now]
            self._items = [item for item in self._items if item.run_at > now]
            return due


class RedisDelayedScheduler:
    def __init__(self, redis_url: str, queue_key: str) -> None:
        self._redis_url = redis_url
        self._queue_key = queue_key

    async def enqueue(self, task: DelayedTask) -> None:
        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise RuntimeError("redis nao instalado")
        redis = aioredis.from_url(self._redis_url, decode_responses=True)
        payload = json.dumps(
            {"run_at": task.run_at.isoformat(), "payload": task.payload},
            ensure_ascii=True,
            sort_keys=True,
        )
        try:
            await redis.zadd(self._queue_key, {payload: task.run_at.timestamp()})
        finally:
            await redis.close()

    async def pop_due(self, now: datetime) -> list[DelayedTask]:
        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise RuntimeError("redis nao instalado")
        redis = aioredis.from_url(self._redis_url, decode_responses=True)
        try:
            raw = await redis.zrangebyscore(self._queue_key, min=0, max=now.timestamp())
            if not raw:
                return []
            tasks: list[DelayedTask] = []
            for item in raw:
                parsed = json.loads(item)
                tasks.append(
                    DelayedTask(
                        run_at=datetime.fromisoformat(parsed["run_at"]).astimezone(UTC),
                        payload=parsed["payload"],
                    )
                )
            if raw:
                await redis.zrem(self._queue_key, *raw)
            return tasks
        finally:
            await redis.close()


class DelayedWorker:
    def __init__(
        self,
        scheduler: DelayedScheduler,
        on_task: Callable[[DelayedTask], Awaitable[None]],
        poll_seconds: int = 5,
    ) -> None:
        self._scheduler = scheduler
        self._on_task = on_task
        self._poll_seconds = max(1, poll_seconds)
        self._task: asyncio.Task[None] | None = None

    def status(self) -> dict[str, Any]:
        running = self._task is not None and not self._task.done()
        return {"ok": True, "running": running, "poll_seconds": self._poll_seconds}

    async def start(self) -> dict[str, Any]:
        if self._task is not None and not self._task.done():
            return {"ok": True, "running": True, "already_running": True}
        self._task = asyncio.create_task(self._run(), name="routing-delayed-worker")
        return {"ok": True, "running": True}

    async def stop(self) -> dict[str, Any]:
        if self._task is None or self._task.done():
            self._task = None
            return {"ok": True, "running": False}
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
        return {"ok": True, "running": False}

    async def process_due_once(self) -> int:
        due = await self._scheduler.pop_due(datetime.now(UTC))
        for task in due:
            try:
                await self._on_task(task)
            except Exception as exc:  # pragma: no cover
                logger.warning("Falha ao processar delayed task: %s", exc)
        return len(due)

    async def _run(self) -> None:
        while True:
            await self.process_due_once()
            await asyncio.sleep(self._poll_seconds)

