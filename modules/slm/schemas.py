"""Pydantic models (request/response) do modulo SLM."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0)
    stream: bool = False


class SourceRef(BaseModel):
    title: str
    source_path: str
    similarity: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
    model: str
    latency_ms: int


class ModelInfo(BaseModel):
    name: str
    size: Optional[str] = None

