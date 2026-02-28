"""Pydantic models for CDS Hooks 2.0 protocol.

Spec: https://cds-hooks.hl7.org/2.0/
"""

from __future__ import annotations

import uuid
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ── Authorization ──────────────────────────────────────────────────────────────


class FHIRAuthorization(BaseModel):
    """OAuth2 bearer token for FHIR server access in a hook call."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str
    subject: str


# ── Card building blocks ────────────────────────────────────────────────────────


class CardSource(BaseModel):
    """Attribution for a CDS Hook card."""

    label: str
    url: Optional[str] = None
    icon: Optional[str] = None
    topic: Optional[dict[str, Any]] = None  # Coding


class Action(BaseModel):
    """An action that can be auto-applied or suggested inside a Card."""

    type: Literal["create", "update", "delete"]
    description: str
    resource: Optional[dict[str, Any]] = None  # FHIR resource


class Suggestion(BaseModel):
    """A suggested change a user can accept."""

    label: str
    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actions: list[Action] = []
    isRecommended: bool = False


class Link(BaseModel):
    """An external link shown in a Card."""

    label: str
    url: str
    type: Literal["absolute", "smart"] = "absolute"
    appContext: Optional[str] = None


class Card(BaseModel):
    """A CDS Hook card — the primary response unit.

    indicator: 'info' | 'warning' | 'critical'
    selectionBehavior: 'at-most-one' | 'any' (controls suggestion display)
    """

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    summary: str
    detail: Optional[str] = None
    indicator: Literal["info", "warning", "critical"] = "info"
    source: CardSource
    suggestions: list[Suggestion] = []
    selectionBehavior: Optional[Literal["at-most-one", "any"]] = None
    overrideReasons: Optional[list[dict[str, Any]]] = None
    links: list[Link] = []


# ── Request / Response ─────────────────────────────────────────────────────────


class CDSRequest(BaseModel):
    """Incoming CDS Hook request from the EHR."""

    hookInstance: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hook: str  # e.g. "patient-view", "order-sign"
    context: dict[str, Any]
    prefetch: Optional[dict[str, Any]] = None
    fhirServer: Optional[str] = None
    fhirAuthorization: Optional[FHIRAuthorization] = None


class CDSResponse(BaseModel):
    """Response from a CDS Hook service."""

    cards: list[Card] = []
    systemActions: list[Action] = []


# ── Service discovery ──────────────────────────────────────────────────────────


class CDSServiceDefinition(BaseModel):
    """Metadata for a single CDS service, returned at /cds-services discovery."""

    id: str
    hook: str
    title: str
    description: str
    prefetch: dict[str, str] = {}
    usageRequirements: Optional[str] = None
