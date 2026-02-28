"""Handle /guideline command — clinical guideline search via Florence RAG (EF-W012)."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def handle_guideline(
    query: str,
    http_client: Optional[Any],
    module_urls: dict[str, str],
    formatter: Any,
) -> tuple[str, list[dict]]:
    """Return (text, attachments) for the /guideline command."""
    if not query:
        return "Informe a pergunta: `/guideline <pergunta clinica>`", []

    result_text = "Diretriz não encontrada."
    florence_url = module_urls.get("intellicare-florence", "")

    if florence_url and http_client:
        try:
            resp = await http_client.post(
                f"{florence_url}/api/v1/rag/query",
                json={"query": query, "top_k": 3},
                timeout=20.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                result_text = data.get("answer") or data.get("result") or result_text
        except Exception as exc:
            logger.warning("Florence RAG query failed: %s", exc)
            result_text = f"Erro ao consultar Florence: {exc}"

    attachments = formatter.guideline_result(query, result_text)
    return f"Diretriz clínica para: _{query}_", attachments
