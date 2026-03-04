"""Modelo SQLAlchemy para CarePlan (Plano de Cuidado)."""

from datetime import datetime, UTC
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from geralda.database.base import Base


class CarePlan(Base):
    """
    Plano de cuidado do paciente.

    Tabela: care_plans
    """

    __tablename__ = "care_plans"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # Patient Information
    patient_id: Mapped[str] = mapped_column(String(200), index=True)
    patient_name: Mapped[str] = mapped_column(String(200))

    # Clinical Data (JSON — JSONB on PostgreSQL, JSON on SQLite)
    conditions: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    goals: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Deactivation
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships (lazy loaded)
    # tasks = relationship("CareTask", back_populates="care_plan", cascade="all, delete-orphan")
    # reminders = relationship("Reminder", back_populates="care_plan", cascade="all, delete-orphan")
    # educational_materials = relationship("EducationalMaterial", back_populates="care_plan", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_care_plans_patient_id", "patient_id"),
        Index("idx_care_plans_active", "active"),
    )

    def __repr__(self) -> str:
        return f"<CarePlan(id={self.id}, patient_id={self.patient_id}, active={self.active})>"

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário (compatibilidade com API)."""
        return {
            "id": str(self.id),
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "conditions": self.conditions,
            "goals": self.goals,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deactivated_at": self.deactivated_at.isoformat() if self.deactivated_at else None,
            "deactivation_reason": self.deactivation_reason,
        }

    def summary(self) -> dict[str, int]:
        """
        Resumo do plano.

        Returns:
            Dict com contagem de tarefas por status.
        """
        # This will be populated after relationships are set up
        return {
            "total_tasks": 0,
            "pending_tasks": 0,
            "completed_tasks": 0,
            "overdue_tasks": 0,
        }
