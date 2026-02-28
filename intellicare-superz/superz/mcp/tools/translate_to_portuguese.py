"""Tool: translate_to_portuguese — Traducao medica PT-BR."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from superz.llm.qwen_client import QwenClient


async def handle_translate_to_portuguese(qwen: QwenClient, arguments: dict[str, Any]) -> dict:
    """Traduz texto medico para PT-BR."""
    result = await qwen.translate(
        text=arguments["text"],
        source_language=arguments.get("source_language", "auto"),
        preserve_medical_terms=arguments.get("preserve_medical_terms", True),
        context=arguments.get("context", "medical_guideline"),
    )

    return asdict(result)
