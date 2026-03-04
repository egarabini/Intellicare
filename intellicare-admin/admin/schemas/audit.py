from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class AuditLogResponse(BaseModel):
    id: UUID
    actor_id: UUID
    actor_email: str
    actor_role: str
    action: str
    target_type: Optional[str]
    target_id: Optional[UUID]
    payload: Optional[dict]
    result: Optional[str]
    error_message: Optional[str]
    ip: Optional[str]
    user_agent: Optional[str]
    impersonated_as: Optional[UUID]
    reason: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AuditLogList(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    per_page: int
