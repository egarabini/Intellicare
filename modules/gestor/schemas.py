from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime, date
from typing import Literal, Optional, Any
from uuid import UUID


# ---------------------------------------------------------------------------
# Unit Profile / Tenant Settings
# ---------------------------------------------------------------------------


class UnitProfile(BaseModel):
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    unit_type: Literal["ubs", "clinic", "hospital", "specialty"] = "clinic"
    phone: Optional[str] = None
    email: Optional[str] = None


class UnitProfileResponse(UnitProfile):
    id: UUID
    updated_at: datetime


class InviteUserRequest(BaseModel):
    email: EmailStr
    name: str
    role: Literal["CLINICO", "PACIENTE"]


class DocumentInfo(BaseModel):
    source_path: str
    chunk_count: int
    last_ingested_at: datetime


class UsageReport(BaseModel):
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    total_queries: int
    avg_latency_ms: float
    top_queries: list[str]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardStats(BaseModel):
    patients_active: int
    appointments_today: int
    appointments_week: int
    appointments_month: int
    invoices_pending_count: int
    invoices_pending_total: float
    rag_documents_count: int
    recent_activity: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------

class PatientCreate(BaseModel):
    name: str = Field(..., min_length=3)
    cpf: str = Field(..., min_length=11, max_length=11)
    birth_date: date
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    health_plan: Optional[str] = None

class PatientUpdate(BaseModel):
    name: Optional[str] = None
    cpf: Optional[str] = None
    birth_date: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    health_plan: Optional[str] = None

class PatientResponse(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

class AppointmentCreate(BaseModel):
    patient_id: UUID
    clinician_id: str | UUID
    scheduled_at: datetime
    type: Literal["consulta", "retorno", "exame"]
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    type: Optional[Literal["consulta", "retorno", "exame"]] = None
    status: Optional[Literal["agendado", "confirmado", "realizado", "cancelado"]] = None
    notes: Optional[str] = None

class AppointmentResponse(AppointmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------------

class ProgramCreate(BaseModel):
    name: str = Field(..., min_length=3)
    description: Optional[str] = None
    eligibility_criteria: Optional[str] = None

class ProgramResponse(ProgramCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    active: bool
    created_at: datetime

class CoverageReport(BaseModel):
    program_id: UUID
    program_name: str
    eligible_patients: int
    enrolled_patients: int
    coverage_pct: float
    overdue_patients: int
