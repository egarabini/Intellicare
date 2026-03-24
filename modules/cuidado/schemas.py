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


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str # The spec returned "name" in Gestor and Profile, but db is full_name let's map it.
    cpf: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    health_plan: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    active: bool
    created_at: datetime
    last_encounter: Optional[date] = None
    encounter_count: int = 0
    programs: list[str] = []
    pessoa_id: Optional[UUID] = None

class PatientClinicalUpdate(BaseModel):
    allergies: Optional[str] = None
    medications: Optional[str] = None

class AgendaItem(BaseModel):
    id: UUID
    patient_id: UUID
    patient_name: str
    scheduled_at: datetime
    type: str
    status: str
    encounter_id: Optional[UUID] = None


class EncounterCreate(BaseModel):
    patient_id: UUID
    chief_complaint: Optional[str] = None
    priority: Literal["emergency", "urgent", "normal", "low"] = "normal"


class EncounterUpdate(BaseModel):
    cid10_code: Optional[str] = None
    prescription: Optional[str] = None

class EncounterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    clinician_id: str
    status: str
    chief_complaint: Optional[str]
    priority: str
    cid10_code: Optional[str] = None
    prescription: Optional[str] = None
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


class Cid10Response(BaseModel):
    code: str
    description: str

class ClinicalAskRequest(BaseModel):
    query: str
    limit: int = 5
    min_similarity: float = 0.5


# ── Paciente Portal Schemas ──────────────────────────────────────────────────

class PacientePainelResponse(BaseModel):
    patient_name: str
    next_appointment: Optional[dict] = None
    clinic_notice: Optional[str] = None
    upcoming_count: int = 0
    past_count: int = 0


class PacienteAppointmentItem(BaseModel):
    id: UUID
    scheduled_at: datetime
    clinician_name: str
    type: str
    status: str


class PacienteHistoryItem(BaseModel):
    id: UUID
    date: date
    clinician_name: str
    type: str
    cid10_code: Optional[str] = None
    cid10_description: Optional[str] = None
    prescription: Optional[str] = None


class PacienteHistoryResponse(BaseModel):
    items: list[PacienteHistoryItem]
    total: int
    page: int
    size: int


class PacienteJourneyItem(BaseModel):
    correlation_id: UUID
    channel: str
    status: str
    template_name: Optional[str] = None
    opened_at: datetime
    closed_at: Optional[datetime] = None


class PacienteClinicalNoteItem(BaseModel):
    encounter_date: datetime
    professional_name: str
    summary: str


class PacienteProgramItem(BaseModel):
    id: int
    name: str
    clinician_name: Optional[str] = None
    enrolled_at: Optional[date] = None
    status: str
    next_action: Optional[str] = None


class PacienteMeResponse(BaseModel):
    full_name: str
    cpf: Optional[str] = None
    birth_date: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    health_plan: Optional[str] = None


class PacienteMeUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None


class ClinicInfoResponse(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    hours: Optional[str] = None


# ── DEM-071: Linha do Tempo Clínica ─────────────────────────────────────────

class TimelineNoteItem(BaseModel):
    id: int
    note_type: str
    soap_s: Optional[str] = None
    soap_o: Optional[str] = None
    soap_a: Optional[str] = None
    soap_p: Optional[str] = None
    free_text: Optional[str] = None
    author_name: str
    created_at: datetime


class TimelinePrescriptionItem(BaseModel):
    id: int
    cid10_code: Optional[str] = None
    cid10_desc: Optional[str] = None
    items: list[dict] = []
    notes: Optional[str] = None
    status: str
    author_name: str
    created_at: datetime


class TimelineEvent(BaseModel):
    """Um item na linha do tempo clínica unificada."""
    event_type: Literal[
        "encounter", "clinical_note", "prescription", "care_task",
    ]
    event_id: str
    occurred_at: datetime
    title: str
    subtitle: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


class ClinicalTimelineResponse(BaseModel):
    patient_id: str
    total: int
    items: list[TimelineEvent]


# ── DEM-032: Clínico Gestão ──────────────────────────────────────────────────

class ProfessionalCreate(BaseModel):
    name: str
    council_type: Literal["CRM", "COREN", "CRO", "CRP", "CREFITO", "other"]
    council_number: str
    specialty: str
    unit_id: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class ProfessionalUpdate(BaseModel):
    name: Optional[str] = None
    council_type: Optional[Literal["CRM", "COREN", "CRO", "CRP", "CREFITO", "other"]] = None
    council_number: Optional[str] = None
    specialty: Optional[str] = None
    unit_id: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class ProfessionalOut(BaseModel):
    id: int
    name: str
    council_type: str
    council_number: str
    specialty: str
    unit_id: Optional[int] = None
    unit_name: Optional[str] = None
    groups: list[str] = []
    status: str
    keycloak_id: Optional[str] = None


class GroupCreate(BaseModel):
    name: str
    specialty: Optional[str] = None
    unit_id: Optional[int] = None
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    unit_id: Optional[int] = None
    description: Optional[str] = None


class GroupOut(BaseModel):
    id: int
    name: str
    specialty: Optional[str] = None
    unit_id: Optional[int] = None
    unit_name: Optional[str] = None
    description: Optional[str] = None
    status: str
    member_count: int = 0


class AddMember(BaseModel):
    professional_id: int


class GroupMemberOut(BaseModel):
    professional_id: int
    name: str
    council_type: str
    council_number: str
    specialty: str
    added_at: datetime


class ClinicalUserOut(BaseModel):
    id: int
    keycloak_id: str
    name: str
    email: Optional[str] = None
    role: str
    status: str
