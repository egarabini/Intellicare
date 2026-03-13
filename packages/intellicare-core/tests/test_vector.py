from __future__ import annotations

import pytest

from intellicare_core.contracts import TenantContext
from intellicare_core.vector import get_embedding, semantic_search


@pytest.mark.asyncio
async def test_get_embedding_returns_vector() -> None:
    embedding = await get_embedding("teste")
    assert isinstance(embedding, list)
    assert len(embedding) > 100
    assert all(isinstance(value, float) for value in embedding[:10])


@pytest.mark.asyncio
async def test_semantic_search_returns_results() -> None:
    ctx = TenantContext.from_slug("dev", "user-1", ["CLINICO"])
    results = await semantic_search(
        query="protocolos clinicos",
        ctx=ctx,
        table="knowledge_base",
        limit=3,
        min_similarity=0.0,
    )
    assert isinstance(results, list)
    assert len(results) >= 1
    assert "title" in results[0]
    assert "similarity" in results[0]
