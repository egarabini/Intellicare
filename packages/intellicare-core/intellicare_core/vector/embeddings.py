"""Embeddings via OLLAMA — versão de produção com batch e retry."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any
from typing import Sequence

import httpx
from sqlalchemy import text

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session

OLLAMA_URL  = os.getenv("OLLAMA_URL",   "http://ollama:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL",  "nomic-embed-text")
EMBED_DIM   = 768
BATCH_SIZE  = 32
MAX_RETRIES = 3

logger = logging.getLogger("intellicare.vector.embeddings")


async def get_embedding(text: str) -> list[float]:
    """Gera embedding para um único texto."""
    results = await batch_embed([text])
    return results[0]


async def batch_embed(texts: Sequence[str]) -> list[list[float]]:
    """
    Gera embeddings para múltiplos textos em batches de BATCH_SIZE.
    Retry automático com backoff exponencial.
    """
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    tasks = [
                        client.post(
                            f"{OLLAMA_URL}/api/embeddings",
                            json={"model": EMBED_MODEL, "prompt": t},
                        )
                        for t in batch
                    ]
                    responses = await asyncio.gather(*tasks)

                embeddings = []
                for resp in responses:
                    resp.raise_for_status()
                    emb = resp.json()["embedding"]
                    if len(emb) != EMBED_DIM:
                        raise ValueError(f"Embedding dim inesperada: {len(emb)} (esperado {EMBED_DIM})")
                    embeddings.append(emb)

                all_embeddings.extend(embeddings)
                break  # sucesso, sair do retry loop

            except Exception as exc:
                if attempt == MAX_RETRIES:
                    raise RuntimeError(f"Falha ao gerar embeddings após {MAX_RETRIES} tentativas: {exc}")
                wait = 2 ** attempt
                logger.warning("Embedding falhou (tentativa %d/%d), aguardando %ds: %s",
                               attempt, MAX_RETRIES, wait, exc)
                await asyncio.sleep(wait)

    return all_embeddings


async def semantic_search(
    query: str,
    ctx: TenantContext,
    table: str = "knowledge_base",
    limit: int = 5,
    min_similarity: float = 0.5,
) -> list[dict[str, Any]]:
    """Executa busca semantica no schema do tenant usando pgvector."""
    embedding = await get_embedding(query)
    embedding_str = "[" + ",".join(str(value) for value in embedding) + "]"

    async with tenant_session(ctx) as db:
        result = await db.execute(
            text(
                f"""
                SELECT
                    id,
                    title,
                    content,
                    source_path,
                    chunk_index,
                    created_at,
                    1 - (embedding <=> :emb::vector) AS similarity
                FROM {table}
                WHERE 1 - (embedding <=> :emb::vector) >= :min_similarity
                ORDER BY embedding <=> :emb::vector
                LIMIT :limit
                """
            ),
            {
                "emb": embedding_str,
                "min_similarity": min_similarity,
                "limit": limit,
            },
        )
        return [dict(row) for row in result.mappings().all()]


async def generate(prompt: str, context_chunks: list[str], model: str | None = None) -> str:
    """Gera resposta textual a partir de contexto recuperado."""
    settings = get_settings()
    generate_model = model or settings.ollama_generate_model
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
            json={"model": generate_model, "prompt": full_prompt, "stream": False},
        )
        response.raise_for_status()
        return response.json()["response"]
