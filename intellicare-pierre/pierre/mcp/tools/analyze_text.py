"""Tool: analyze_text — Analise profunda de texto via LLM local."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from pierre.llm.qwen_client import QwenClient


async def handle_analyze_text(qwen: QwenClient, arguments: dict[str, Any]) -> dict:
    """Executa analise de texto via Qwen e retorna resultado."""
    result = await qwen.analyze(
        text=arguments["text"],
        instruction=arguments["instruction"],
        output_format=arguments.get("output_format", "bullet_points"),
        max_tokens=arguments.get("max_tokens", 500),
        language=arguments.get("language", "pt-BR"),
    )

    return asdict(result)
