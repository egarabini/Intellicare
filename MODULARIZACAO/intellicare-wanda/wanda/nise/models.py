"""Domain models for Dr. Nise / FLOWISE chatbot (EF-W013)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"
    ESCALATED = "ESCALATED"


@dataclass
class NiseSession:
    """Represents a patient chat session with Dr. Nise."""

    patient_id: str
    channel: str = "web"  # web | app | rc
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    message_count: int = 0
    flagged_count: int = 0
    escalated: bool = False
    status: SessionStatus = SessionStatus.ACTIVE
    history: list[dict] = field(default_factory=list)  # [{role, content}]


@dataclass
class PatientMessage:
    """A message sent by a patient to Dr. Nise."""

    patient_id: str
    content: str
    session_id: Optional[str] = None
    channel: str = "web"


@dataclass
class FlowiseResponse:
    """Raw response from FLOWISE API."""

    text: str
    success: bool = True
    error: Optional[str] = None


@dataclass
class FilterResult:
    """Result of safety filtering on a FLOWISE response."""

    safe: bool
    filtered_text: str
    flagged_patterns: list[str] = field(default_factory=list)
    requires_escalation: bool = False


@dataclass
class DrNiseResponse:
    """Final response returned to the patient."""

    session_id: str
    text: str
    flagged: bool = False
    escalated: bool = False
    message_count: int = 0
