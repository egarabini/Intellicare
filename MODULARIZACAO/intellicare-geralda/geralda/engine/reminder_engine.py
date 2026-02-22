"""Reminder engine — manages scheduled reminders and notification dispatch."""

import uuid
from datetime import date
from typing import Optional

from geralda.engine.models import (
    Reminder,
    ReminderFrequency,
    ReminderStatus,
)


class ReminderEngine:
    """Manages patient reminders with scheduling and notification logic."""

    def __init__(self, default_advance_minutes: int = 30):
        self._reminders: dict[str, Reminder] = {}
        self._by_patient: dict[str, list[str]] = {}
        self.default_advance_minutes = default_advance_minutes

    def _gen_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def create_reminder(
        self,
        patient_id: str,
        title: str,
        message: str,
        reminder_time: str,  # HH:MM
        frequency: ReminderFrequency = ReminderFrequency.DAILY,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days_of_week: Optional[list[int]] = None,
        category: str = "general",
    ) -> Reminder:
        """Create a new reminder for a patient."""
        reminder = Reminder(
            id=self._gen_id(),
            patient_id=patient_id,
            title=title,
            message=message,
            frequency=frequency,
            time=reminder_time,
            start_date=start_date or date.today(),
            end_date=end_date,
            days_of_week=days_of_week or [],
        )
        self._reminders[reminder.id] = reminder
        self._by_patient.setdefault(patient_id, []).append(reminder.id)
        return reminder

    def get_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """Get a specific reminder by ID."""
        return self._reminders.get(reminder_id)

    def get_patient_reminders(
        self,
        patient_id: str,
        status: Optional[ReminderStatus] = None,
    ) -> list[Reminder]:
        """Get all reminders for a patient, optionally filtered by status."""
        ids = self._by_patient.get(patient_id, [])
        reminders = [self._reminders[rid] for rid in ids if rid in self._reminders]
        if status:
            reminders = [r for r in reminders if r.status == status]
        return reminders

    def get_due_reminders(self, patient_id: str, today: Optional[date] = None) -> list[Reminder]:
        """Get all reminders due today for a patient."""
        reminders = self.get_patient_reminders(patient_id, status=ReminderStatus.ACTIVE)
        return [r for r in reminders if r.is_due_today(today)]

    def pause_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """Pause an active reminder."""
        reminder = self._reminders.get(reminder_id)
        if reminder and reminder.status == ReminderStatus.ACTIVE:
            reminder.status = ReminderStatus.PAUSED
            return reminder
        return None

    def resume_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """Resume a paused reminder."""
        reminder = self._reminders.get(reminder_id)
        if reminder and reminder.status == ReminderStatus.PAUSED:
            reminder.status = ReminderStatus.ACTIVE
            return reminder
        return None

    def cancel_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """Cancel a reminder."""
        reminder = self._reminders.get(reminder_id)
        if reminder and reminder.status in (ReminderStatus.ACTIVE, ReminderStatus.PAUSED):
            reminder.status = ReminderStatus.CANCELLED
            return reminder
        return None

    def generate_daily_schedule(self, patient_id: str, today: Optional[date] = None) -> list[dict]:
        """Generate today's schedule for a patient, sorted by time."""
        due = self.get_due_reminders(patient_id, today)
        schedule = []
        for r in sorted(due, key=lambda x: x.time):
            schedule.append(
                {
                    "id": r.id,
                    "time": r.time,
                    "title": r.title,
                    "message": r.message,
                    "frequency": r.frequency.value,
                }
            )
        return schedule

    @property
    def total_reminders(self) -> int:
        return len(self._reminders)

    @property
    def active_reminders(self) -> int:
        return sum(1 for r in self._reminders.values() if r.status == ReminderStatus.ACTIVE)
