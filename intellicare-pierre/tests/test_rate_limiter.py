"""Testes do TavilyRateLimiter — 2 testes."""

from __future__ import annotations

import pytest

from pierre.rate_limiter.limiter import TavilyRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit():
    """Rate limiter permite queries dentro do limite."""
    limiter = TavilyRateLimiter(limit_per_hour=10)

    # Deve permitir 10 queries
    results = []
    for _ in range(10):
        results.append(await limiter.acquire())

    assert all(results)

    # 11a deve falhar
    assert await limiter.acquire() is False


@pytest.mark.asyncio
async def test_rate_limiter_status():
    """Status mostra tokens restantes corretamente."""
    limiter = TavilyRateLimiter(limit_per_hour=100)

    # Consumir 3 tokens
    await limiter.acquire()
    await limiter.acquire()
    await limiter.acquire()

    status = await limiter.get_status()
    assert status["limit_per_hour"] == 100
    assert status["tokens_remaining"] == 97
