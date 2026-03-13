from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID


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
