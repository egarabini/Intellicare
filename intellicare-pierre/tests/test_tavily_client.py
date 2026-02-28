"""Testes do TavilySearchClient — 4 testes."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pierre.cache.search_cache import SearchCache
from pierre.models import SearchStatus
from pierre.rate_limiter.limiter import TavilyRateLimiter
from pierre.search.tavily_client import TavilySearchClient


@pytest.mark.asyncio
async def test_tavily_search_success(cache, rate_limiter):
    """Busca Tavily com sucesso retorna resultados."""
    client = TavilySearchClient(api_key="tvly-test", cache=cache, rate_limiter=rate_limiter)

    mock_tavily = MagicMock()
    mock_tavily.search.return_value = {
        "results": [
            {
                "title": "KDIGO 2024 CKD Guideline",
                "url": "https://kdigo.org/guidelines/ckd/2024",
                "content": "The 2024 KDIGO guideline recommends...",
                "published_date": "2024-11-15",
                "score": 0.97,
            }
        ],
        "answer": "KDIGO 2024 recommends SGLT2 inhibitors...",
    }

    with patch.object(client, "_get_client", return_value=mock_tavily):
        response = await client.search("KDIGO 2024 CKD guidelines")

    assert response.status == SearchStatus.SUCCESS
    assert len(response.results) == 1
    assert response.results[0].title == "KDIGO 2024 CKD Guideline"
    assert response.results[0].relevance_score == 0.97
    assert response.answer is not None


@pytest.mark.asyncio
async def test_tavily_search_no_results(cache, rate_limiter):
    """Busca sem resultados retorna NO_RESULTS."""
    client = TavilySearchClient(api_key="tvly-test", cache=cache, rate_limiter=rate_limiter)

    mock_tavily = MagicMock()
    mock_tavily.search.return_value = {"results": [], "answer": None}

    with patch.object(client, "_get_client", return_value=mock_tavily):
        response = await client.search("xyznonexistent12345")

    assert response.status == SearchStatus.NO_RESULTS
    assert len(response.results) == 0


@pytest.mark.asyncio
async def test_tavily_search_rate_limited():
    """Rate limit atingido retorna RATE_LIMITED."""
    cache = SearchCache(enabled=False)
    rate_limiter = TavilyRateLimiter(limit_per_hour=0)  # Zero tokens!

    client = TavilySearchClient(api_key="tvly-test", cache=cache, rate_limiter=rate_limiter)
    response = await client.search("any query")

    assert response.status == SearchStatus.RATE_LIMITED


@pytest.mark.asyncio
async def test_tavily_search_cache_hit(rate_limiter):
    """Cache hit retorna resultado cacheado sem chamar API."""
    cache = SearchCache(enabled=False)  # Vamos mockar diretamente

    cached_data = {
        "results": [
            {
                "title": "Cached Result",
                "url": "https://example.com",
                "content": "From cache",
                "published_date": None,
                "relevance_score": 0.9,
                "source_type": "other",
            }
        ],
        "answer": "Cached answer",
        "total_results": 1,
    }

    cache.get = AsyncMock(return_value=cached_data)

    client = TavilySearchClient(api_key="tvly-test", cache=cache, rate_limiter=rate_limiter)
    response = await client.search("cached query")

    assert response.cached is True
    assert response.status == SearchStatus.SUCCESS
    assert response.results[0].title == "Cached Result"
