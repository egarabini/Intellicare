"""Modelos de resultado de extracao."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class ExtractionStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class ExtractionResult(BaseModel):
    status: ExtractionStatus
    raw_text: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: int
    engine_used: str
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None

