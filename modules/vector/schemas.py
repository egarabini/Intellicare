from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class IngestResponse(BaseModel):
    source_path: str
    chunk_count: int
    duration_ms: int


class SearchResponse(BaseModel):
    id: int
    title: str
    content: str
    source_path: str
    similarity: float


class VectorStats(BaseModel):
    doc_count: int
    chunk_count: int
    last_ingested_at: Optional[datetime]
