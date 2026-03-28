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
    units_active: int = 0
    professionals_allocated: int = 0
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

class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    cpf: str
    birth_date: date
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    health_plan: Optional[str] = None
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
    id: int
    active: bool
    created_at: datetime

class CoverageReport(BaseModel):
    program_id: int
    program_name: str
    eligible_patients: int
    enrolled_patients: int
    coverage_pct: float
    overdue_patients: int


# ---------------------------------------------------------------------------
# Units (DEM-031)
# ---------------------------------------------------------------------------

class UnitCreate(BaseModel):
    name: str = Field(..., min_length=2)
    type: Literal['ubs', 'hospital', 'clinic', 'secretary', 'other']
    cnes: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = Field(None, max_length=2)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    manager_user_id: Optional[str] = None

class UnitUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[Literal['ubs', 'hospital', 'clinic', 'secretary', 'other']] = None
    cnes: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = Field(None, max_length=2)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    manager_user_id: Optional[str] = None

class UnitOut(BaseModel):
    id: int
    name: str
    type: str
    cnes: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_user_id: Optional[str] = None
    status: str
    professional_count: int = 0
    patient_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Unit Professionals (DEM-031)
# ---------------------------------------------------------------------------

class AllocateProfessional(BaseModel):
    professional_id: int
    role_in_unit: Optional[str] = None
    workload_hours: Optional[int] = Field(None, ge=1, le=168)

class UnitProfessionalOut(BaseModel):
    professional_id: int
    name: str
    specialty: Optional[str] = None
    role_in_unit: Optional[str] = None
    workload_hours: Optional[int] = None
    allocated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Tenant Users (DEM-031)
# ---------------------------------------------------------------------------

class TenantUserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2)
    role: Literal['gestor', 'clinico', 'recepcionista'] = 'clinico'
    unit_id: Optional[int] = None

class TenantUserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Literal['gestor', 'clinico', 'recepcionista']] = None
    unit_id: Optional[int] = None
    status: Optional[Literal['active', 'inactive']] = None

class TenantUserOut(BaseModel):
    id: int
    keycloak_id: Optional[str] = None
    email: str
    name: str
    role: str
    unit_id: Optional[int] = None
    unit_name: Optional[str] = None
    status: str
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
