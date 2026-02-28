"""Tool: check_regulatory — Verificacao regulatoria ANVISA/ANS/CFM/COFEN."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pierre.search.regulatory_client import RegulatoryClient


async def handle_check_regulatory(regulatory: RegulatoryClient, arguments: dict[str, Any]) -> dict:
    """Executa verificacao regulatoria e retorna resultado."""
    response = await regulatory.check(
        query=arguments["query"],
        authority=arguments.get("authority", "all"),
        document_type=arguments.get("document_type", "any"),
    )

    return {
        "status": response.status.value,
        "results": [asdict(r) for r in response.results],
        "query_time_ms": response.query_time_ms,
        "source": response.source,
        "cached": response.cached,
    }
