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
import os

import httpx


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
