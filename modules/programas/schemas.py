from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProgramCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: str | None = None
    target_count: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("name must have at least 3 characters")
        return value


class ProgramResponse(BaseModel):
    id: int
    name: str
    description: str | None
    target_count: int
    active: bool
    created_by: str | None
    created_at: datetime
    updated_at: datetime


class EnrollRequest(BaseModel):
    patient_id: UUID
    notes: str | None = None


class EnrollmentResponse(BaseModel):
    id: int
    program_id: int
    patient_id: UUID
    enrolled_at: datetime
    enrolled_by: str | None
    status: Literal["active", "discharged", "suspended"]
    notes: str | None


class OverduePatient(BaseModel):
    patient_id: UUID
    full_name: str
    last_encounter_date: datetime | None
    days_without_visit: int


class CoverageReport(BaseModel):
    program_id: int
    program_name: str
    target_count: int
    enrolled_count: int
    coverage_pct: float
    overdue_count: int
