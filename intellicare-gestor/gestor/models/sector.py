import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from gestor.db import Base

class Sector(Base):
    __tablename__ = "sectors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # "UTI", "Enfermaria", etc.
    parent_id = Column(UUID(as_uuid=True), ForeignKey("sectors.id"), nullable=True)  # Hierarquia
    responsavel_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
