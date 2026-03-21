"""Pydantic models (request/response) do modulo admin."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional
from uuid import UUID
import re

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


SLUG_PATTERN = re.compile(r'^[a-z0-9_]{3,30}$')


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------

class TenantCreate(BaseModel):
    slug: str
    name: str
    gestor_email: str  # sera o primeiro usuario TENANT_GESTOR

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError("slug deve ter 3-30 chars: [a-z0-9_]")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("name deve ter ao menos 3 caracteres")
        return v.strip()


class TenantStatusUpdate(BaseModel):
    status: Literal["active", "suspended"]


class TenantProvisionRequest(BaseModel):
    """Request para provisionar um novo tenant completo via tenant_provisioner."""
    slug: str
    name: str
    gestor_email: str

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError("slug deve ter 3-30 chars: [a-z0-9_]")
        return v


class TenantConfigItem(BaseModel):
    key: str
    value: str


class TenantConfigResponse(BaseModel):
    tenant_slug: str
    configs: list[TenantConfigItem]


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    status: str
    gestor_email: str | None = None
    suspended_at: datetime | None = None
    suspended_by: str | None = None
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
    page: int
    size: int


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3)
    gestor_email: str | None = None


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    id: int
    actor_id: str
    actor_email: str | None = None
    action: str
    target_type: str
    target_id: str | None = None
    payload: dict | None = None
    created_at: datetime


class AuditLogResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int


# ---------------------------------------------------------------------------
# Usuario (view do Keycloak)
# ---------------------------------------------------------------------------

class TenantUser(BaseModel):
    keycloak_id: str
    username: str
    email: str
    roles: list[str]
    enabled: bool


class TenantUsersResponse(BaseModel):
    tenant_slug: str
    users: list[TenantUser]
    total: int


class UserInviteRequest(BaseModel):
    email: str
    name: str = Field(..., min_length=3)
    role: Literal["TENANT_GESTOR", "CLINICO", "PACIENTE"]


class UserInviteResponse(BaseModel):
    keycloak_id: str
    email: str
    role: str
    invited: bool  # True=criado, False=já existia


# ---------------------------------------------------------------------------
# Servidores
# ---------------------------------------------------------------------------


class ServerCreate(BaseModel):
    name: str
    type: Literal["vps", "dedicated", "cloud"]
    provider: str
    region: str
    hostname: str | None = None
    vcpu: int = Field(gt=0)
    ram_gb: int = Field(gt=0)
    disk_gb: int = Field(gt=0)
    cost_brl: int = Field(ge=0, description="Centavos")
    status: Literal["active", "inactive", "maintenance"] = "active"
    notes: str | None = None


class ServerUpdate(BaseModel):
    name: str | None = None
    type: Literal["vps", "dedicated", "cloud"] | None = None
    provider: str | None = None
    region: str | None = None
    hostname: str | None = None
    vcpu: int | None = Field(default=None, gt=0)
    ram_gb: int | None = Field(default=None, gt=0)
    disk_gb: int | None = Field(default=None, gt=0)
    cost_brl: int | None = Field(default=None, ge=0)
    status: Literal["active", "inactive", "maintenance"] | None = None
    notes: str | None = None


class ServerOut(BaseModel):
    id: int
    name: str
    type: str
    provider: str
    region: str
    hostname: str | None
    vcpu: int
    ram_gb: int
    disk_gb: int
    cost_brl: int
    cost_brl_display: float
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Modulos
# ---------------------------------------------------------------------------


class ModuleStatusUpdate(BaseModel):
    status: Literal["active", "inactive", "dev"]


class TenantModuleUpdate(BaseModel):
    enabled: bool


class ModuleOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str | None
    version: str
    status: str
    tenant_count: int = 0


class TenantModuleOut(BaseModel):
    tenant_slug: str
    module_slug: str
    name: str
    description: str | None
    version: str
    status: str
    enabled: bool
    enabled_at: datetime | None = None


# ---------------------------------------------------------------------------
# Financeiro
# ---------------------------------------------------------------------------


class ExpenseCreate(BaseModel):
    category: Literal["infrastructure", "license", "personnel", "other"]
    description: str
    amount_brl: int = Field(gt=0, description="Centavos")
    expense_date: date
    tenant_slug: str | None = None


class ExpenseUpdate(BaseModel):
    category: Literal["infrastructure", "license", "personnel", "other"] | None = None
    description: str | None = None
    amount_brl: int | None = Field(default=None, gt=0, description="Centavos")
    expense_date: date | None = None
    tenant_slug: str | None = None


class ExpenseOut(BaseModel):
    id: int
    category: str
    description: str
    amount_brl: int
    amount_brl_display: float
    expense_date: date
    tenant_slug: str | None
    created_at: datetime


class InvoiceStatusUpdate(BaseModel):
    status: Literal["paid", "overdue", "cancelled", "pending"]
    paid_at: datetime | None = None


class FinanceiroDashboard(BaseModel):
    receita_mes: float
    despesa_mes: float
    resultado_mes: float
    inadimplencia: float
    historico: list[dict[str, Any]]


class InvoiceOut(BaseModel):
    id: str
    contract_id: str
    tenant_slug: str
    amount_brl: int
    amount_brl_display: float
    due_date: date
    paid_at: datetime | None
    status: str
    period_start: date
    period_end: date
    created_at: datetime


class PagedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    size: int


# ---------------------------------------------------------------------------
# Usuarios administrativos
# ---------------------------------------------------------------------------


class AdminUserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=3)
    role: Literal["admin", "financ", "coordenador"] = "coordenador"
    status: Literal["active", "inactive"] = "active"


class AdminUserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3)
    role: Literal["admin", "financ", "coordenador"] | None = None
    status: Literal["active", "inactive"] | None = None


class AdminUserOut(BaseModel):
    id: int
    keycloak_id: str | None = None
    email: EmailStr
    name: str
    role: str
    status: str
    last_login_at: datetime | None
    created_at: datetime
    temporary_password: str | None = None
