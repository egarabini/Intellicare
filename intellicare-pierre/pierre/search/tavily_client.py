"""TavilySearchClient — busca web curada para agentes LLM."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict
from typing import Any, Optional

from pierre.cache.search_cache import SearchCache
from pierre.errors import TavilyRateLimitError, TavilyUnavailableError
from pierre.models import SearchStatus, WebSearchResponse, WebSearchResult
from pierre.rate_limiter.limiter import TavilyRateLimiter

logger = logging.getLogger(__name__)


class TavilySearchClient:
    """
    Cliente para Tavily API — busca web curada para agentes LLM.

    Rate limit padrao: 100 queries/hora (configuravel).
    Cache: 6h por query identica (Redis).
    """

    def __init__(
        self,
        api_key: str,
        cache: SearchCache,
        rate_limiter: TavilyRateLimiter,
    ):
        self._api_key = api_key
        self._cache = cache
        self._rate_limiter = rate_limiter
        self._client: Any = None

    def _get_client(self) -> Any:
        """Lazy-init TavilyClient."""
        if self._client is None:
            if not self._api_key:
                raise TavilyUnavailableError("TAVILY_API_KEY nao configurada")
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self._api_key)
            except ImportError:
                raise TavilyUnavailableError("tavily-python nao instalado")
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        time_range: str | None = None,
    ) -> WebSearchResponse:
        """Busca web via Tavily com cache e rate limiting."""
        t0 = time.monotonic()

        # 1. Cache check
        params = {
            "max_results": max_results,
            "search_depth": search_depth,
            "include_domains": include_domains or [],
            "exclude_domains": exclude_domains or [],
            "time_range": time_range or "",
        }
        cached = await self._cache.get("tavily", query, params)
        if cached:
            resp = self._parse_cached(cached)
            resp.cached = True
            resp.query_time_ms = int((time.monotonic() - t0) * 1000)
            return resp

        # 2. Rate limit check
        if not await self._rate_limiter.acquire():
            return WebSearchResponse(
                status=SearchStatus.RATE_LIMITED,
                query_time_ms=int((time.monotonic() - t0) * 1000),
            )

        # 3. Call Tavily API (sync → thread)
        try:
            client = self._get_client()
            kwargs: dict[str, Any] = {
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
            }
            if include_domains:
                kwargs["include_domains"] = include_domains
            if exclude_domains:
                kwargs["exclude_domains"] = exclude_domains

            raw = await asyncio.to_thread(client.search, **kwargs)
        except TavilyUnavailableError:
            raise
        except Exception as e:
            logger.error("Tavily search falhou: %s", e)
            return WebSearchResponse(
                status=SearchStatus.SOURCE_UNAVAILABLE,
                query_time_ms=int((time.monotonic() - t0) * 1000),
            )

        # 4. Parse response
        results = []
        for r in raw.get("results", []):
            results.append(WebSearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                published_date=r.get("published_date"),
                relevance_score=r.get("score", 0.0),
                source_type=self._classify_source(r.get("url", "")),
            ))

        response = WebSearchResponse(
            status=SearchStatus.SUCCESS if results else SearchStatus.NO_RESULTS,
            results=results,
            answer=raw.get("answer"),
            total_results=len(results),
            query_time_ms=int((time.monotonic() - t0) * 1000),
        )

        # 5. Cache save
        cache_data = {
            "results": [asdict(r) for r in results],
            "answer": raw.get("answer"),
            "total_results": len(results),
        }
        await self._cache.set("tavily", query, params, cache_data)

        return response

    async def is_available(self) -> bool:
        """Verifica se Tavily API esta configurada."""
        return bool(self._api_key)

    @staticmethod
    def _classify_source(url: str) -> str:
        """Classifica tipo de fonte pela URL."""
        url_lower = url.lower()
        if any(d in url_lower for d in ["pubmed", "ncbi", "scielo", "bireme"]):
            return "article"
        if any(d in url_lower for d in ["anvisa", "ans.gov", "cfm.org", "cofen"]):
            return "regulatory"
        if any(d in url_lower for d in ["guideline", "kdigo", "gold", "who.int"]):
            return "guideline"
        if any(d in url_lower for d in ["news", "agencia", "reuters", "folha"]):
            return "news"
        return "other"

    @staticmethod
    def _parse_cached(cached: dict) -> WebSearchResponse:
        """Converte dados do cache em WebSearchResponse."""
        results = [
            WebSearchResult(**r) for r in cached.get("results", [])
        ]
        return WebSearchResponse(
            status=SearchStatus.SUCCESS if results else SearchStatus.NO_RESULTS,
            results=results,
            answer=cached.get("answer"),
            total_results=cached.get("total_results", len(results)),
        )
