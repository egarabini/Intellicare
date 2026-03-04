import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from gestor.db import Base

class TenantSetting(Base):
    __tablename__ = "settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False)  # "branding", "comunicacao", "modulos"
    key = Column(String(255), nullable=False, unique=True)
    value = Column(Text)
    value_type = Column(String(20), default="string")  # string, number, boolean, json
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(UUID(as_uuid=True), nullable=True)
