"""LLM client compartilhado — OpenAI-compatible (Ollama, OpenAI, Groq, etc).

Variáveis de ambiente:
  FLORENCE_LLM_URL      — URL do endpoint (ex: https://api.openai.com/v1/chat/completions)
  FLORENCE_LLM_API_KEY  — API key (Bearer token)
  FLORENCE_LLM_MODEL    — modelo (default: gpt-4o-mini)

Sem FLORENCE_LLM_URL configurada, call_llm() levanta RuntimeError
e o chamador deve fazer fallback para regras determinísticas.
"""
from __future__ import annotations

import json
import logging
import os

import httpx
from sqlalchemy import text

from intellicare_core.db.session import get_engine

logger = logging.getLogger("intellicare.shared.llm")
_PROMPT_CACHE: dict[str, str] = {}


def clear_prompt_cache(prompt_key: str | None = None) -> None:
    if prompt_key is None:
        _PROMPT_CACHE.clear()
        return
    _PROMPT_CACHE.pop(prompt_key, None)


async def get_prompt_template(prompt_key: str, fallback_prompt: str) -> str:
    cached = _PROMPT_CACHE.get(prompt_key)
    if cached is not None:
        return cached

    prompt = fallback_prompt
    try:
        async with get_engine().connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT content
                    FROM public.prompt_templates
                    WHERE prompt_key = :prompt_key
                      AND is_active = true
                    ORDER BY version DESC
                    LIMIT 1
                """),
                {"prompt_key": prompt_key},
            )
            db_prompt = result.scalar_one_or_none()
            if db_prompt:
                prompt = db_prompt
    except Exception:
        logger.debug("Prompt versioning indisponivel para %s; usando fallback", prompt_key, exc_info=True)

    _PROMPT_CACHE[prompt_key] = prompt
    return prompt


async def call_llm(prompt: str) -> dict:
    """Chama LLM OpenAI-compatible e retorna o JSON parseado."""
    url = os.getenv("FLORENCE_LLM_URL", "")
    api_key = os.getenv("FLORENCE_LLM_API_KEY", "")
    model = os.getenv("FLORENCE_LLM_MODEL", "gpt-4o-mini")

    if not url:
        raise RuntimeError("FLORENCE_LLM_URL not configured")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        data["model"] = model
        return data
