"""Modelo SQLAlchemy para Reminder (Lembretes)."""

from datetime import datetime, UTC
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from geralda.database.base import Base


class ReminderStatus(str, Enum):
    """Status de um lembrete."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Reminder(Base):
    """
    Lembrete para paciente ou profissional.

    Tabela: reminders
    """

    __tablename__ = "reminders"

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    # Foreign Keys
    plan_id: Mapped[UUID] = mapped_column(index=True)  # FK para care_plans
    patient_id: Mapped[str] = mapped_column(String(200), index=True)
    task_id: Mapped[UUID | None] = mapped_column(index=True)  # FK para care_tasks (nullable)

    # Content
    message: Mapped[str] = mapped_column(Text)

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Channel
    channel: Mapped[str] = mapped_column(String(50))  # "email", "sms", "whatsapp", "push"

    # Status
    status: Mapped[ReminderStatus] = mapped_column(
        SQLEnum(ReminderStatus),
        default=ReminderStatus.PENDING,
    )

    # Relationships
    # care_plan = relationship("CarePlan", back_populates="reminders")
    # care_task = relationship("CareTask", back_populates="reminders")

    # Indexes
    __table_args__ = (
        Index("idx_reminders_patient_id", "patient_id"),
        Index("idx_reminders_scheduled_at", "scheduled_at"),
    )

    def __repr__(self) -> str:
        return f"<Reminder(id={self.id}, patient_id={self.patient_id}, status={self.status})>"

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário (compatibilidade com API)."""
        return {
            "id": str(self.id),
            "plan_id": str(self.plan_id),
            "patient_id": self.patient_id,
            "task_id": str(self.task_id) if self.task_id else None,
            "message": self.message,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "channel": self.channel,
            "status": self.status.value,
        }

    def is_ready_to_send(self) -> bool:
        """Verifica se o lembrete está pronto para ser enviado."""
        return (
            self.status == ReminderStatus.PENDING
            and self.scheduled_at <= datetime.now(UTC)
        )
