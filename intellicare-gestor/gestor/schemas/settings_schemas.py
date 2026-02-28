"""Schemas Pydantic para TenantSetting."""

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel

ValueType = Literal["string", "number", "boolean", "json"]


class SettingUpdate(BaseModel):
    value: str
    value_type: Optional[ValueType] = None


class SettingResponse(BaseModel):
    id: uuid.UUID
    category: str
    key: str
    value: Optional[str] = None
    value_type: str
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SettingsBulkUpdate(BaseModel):
    settings: dict[str, str]  # key → value
