"""
Embedding e busca semantica via OLLAMA + pgvector.
"""

from __future__ import annotations

import re
from typing import Any

import httpx
from sqlalchemy import text

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session


def _quote_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
        raise ValueError(f"Identificador SQL invalido: {identifier}")
    return f'"{identifier}"'


async def get_embedding(text_input: str, model: str | None = None) -> list[float]:
    settings = get_settings()
    selected_model = model or settings.ollama_embed_model

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.ollama_api_url}/api/embeddings",
            json={"model": selected_model, "prompt": text_input},
        )
        response.raise_for_status()
        return response.json()["embedding"]


async def semantic_search(
    query: str,
    ctx: TenantContext,
    table: str = "knowledge_base",
    limit: int = 5,
    min_similarity: float = 0.5,
) -> list[dict[str, Any]]:
    embedding = await get_embedding(query)
    embedding_str = "[" + ",".join(str(value) for value in embedding) + "]"
    quoted_table = _quote_identifier(table)

    async with tenant_session(ctx) as db:
        result = await db.execute(
            text(
                f"""
                SELECT
                    id,
                    title,
                    content,
                    source_path,
                    1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                FROM {quoted_table}
                WHERE 1 - (embedding <=> CAST(:emb AS vector)) >= :min_sim
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT :limit
                """
            ),
            {"emb": embedding_str, "min_sim": min_similarity, "limit": limit},
        )
        return [dict(row) for row in result.mappings().all()]


async def generate(prompt: str, context_chunks: list[str], model: str | None = None) -> str:
    settings = get_settings()
    selected_model = model or settings.ollama_generate_model
    context = "\n---\n".join(context_chunks)
    full_prompt = (
        "Voce e um assistente clinico. Com base nos protocolos abaixo, "
        "responda de forma objetiva e fundamentada.\n\n"
        f"PROTOCOLOS:\n{context}\n\n"
        f"PERGUNTA: {prompt}\n\n"
        "RESPOSTA:"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.ollama_api_url}/api/generate",
            json={"model": selected_model, "prompt": full_prompt, "stream": False},
        )
        response.raise_for_status()
        return response.json()["response"]
