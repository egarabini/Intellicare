"""Cliente HTTP para intellicare-conhecimento."""

from __future__ import annotations

from typing import Any

import httpx


class KnowledgeClient:
    """Cliente assíncrono para consumo da API de conhecimento."""

    def __init__(self, base_url: str, timeout_seconds: float = 3.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def query_rag(self, query: str, top_k: int = 5, source: str | None = None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"query": query, "top_k": top_k}
        if source:
            payload["source"] = source

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/api/v1/rag/query", json=payload)
            response.raise_for_status()
            data = response.json()

        if isinstance(data, list):
            return data
        return []
