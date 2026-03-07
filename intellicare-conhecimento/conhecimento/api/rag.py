from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from conhecimento.api.dependencies import get_indexer, get_retriever
from conhecimento.rag import KnowledgeIndexer, PGVectorRetriever

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    source: str | None = None


@router.post("/reindex")
def reindex(indexer: KnowledgeIndexer = Depends(get_indexer)):
    count = indexer.reindex_protocols()
    return {"indexed_documents": count}


@router.post("/query")
def query(body: RAGQueryRequest, retriever: PGVectorRetriever = Depends(get_retriever)):
    results = retriever.query(body.query, top_k=body.top_k, source=body.source)
    return [
        {
            "id": item.document.id,
            "source": item.document.source,
            "score": item.score,
            "metadata": item.document.metadata,
            "text": item.document.text[:500],
        }
        for item in results
    ]

