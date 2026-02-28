"""Model ORM — TenantUser.

O schema é definido via SET search_path (TenantAwareSessionFactory).
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from gestor.models.base import Base


class TenantUser(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_user_id = Column(String(255), unique=True, nullable=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    cpf = Column(String(14), unique=True, nullable=True)
    cargo = Column(String(100), nullable=True)      # "Médico", "Enfermeiro"
    conselho = Column(String(50), nullable=True)    # "CRM-SP 123456"
    sector_id = Column(UUID(as_uuid=True), ForeignKey("sectors.id"), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    invited_at = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    sector = relationship("Sector", back_populates="users", foreign_keys=[sector_id])
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
