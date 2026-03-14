"""Pydantic models (request/response) do modulo Cuidado."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PatientCreate(BaseModel):
    full_name: str
    cpf: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[Literal["M", "F", "O"]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class PatientResponse(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    active: bool
    created_at: datetime


class EncounterCreate(BaseModel):
    patient_id: UUID
    chief_complaint: Optional[str] = None
    priority: Literal["emergency", "urgent", "normal", "low"] = "normal"


class EncounterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    clinician_id: str
    status: str
    chief_complaint: Optional[str]
    priority: str
    opened_at: datetime
    closed_at: Optional[datetime]


class NoteCreate(BaseModel):
    subjective: Optional[str] = None
    objective: Optional[str] = None
    assessment: Optional[str] = None
    plan: Optional[str] = None


class NoteResponse(NoteCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    encounter_id: UUID
    clinician_id: str
    created_at: datetime


class ClinicalAskRequest(BaseModel):
    query: str
    limit: int = 5
    min_similarity: float = 0.5

