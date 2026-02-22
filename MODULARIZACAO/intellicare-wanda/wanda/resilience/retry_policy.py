"""Retry policy com backoff exponencial e jitter leve."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int
    initial_delay: float
    max_delay: float
    backoff_factor: float = 2.0


class RetryPolicy:
    def __init__(self) -> None:
        self._policies: dict[str, RetryConfig] = {
            "default": RetryConfig(max_attempts=3, initial_delay=0.5, max_delay=5.0),
            "critical": RetryConfig(max_attempts=5, initial_delay=0.2, max_delay=3.0, backoff_factor=1.5),
            "health_check": RetryConfig(max_attempts=2, initial_delay=1.0, max_delay=2.0),
        }

    async def execute_with_retry(self, coro_factory, policy_name: str = "default") -> Any:
        config = self._policies.get(policy_name, self._policies["default"])
        delay = config.initial_delay
        last_error: Exception | None = None
        for attempt in range(1, config.max_attempts + 1):
            try:
                return await coro_factory()
            except Exception as exc:
                last_error = exc
                if attempt >= config.max_attempts:
                    break
                jitter_factor = 1.0 + random.uniform(0.0, 0.2)
                await asyncio.sleep(min(config.max_delay, delay) * jitter_factor)
                delay = min(config.max_delay, delay * config.backoff_factor)
        if last_error:
            raise last_error
        raise RuntimeError("retry_policy_failed_without_exception")
