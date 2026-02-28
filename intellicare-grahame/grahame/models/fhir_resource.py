"""Modelo de armazenamento de recursos FHIR R4."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .base import Base


class FHIRResource(Base):
    """Armazenamento genérico de recursos FHIR R4.

    Usa uma coluna JSON para armazenar o recurso completo, garantindo
    flexibilidade para qualquer tipo de recurso FHIR sem necessidade de
    migrações por novo tipo.
    """

    __tablename__ = "fhir_resources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fhir_id: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    resource: Mapped[dict] = mapped_column(JSON, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Multi-tenancy (nullable = single-tenant compat)
    tenant_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<FHIRResource {self.resource_type}/{self.fhir_id}>"
