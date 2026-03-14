"""SLMService — geracao de resposta clinica via OLLAMA + RAG."""
from __future__ import annotations

import json as _json
import logging
import os
import time
from typing import AsyncIterator

import httpx

from intellicare_core.contracts.base import TenantContext
from intellicare_core.vector import semantic_search

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
SLM_MODEL = os.getenv("SLM_MODEL", "llama3.2:3b")
SLM_TIMEOUT = int(os.getenv("SLM_TIMEOUT_S", "30"))

SYSTEM_PROMPT = (
    "Você é um assistente clínico do IntelliCare. "
    "Responda APENAS com base no contexto clínico fornecido abaixo. "
    "Responda sempre em português do Brasil. Seja objetivo e cite as fontes pelo título. "
    "Se o contexto não contiver informação suficiente, diga explicitamente. "
    "Nunca invente dados clínicos, doses, diagnósticos ou condutas."
)

logger = logging.getLogger("intellicare.slm")


def _build_prompt(query: str, chunks: list[dict]) -> str:
    ctx = "\n\n---\n\n".join(
        f"[{c['title']}]\n{c['content']}" for c in chunks
    )
    return f"CONTEXTO:\n{ctx}\n\nPERGUNTA: {query}\n\nRESPOSTA:"


class SLMService:
    """Servico de geracao de resposta clinica via OLLAMA."""

    async def ask(
        self,
        query: str,
        ctx: TenantContext,
        limit: int = 5,
        min_similarity: float = 0.5,
    ) -> dict:
        t0 = time.monotonic()

        chunks = await semantic_search(
            query, ctx, limit=limit, min_similarity=min_similarity,
        )

        if not chunks:
            return {
                "answer": "Não encontrei informações suficientes nos protocolos disponíveis.",
                "sources": [],
                "model": SLM_MODEL,
                "latency_ms": int((time.monotonic() - t0) * 1000),
            }

        try:
            async with httpx.AsyncClient(timeout=SLM_TIMEOUT) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": SLM_MODEL,
                        "prompt": _build_prompt(query, chunks),
                        "system": SYSTEM_PROMPT,
                        "stream": False,
                        "options": {"temperature": 0.1},
                    },
                )
                resp.raise_for_status()
                answer = resp.json().get("response", "").strip()
        except httpx.TimeoutException:
            raise RuntimeError("OLLAMA timeout: modelo demorou mais de 30s")
        except httpx.ConnectError:
            raise ConnectionError("OLLAMA indisponível")

        sources = [
            {
                "title": c["title"],
                "source_path": c["source_path"],
                "similarity": c["similarity"],
            }
            for c in chunks
        ]

        return {
            "answer": answer,
            "sources": sources,
            "model": SLM_MODEL,
            "latency_ms": int((time.monotonic() - t0) * 1000),
        }

    async def stream_ask(
        self,
        query: str,
        ctx: TenantContext,
        limit: int = 5,
        min_similarity: float = 0.5,
    ) -> AsyncIterator[str]:
        chunks = await semantic_search(
            query, ctx, limit=limit, min_similarity=min_similarity,
        )

        if not chunks:
            yield "data: Não encontrei informações suficientes.\n\n"
            return

        async with httpx.AsyncClient(timeout=SLM_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": SLM_MODEL,
                    "prompt": _build_prompt(query, chunks),
                    "system": SYSTEM_PROMPT,
                    "stream": True,
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        data = _json.loads(line)
                        if data.get("response"):
                            yield f"data: {data['response']}\n\n"
                        if data.get("done"):
                            break

        yield "data: [DONE]\n\n"

    async def list_models(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(f"{OLLAMA_URL}/api/tags")
                return r.json().get("models", [])
        except Exception:
            return []

