"""Fixtures globais para testes do intellicare-pierre."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pierre.cache.search_cache import SearchCache
from pierre.config import PierreConfig
from pierre.llm.qwen_client import QwenClient
from pierre.llm.url_fetcher import URLFetcher
from pierre.rate_limiter.limiter import TavilyRateLimiter
from pierre.search.bireme_client import BIREMEClient
from pierre.search.pubmed_client import PubMedClient
from pierre.search.scielo_client import SciELOClient
from pierre.search.tavily_client import TavilySearchClient


@pytest.fixture
def config() -> PierreConfig:
    """Config de teste."""
    return PierreConfig(
        tavily_api_key="tvly-test-key-12345",
        pubmed_api_key="test-ncbi-key",
        ollama_url="http://localhost:11434",
        llm_model="qwen2.5:7b",
        llm_model_fallback="qwen2.5:7b",
        redis_url="redis://localhost:6379/15",
        cache_enabled=False,
    )


@pytest.fixture
def cache() -> SearchCache:
    """Cache desabilitado para testes."""
    return SearchCache(enabled=False)


@pytest.fixture
def rate_limiter() -> TavilyRateLimiter:
    """Rate limiter com limite alto para testes."""
    return TavilyRateLimiter(limit_per_hour=10000)


@pytest.fixture
def tavily_client(cache, rate_limiter) -> TavilySearchClient:
    """TavilySearchClient com cache e rate limiter de teste."""
    return TavilySearchClient(api_key="tvly-test-key", cache=cache, rate_limiter=rate_limiter)


@pytest.fixture
def pubmed_client() -> PubMedClient:
    """PubMedClient de teste."""
    return PubMedClient(api_key="test-key")


@pytest.fixture
def bireme_client() -> BIREMEClient:
    """BIREMEClient de teste."""
    return BIREMEClient()


@pytest.fixture
def scielo_client() -> SciELOClient:
    """SciELOClient de teste."""
    return SciELOClient()


@pytest.fixture
def qwen_client() -> QwenClient:
    """QwenClient de teste."""
    return QwenClient(
        ollama_url="http://localhost:11434",
        model="qwen2.5:7b",
        model_fallback="qwen2.5:7b",
    )


@pytest.fixture
def url_fetcher() -> URLFetcher:
    """URLFetcher de teste."""
    return URLFetcher()
