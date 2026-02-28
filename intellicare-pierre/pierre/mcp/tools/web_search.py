"""Tool: web_search — Busca web em tempo real via Tavily."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pierre.search.tavily_client import TavilySearchClient


async def handle_web_search(tavily: TavilySearchClient, arguments: dict[str, Any]) -> dict:
    """Executa web_search e retorna resultado serializado."""
    response = await tavily.search(
        query=arguments["query"],
        max_results=arguments.get("max_results", 5),
        search_depth=arguments.get("search_depth", "advanced"),
        include_domains=arguments.get("include_domains"),
        exclude_domains=arguments.get("exclude_domains"),
        time_range=arguments.get("time_range"),
    )

    return {
        "status": response.status.value,
        "results": [asdict(r) for r in response.results],
        "answer": response.answer,
        "total_results": response.total_results,
        "query_time_ms": response.query_time_ms,
        "cached": response.cached,
    }
