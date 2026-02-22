"""Domain models for ecosystem event coordination (EF-W006)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class EventCoordinationStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class IntelliCareEvent:
    """An event emitted by any IntelliCare module to the Redis Streams bus."""

    event_type: str          # lab_result_critical | vital_sign_alert | adherence_missed |
                             # condition_worsened | medication_schedule | appointment_reminder
    patient_id: str
    source_module: str       # intellicare-florence | oswaldo | geralda | zilda | etc.
    payload: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: str = "medium"  # low | medium | high | critical


@dataclass
class CoordinationResult:
    """Result of coordinating an ecosystem event."""

    event_id: str
    event_type: str
    status: EventCoordinationStatus
    agents_notified: list[str] = field(default_factory=list)
    agents_failed: list[str] = field(default_factory=list)
    workflow_triggered: Optional[str] = None
    coordination_time_ms: int = 0
    error: Optional[str] = None
