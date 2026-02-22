"""Tool: summarize_document — Resume documento longo."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from superz.llm.qwen_client import QwenClient
from superz.llm.url_fetcher import URLFetcher


async def handle_summarize_document(
    qwen: QwenClient,
    url_fetcher: URLFetcher,
    arguments: dict[str, Any],
) -> dict:
    """Resume documento (texto direto ou URL)."""
    text = arguments.get("text", "")
    url = arguments.get("url", "")

    # Se URL fornecida e sem texto, buscar conteudo
    if url and not text:
        fetched = await url_fetcher.fetch_text(url)
        if fetched:
            text = fetched
        else:
            return {
                "summary": f"[ERRO] Nao foi possivel acessar a URL: {url}",
                "key_actions": [],
                "source_url": url,
                "document_title": None,
                "summary_type": arguments.get("summary_type", "clinical_action"),
                "processing_time_ms": 0,
            }

    if not text:
        return {
            "summary": "[ERRO] Nenhum texto ou URL fornecido.",
            "key_actions": [],
            "source_url": None,
            "document_title": None,
            "summary_type": arguments.get("summary_type", "clinical_action"),
            "processing_time_ms": 0,
        }

    result = await qwen.summarize(
        text=text,
        summary_type=arguments.get("summary_type", "clinical_action"),
        max_sentences=arguments.get("max_sentences", 5),
        target_audience=arguments.get("target_audience", "medico"),
        language=arguments.get("language", "pt-BR"),
    )

    result.source_url = url or None

    return asdict(result)
