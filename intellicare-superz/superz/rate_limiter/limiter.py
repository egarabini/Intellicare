"""TavilyRateLimiter — token bucket em memoria."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class TavilyRateLimiter:
    """
    Rate limiter em memoria para Tavily API.
    Usa algoritmo token bucket.

    Padrao: 100 tokens/hora, 1 token por query.
    """

    limit_per_hour: int = 100
    _tokens: float = field(init=False, default=0.0)
    _last_refill: float = field(init=False, default=0.0)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self._tokens = float(self.limit_per_hour)
        self._last_refill = time.monotonic()

    def _refill(self) -> None:
        """Recarrega tokens proporcionalmente ao tempo decorrido."""
        now = time.monotonic()
        elapsed_hours = (now - self._last_refill) / 3600.0
        new_tokens = elapsed_hours * self.limit_per_hour
        self._tokens = min(self.limit_per_hour, self._tokens + new_tokens)
        self._last_refill = now

    async def acquire(self) -> bool:
        """
        Tenta adquirir 1 token.
        Retorna True se pode fazer a query, False se limite atingido.
        """
        async with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            return False

    async def get_status(self) -> dict:
        """Retorna status atual do rate limiter."""
        async with self._lock:
            self._refill()
            seconds_to_next = 0.0
            if self._tokens < 1.0:
                needed = 1.0 - self._tokens
                seconds_to_next = (needed / self.limit_per_hour) * 3600.0
            return {
                "tokens_remaining": int(self._tokens),
                "limit_per_hour": self.limit_per_hour,
                "seconds_to_next_token": round(seconds_to_next, 1),
            }
