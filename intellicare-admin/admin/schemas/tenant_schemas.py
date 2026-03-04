"""Pydantic request/response schemas for tenant endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ─── Request Schemas ─────────────────────────────────────────

class TenantCreate(BaseModel):
    """Request body for creating a new tenant."""
    nome_fantasia: str = Field(..., min_length=2, max_length=255)
    razao_social: str = Field(..., min_length=2, max_length=255)
    cnpj: str = Field(..., pattern=r"^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$")
    email_admin: EmailStr
    logo_url: Optional[str] = None
    cor_primaria: str = Field(default="#1E88E5", pattern=r"^#[0-9a-fA-F]{6}$")
    cor_secundaria: str = Field(default="#43A047", pattern=r"^#[0-9a-fA-F]{6}$")
    dominio_custom: Optional[str] = None
    plan_name: str = Field(default="trial")


class TenantUpdate(BaseModel):
    """Request body for updating a tenant (all fields optional)."""
    nome_fantasia: Optional[str] = Field(None, max_length=255)
    razao_social: Optional[str] = Field(None, max_length=255)
    email_admin: Optional[EmailStr] = None
    logo_url: Optional[str] = None
    cor_primaria: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    cor_secundaria: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    dominio_custom: Optional[str] = None
    plan_name: Optional[str] = None
    max_users: Optional[int] = Field(None, ge=1)
    max_sms_month: Optional[int] = Field(None, ge=0)


class ModuleUpdate(BaseModel):
    """Request body for enabling/disabling a module."""
    module_name: str
    enabled: bool
    config_json: Optional[dict] = None


# ─── Response Schemas ────────────────────────────────────────

class TenantModuleResponse(BaseModel):
    """Module activation info for a tenant."""
    module_name: str
    enabled: bool
    config_json: dict = {}
    activated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TenantResponse(BaseModel):
    """Full tenant info response."""
    id: UUID
    tenant_id: str
    nome_fantasia: str
    razao_social: str
    cnpj: str
    email_admin: str
    logo_url: Optional[str] = None
    cor_primaria: str = "#1E88E5"
    cor_secundaria: str = "#43A047"
    dominio_custom: Optional[str] = None
    status: str
    provisioned: bool
    max_users: int
    max_sms_month: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    trial_expires_at: Optional[datetime] = None
    modules: list[TenantModuleResponse] = []

    model_config = {"from_attributes": True}


class TenantListResponse(BaseModel):
    """Paginated list of tenants."""
    items: list[TenantResponse]
    total: int
    page: int
    size: int
    pages: int
