import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from gestor.db import Base

class TenantUser(Base):
    __tablename__ = "users"
    # Schema será dinâmico por tenant definido na engine via search_path ou TenantContext
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_user_id = Column(String(255), unique=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    cpf = Column(String(14), unique=True)
    cargo = Column(String(100))  # "Médico", "Enfermeiro", etc.
    conselho = Column(String(50))  # "CRM-SP 123456"
    sector_id = Column(UUID(as_uuid=True), ForeignKey("sectors.id"), nullable=True)
    active = Column(Boolean, default=True)
    invited_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
