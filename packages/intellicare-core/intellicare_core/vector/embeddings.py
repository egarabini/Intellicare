"""Embeddings via OLLAMA — versão de produção com batch e retry."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Sequence

import httpx

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
