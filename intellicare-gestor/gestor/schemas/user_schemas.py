"""Schemas Pydantic para TenantUser."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    conselho: Optional[str] = None
    sector_id: Optional[uuid.UUID] = None

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) != 11:
            raise ValueError("CPF deve ter 11 dígitos")
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


class UserUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    conselho: Optional[str] = None
    sector_id: Optional[uuid.UUID] = None
    active: Optional[bool] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    nome: str
    email: str
    cpf: Optional[str] = None
    cargo: Optional[str] = None
    conselho: Optional[str] = None
    sector_id: Optional[uuid.UUID] = None
    active: bool
    invited_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
