from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class SectorBase(BaseModel):
    name: str = Field(..., max_length=255)
    type: Optional[str] = Field(None, max_length=50) # "UTI", "Enfermaria", etc.
    parent_id: Optional[UUID] = None
    responsavel_id: Optional[UUID] = None
    active: bool = True

class SectorCreate(SectorBase):
    pass

class SectorUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    type: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[UUID] = None
    responsavel_id: Optional[UUID] = None
    active: Optional[bool] = None

class SectorResponse(SectorBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class SectorListResponse(BaseModel):
    sectors: List[SectorResponse]
    total: int
