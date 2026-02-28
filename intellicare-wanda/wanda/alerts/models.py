"""Domain models for clinical alert coordination (EF-W007)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ClinicalAlert:
    """Alert sent by an agent (Florence, Oswaldo, Geralda) to the AlertHub."""

    patient_id: str
    source_agent: str      # intellicare-florence | oswaldo | geralda
    alert_type: str        # vital_sign | lab_result | adherence_low | condition_worsened | medication_missed
    severity: str          # low | medium | high | critical
    title: str
    description: str = ""
    recommended_action: str = ""
    clinical_data: dict = field(default_factory=dict)
    idempotency_key: Optional[str] = None
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.idempotency_key is None:
            # Auto-generate stable key: patient + type + agent + hour
            hour_bucket = self.timestamp.strftime("%Y%m%d%H")
            self.idempotency_key = (
                f"{self.patient_id}:{self.alert_type}:{self.source_agent}:{hour_bucket}"
            )


@dataclass
class AlertPriority:
    """Priority calculation result for an alert."""

    score: int               # 0-100 (higher = more urgent)
    adjusted_severity: str   # may differ from original if context factors apply
    factors: list[str] = field(default_factory=list)


@dataclass
class AlertProcessingResult:
    """Result returned after AlertHub processes a received alert."""

    alert_id: str
    status: str              # accepted | deduplicated | consolidated | error
    priority_score: int = 0
    message: str = ""


@dataclass
class ConsolidatedAlert:
    """Multiple simultaneous alerts merged into one."""

    primary_alert: ClinicalAlert
    merged_ids: list[str] = field(default_factory=list)
    consolidated_title: str = ""

    def __post_init__(self) -> None:
        if not self.consolidated_title:
            count = len(self.merged_ids) + 1
            self.consolidated_title = f"{self.primary_alert.title} (+{count - 1} relacionados)"
