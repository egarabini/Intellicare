"""Modelo para conceitos de CodeSystem FHIR pré-carregados (suporte ao $expand)."""

import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CodeSystemConcept(Base):
    """Conceitos pré-carregados de CodeSystems FHIR (CID-10, LOINC, TUSS, etc.)

    Alimentado via script de seed ou endpoint de importação.
    Usado pela operação ValueSet/$expand.
    """

    __tablename__ = "fhir_codesystem_concepts"
    __table_args__ = (
        UniqueConstraint("codesystem_url", "code", "tenant_id", name="uq_concept"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    codesystem_url: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(256), nullable=False)
    display: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    definition: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="public")

    def __repr__(self) -> str:
        return f"<CodeSystemConcept {self.codesystem_url}|{self.code}>"
