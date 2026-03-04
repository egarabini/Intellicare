from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class TenantSettingUpdate(BaseModel):
    value: str
    value_type: str = Field(default="string", pattern="^(string|number|boolean|json)$")

class TenantSettingResponse(BaseModel):
    id: UUID
    category: str
    key: str
    value: Optional[str] = None
    value_type: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True

class TenantSettingListResponse(BaseModel):
    settings: List[TenantSettingResponse]
    total: int
