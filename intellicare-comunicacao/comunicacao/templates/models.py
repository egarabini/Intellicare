"""Modelos de templates multi-canal."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class TemplateVariant(BaseModel):
    format: str
    body: str
    subject: str | None = None
    title: str | None = None
    max_length: int | None = None


class MessageTemplate(BaseModel):
    id: str
    name: str
    category: str
    description: str | None = None
    version: int = 1
    active: bool = True
    params_schema: dict[str, Any] = Field(default_factory=dict)
    sample_params: dict[str, Any] = Field(default_factory=dict)
    channel_variants: dict[str, TemplateVariant] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

