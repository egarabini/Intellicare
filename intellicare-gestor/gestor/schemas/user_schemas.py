from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class TenantUserBase(BaseModel):
    nome: str
    email: EmailStr
    cpf: Optional[str] = Field(None, max_length=14)
    cargo: Optional[str] = None
    conselho: Optional[str] = None
    sector_id: Optional[UUID] = None
    active: bool = True

class TenantUserCreate(TenantUserBase):
    pass

class TenantUserUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = Field(None, max_length=14)
    cargo: Optional[str] = None
    conselho: Optional[str] = None
    sector_id: Optional[UUID] = None
    active: Optional[bool] = None

class TenantUserResponse(TenantUserBase):
    id: UUID
    keycloak_user_id: Optional[str] = None
    invited_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TenantUserListResponse(BaseModel):
    users: List[TenantUserResponse]
    total: int
