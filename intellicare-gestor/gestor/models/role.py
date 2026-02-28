"""Models ORM — Role e UserRole."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from gestor.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)  # True = seed, não deletar
    permissions = Column(JSON, default=list, nullable=False)    # ["oswaldo.classificar", ...]
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    assigned_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    assigned_by = Column(UUID(as_uuid=True), nullable=True)

    user = relationship("TenantUser", back_populates="roles")
    role = relationship("Role", back_populates="user_roles")
