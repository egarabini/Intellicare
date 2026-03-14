"""AC-7: Ingest de documento + busca semântica."""
from __future__ import annotations

import os

import asyncpg
import httpx
import pytest

pytestmark = pytest.mark.e2e

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://intellicare:intellicare@localhost:5432/intellicare",
)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


@pytest.mark.asyncio
async def test_ingest_e_busca_semantica():
    """Ingerir 1 documento e verificar que a busca retorna ele no top-1."""
    # 1. Obter embedding do documento
    resp = httpx.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": "Protocolo de hipertensão arterial sistêmica"},
        timeout=30,
    )
    if resp.status_code != 200:
        pytest.skip(f"OLLAMA não disponível: {resp.status_code}")

    embedding = resp.json()["embedding"]
    assert len(embedding) == 768, f"Embedding com dimensão inesperada: {len(embedding)}"

    # 2. Inserir na knowledge_base do tenant_dev
    conn = await asyncpg.connect(DB_URL)
    try:
        await conn.execute("SET search_path TO tenant_dev, public")

        # Inserir com embedding
        emb_str = f"[{','.join(str(x) for x in embedding)}]"
        await conn.execute(
            """
            INSERT INTO knowledge_base (title, content, source_path, embedding)
            VALUES ($1, $2, $3, $4::vector)
            ON CONFLICT DO NOTHING
            """,
            "Protocolo HAS",
            "Protocolo de hipertensão arterial sistêmica — PA > 140/90 mmHg",
            "test/rag_test.txt",
            emb_str,
        )

        # 3. Busca semântica
        query_resp = httpx.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": "hipertensão pressão arterial"},
            timeout=30,
        )
        query_emb = query_resp.json()["embedding"]
        query_emb_str = f"[{','.join(str(x) for x in query_emb)}]"

        rows = await conn.fetch(
            f"""
            SELECT title,
                   1 - (embedding <=> '{query_emb_str}'::vector) AS sim
            FROM knowledge_base
            ORDER BY embedding <=> '{query_emb_str}'::vector
            LIMIT 3
            """
        )

        assert rows, "Busca não retornou resultados"
        top1 = rows[0]["title"]
        assert top1 == "Protocolo HAS", f"Top-1 inesperado: {top1}"

        # Cleanup
        await conn.execute(
            "DELETE FROM knowledge_base WHERE source_path = 'test/rag_test.txt'"
        )
    finally:
        await conn.close()

