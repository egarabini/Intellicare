"""Schemas Pydantic para Role e UserRole."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from gestor.permissions import validate_permissions


class RoleCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    permissions: list[str] = []

    @field_validator("permissions")
    @classmethod
    def validate_perms(cls, v: list[str]) -> list[str]:
        invalid = validate_permissions(v)
        if invalid:
            raise ValueError(f"Permissões inválidas: {invalid}")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError("Nome da role deve ser alfanumérico (underscores permitidos)")
        return v.lower()


class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    permissions: Optional[list[str]] = None

    @field_validator("permissions")
    @classmethod
    def validate_perms(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        invalid = validate_permissions(v)
        if invalid:
            raise ValueError(f"Permissões inválidas: {invalid}")
        return v


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: Optional[str] = None
    is_system: bool
    permissions: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserRoleAssign(BaseModel):
    role_id: uuid.UUID
