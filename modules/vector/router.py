"""Vector Router — API de ingest e search."""
from __future__ import annotations

import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from intellicare_core.auth.jwt import require_role, get_current_tenant
from intellicare_core.contracts.base import TenantContext
from intellicare_core.vector.search import semantic_search
from .ingest_service import IngestService
from .schemas import IngestResponse, SearchResponse, VectorStats

router = APIRouter(prefix="/vector", tags=["vector"])
_ingest = IngestService()

GestorOrAdmin = Annotated[
    TenantContext,
    Depends(lambda ctx=Depends(get_current_tenant): ctx)  # qualquer autenticado
]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "vector", "version": "1.0.0"}


@router.post("/ingest", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
    ctx: GestorOrAdmin = Depends(get_current_tenant),
) -> dict:
    """Upload e ingestão de documento na knowledge_base do tenant."""
    if file.content_type not in (
        "application/pdf",
        "text/plain",
        "text/markdown",
        "text/x-markdown",
    ):
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de arquivo não suportado: {file.content_type}",
        )

    # Salvar temporariamente
    suffix = "." + (file.filename or "doc.txt").rsplit(".", 1)[-1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = await _ingest.ingest_file(
            file_path=tmp_path,
            ctx=ctx,
            source_label=file.filename or "unknown",
        )
    finally:
        os.unlink(tmp_path)

    return result


@router.get("/search", response_model=list[SearchResponse])
async def search(
    q: str = Query(..., min_length=2, description="Query de busca semântica"),
    limit: int = Query(default=5, ge=1, le=20),
    min_similarity: float = Query(default=0.5, ge=0.0, le=1.0),
    ctx: GestorOrAdmin = Depends(get_current_tenant),
) -> list[dict]:
    results = await semantic_search(
        query=q,
        ctx=ctx,
        limit=limit,
        min_similarity=min_similarity,
    )
    return results


@router.delete("/documents/{source_path:path}")
async def delete_document(
    source_path: str,
    ctx: Annotated[TenantContext, Depends(require_role("TENANT_GESTOR"))],
) -> dict:
    deleted = await _ingest.delete_document(source_path, ctx)
    return {"deleted_chunks": deleted, "source_path": source_path}


@router.get("/stats", response_model=VectorStats)
async def get_stats(ctx: GestorOrAdmin = Depends(get_current_tenant)) -> dict:
    return await _ingest.get_stats(ctx)
