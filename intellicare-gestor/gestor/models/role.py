import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from gestor.models.base import Base

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255))
    is_system = Column(Boolean, default=False)  # True = seed role, não pode deletar
    permissions = Column(JSON, default=list)  # ["oswaldo.classificar", "florence.ver"]
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    assigned_by = Column(UUID(as_uuid=True))  # Quem atribuiu
