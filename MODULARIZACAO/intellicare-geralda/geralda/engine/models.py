"""Modelos de dados do Geralda."""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    OVERDUE = "overdue"


class TaskCategory(str, Enum):
    MEDICATION = "medication"
    EXERCISE = "exercise"
    DIET = "diet"
    EXAM = "exam"
    APPOINTMENT = "appointment"
    MONITORING = "monitoring"
    EDUCATION = "education"
    OTHER = "other"


class ReminderFrequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReminderStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class CareTask:
    """Tarefa de cuidado diario do paciente."""

    id: str
    patient_id: str
    title: str
    description: str
    category: TaskCategory
    status: TaskStatus = TaskStatus.PENDING
    due_date: date | None = None
    due_time: str | None = None  # HH:MM
    completed_at: datetime | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "status": self.status.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "due_time": self.due_time,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "notes": self.notes,
        }


@dataclass
class CarePlan:
    """Plano de cuidado do paciente."""

    id: str
    patient_id: str
    patient_name: str
    conditions: list[str]
    goals: list[str]
    tasks: list[CareTask] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "conditions": self.conditions,
            "goals": self.goals,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "active": self.active,
            "summary": self.summary(),
        }

    def summary(self) -> dict[str, int]:
        """Resumo de tarefas por status."""
        counts: dict[str, int] = {}
        for t in self.tasks:
            counts[t.status.value] = counts.get(t.status.value, 0) + 1
        return counts


@dataclass
class Reminder:
    """Lembrete para o paciente."""

    id: str
    patient_id: str
    title: str
    message: str
    frequency: ReminderFrequency
    time: str  # HH:MM
    status: ReminderStatus = ReminderStatus.ACTIVE
    start_date: date | None = None
    end_date: date | None = None
    days_of_week: list[int] = field(default_factory=list)  # 0=Mon, 6=Sun
    last_sent: datetime | None = None
    send_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "title": self.title,
            "message": self.message,
            "frequency": self.frequency.value,
            "time": self.time,
            "status": self.status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "days_of_week": self.days_of_week,
            "last_sent": self.last_sent.isoformat() if self.last_sent else None,
            "send_count": self.send_count,
        }

    def is_due_today(self, today: date | None = None) -> bool:
        """Verifica se o lembrete deve ser enviado hoje."""
        if self.status != ReminderStatus.ACTIVE:
            return False
        today = today or date.today()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        if self.frequency == ReminderFrequency.ONCE:
            return self.send_count == 0
        if self.frequency == ReminderFrequency.DAILY:
            return True
        if self.frequency == ReminderFrequency.WEEKLY:
            return today.weekday() in self.days_of_week
        if self.frequency == ReminderFrequency.MONTHLY:
            return today.day == 1 or (self.start_date and today.day == self.start_date.day)
        return False


@dataclass
class EducationContent:
    """Material educativo em saude."""

    id: str
    condition_code: str
    condition_name: str
    title: str
    content: str
    language: str = "pt-BR"
    reading_level: str = "basic"  # basic, intermediate, advanced
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "condition_code": self.condition_code,
            "condition_name": self.condition_name,
            "title": self.title,
            "content": self.content,
            "language": self.language,
            "reading_level": self.reading_level,
            "tags": self.tags,
        }


@dataclass
class PatientAdherence:
    """Resumo de adesao do paciente."""

    patient_id: str
    total_tasks: int
    completed_tasks: int
    skipped_tasks: int
    overdue_tasks: int
    adherence_rate: float  # 0.0 - 1.0
    active_reminders: int
    conditions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "skipped_tasks": self.skipped_tasks,
            "overdue_tasks": self.overdue_tasks,
            "adherence_rate": round(self.adherence_rate, 2),
            "adherence_percent": f"{self.adherence_rate * 100:.0f}%",
            "active_reminders": self.active_reminders,
            "conditions": self.conditions,
        }
