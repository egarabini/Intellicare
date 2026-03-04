from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class RoleBase(BaseModel):
    name: str = Field(..., max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    permissions: List[str] = []

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    permissions: Optional[List[str]] = None

class RoleResponse(RoleBase):
    id: UUID
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total: int

class UserRoleCreate(BaseModel):
    role_id: UUID
