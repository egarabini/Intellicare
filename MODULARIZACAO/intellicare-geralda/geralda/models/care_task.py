"""Modelo SQLAlchemy para CareTask (Tarefas de Cuidado)."""

from datetime import date, datetime, UTC
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Enum as SQLEnum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from geralda.database.base import Base


class TaskStatus(str, Enum):
    """Status de uma tarefa."""

    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    OVERDUE = "overdue"


class TaskCategory(str, Enum):
    """Categoria de uma tarefa."""

    MEDICATION = "medication"
    EXERCISE = "exercise"
    DIET = "diet"
    EXAM = "exam"
    APPOINTMENT = "appointment"
    MONITORING = "monitoring"
    EDUCATION = "education"
    OTHER = "other"


class CareTask(Base):
    """
    Tarefa de cuidado diário do paciente.

    Tabela: care_tasks
    """

    __tablename__ = "care_tasks"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # Foreign Keys
    plan_id: Mapped[UUID] = mapped_column(index=True)  # FK para care_plans
    patient_id: Mapped[str] = mapped_column(String(200), index=True)

    # Task Details
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[TaskCategory] = mapped_column(SQLEnum(TaskCategory))
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        default=TaskStatus.PENDING,
        index=True,
    )

    # Scheduling
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    due_time: Mapped[str | None] = mapped_column(String(5))  # HH:MM format

    # Completion
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_by: Mapped[str | None] = mapped_column(String(200))

    # Additional Info
    notes: Mapped[str] = mapped_column(Text, default="")

    # Recurrence (for future implementation)
    recurrence_rule: Mapped[str | None] = mapped_column(String(100))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    # care_plan = relationship("CarePlan", back_populates="tasks")

    # Indexes
    __table_args__ = (
        Index("idx_care_tasks_plan_id", "plan_id"),
        Index("idx_care_tasks_patient_id", "patient_id"),
        Index("idx_care_tasks_status", "status"),
        Index("idx_care_tasks_due_date", "due_date"),
    )

    def __repr__(self) -> str:
        return f"<CareTask(id={self.id}, title={self.title}, status={self.status})>"

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário (compatibilidade com API)."""
        return {
            "id": str(self.id),
            "plan_id": str(self.plan_id),
            "patient_id": self.patient_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "status": self.status.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "due_time": self.due_time,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completed_by": self.completed_by,
            "notes": self.notes,
            "recurrence_rule": self.recurrence_rule,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def is_overdue(self) -> bool:
        """Verifica se a tarefa está atrasada."""
        if self.due_date and self.status == TaskStatus.PENDING:
            return date.today() > self.due_date
        return False
