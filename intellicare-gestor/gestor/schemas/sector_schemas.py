"""Schemas Pydantic para Sector."""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

SectorType = Literal["UTI", "Enfermaria", "Ambulatório", "Administração", "Outro"]


class SectorCreate(BaseModel):
    name: str
    type: Optional[SectorType] = None
    parent_id: Optional[uuid.UUID] = None
    responsavel_id: Optional[uuid.UUID] = None


class SectorUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[SectorType] = None
    parent_id: Optional[uuid.UUID] = None
    responsavel_id: Optional[uuid.UUID] = None
    active: Optional[bool] = None


class SectorResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    responsavel_id: Optional[uuid.UUID] = None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
