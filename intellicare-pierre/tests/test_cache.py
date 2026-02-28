"""Testes do SearchCache — 3 testes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pierre.cache.search_cache import SearchCache


@pytest.mark.asyncio
async def test_cache_hit():
    """Cache retorna dados quando presente."""
    cache = SearchCache(enabled=True)

    # Mock Redis
    mock_redis = AsyncMock()
    mock_redis.get.return_value = '{"results": [{"title": "Cached"}], "total_results": 1}'
    mock_redis.ping.return_value = True
    cache._redis = mock_redis

    result = await cache.get("tavily", "test query", {"max_results": 5})
    assert result is not None
    assert result["results"][0]["title"] == "Cached"


@pytest.mark.asyncio
async def test_cache_miss():
    """Cache retorna None quando nao encontra."""
    cache = SearchCache(enabled=True)

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.ping.return_value = True
    cache._redis = mock_redis

    result = await cache.get("tavily", "new query", {})
    assert result is None


@pytest.mark.asyncio
async def test_cache_redis_unavailable():
    """Cache funciona (retorna None) quando Redis indisponivel."""
    cache = SearchCache(redis_url="redis://nonexistent:6379/1", enabled=True)

    # Forcar falha de conexao
    result = await cache.get("tavily", "any query", {})
    assert result is None

    # is_available retorna False
    available = await cache.is_available()
    assert available is False
