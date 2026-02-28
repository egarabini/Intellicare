"""Model ORM — Sector."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import UUID, Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from gestor.models.base import Base


class Sector(Base):
    __tablename__ = "sectors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=True)   # "UTI", "Enfermaria", "Ambulatório", "Administração"
    parent_id = Column(UUID(as_uuid=True), ForeignKey("sectors.id"), nullable=True)
    responsavel_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    users = relationship("TenantUser", back_populates="sector", foreign_keys="TenantUser.sector_id")
    children = relationship("Sector", backref="parent", foreign_keys=[parent_id])
