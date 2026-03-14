"""Pydantic models (request/response) do modulo admin."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
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


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
    page: int
    size: int


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=3)


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

