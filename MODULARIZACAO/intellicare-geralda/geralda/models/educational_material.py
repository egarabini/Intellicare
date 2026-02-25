"""Modelo SQLAlchemy para EducationalMaterial (Materiais Educativos)."""

from datetime import datetime, UTC
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from geralda.database.base import Base


class EducationalMaterial(Base):
    """
    Material educacional para paciente.

    Tabela: educational_materials
    """

    __tablename__ = "educational_materials"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # Foreign Keys
    plan_id: Mapped[UUID] = mapped_column(index=True)  # FK para care_plans
    patient_id: Mapped[str] = mapped_column(String(200), index=True)

    # Content
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))

    # Clinical Codes (for filtering - e.g., ICD-10 codes)
    condition_codes: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    # Language
    language: Mapped[str] = mapped_column(String(10), default="pt-BR")

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    # care_plan = relationship("CarePlan", back_populates="educational_materials")

    # Indexes
    __table_args__ = (
        Index("idx_educational_materials_plan_id", "plan_id"),
        Index("idx_educational_materials_patient_id", "patient_id"),
    )

    def __repr__(self) -> str:
        return f"<EducationalMaterial(id={self.id}, title={self.title})>"

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário (compatibilidade com API)."""
        return {
            "id": str(self.id),
            "plan_id": str(self.plan_id),
            "patient_id": self.patient_id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "condition_codes": self.condition_codes,
            "language": self.language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
