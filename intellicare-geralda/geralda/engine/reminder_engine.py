"""Reminder engine com suporte multi-tenant."""

import uuid
from datetime import date
from typing import Optional, Any

from geralda.engine.models import (
    Reminder,
    ReminderFrequency,
    ReminderStatus,
)


class ReminderEngine:
    """Manages patient reminders with scheduling and notification logic, isolated per tenant."""

    def __init__(self, default_advance_minutes: int = 30):
        self._tenant_reminders: dict[str, dict[str, Reminder]] = {}
        self._tenant_by_patient: dict[str, dict[str, list[str]]] = {}
        self.default_advance_minutes = default_advance_minutes

    def _gen_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _get_tenant(self, ctx: Any) -> str:
        if ctx and hasattr(ctx, "tenant_id"):
            return ctx.tenant_id
        return "default"

    def _get_reminders(self, tenant: str) -> dict[str, Reminder]:
        return self._tenant_reminders.setdefault(tenant, {})

    def _get_by_patient(self, tenant: str) -> dict[str, list[str]]:
        return self._tenant_by_patient.setdefault(tenant, {})

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
        ctx: Any = None,
    ) -> Reminder:
        tenant = self._get_tenant(ctx)
        reminders = self._get_reminders(tenant)
        by_patient = self._get_by_patient(tenant)

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
        reminders[reminder.id] = reminder
        by_patient.setdefault(patient_id, []).append(reminder.id)
        return reminder

    def get_reminder(self, reminder_id: str, ctx: Any = None) -> Optional[Reminder]:
        tenant = self._get_tenant(ctx)
        return self._get_reminders(tenant).get(reminder_id)

    def get_patient_reminders(
        self,
        patient_id: str,
        status: Optional[ReminderStatus] = None,
        ctx: Any = None,
    ) -> list[Reminder]:
        tenant = self._get_tenant(ctx)
        reminders_dict = self._get_reminders(tenant)
        by_patient = self._get_by_patient(tenant)

        ids = by_patient.get(patient_id, [])
        reminders_list = [reminders_dict[rid] for rid in ids if rid in reminders_dict]
        if status:
            reminders_list = [r for r in reminders_list if r.status == status]
        return reminders_list

    def get_due_reminders(self, patient_id: str, today: Optional[date] = None, ctx: Any = None) -> list[Reminder]:
        reminders = self.get_patient_reminders(patient_id, status=ReminderStatus.ACTIVE, ctx=ctx)
        return [r for r in reminders if r.is_due_today(today)]

    def pause_reminder(self, reminder_id: str, ctx: Any = None) -> Optional[Reminder]:
        tenant = self._get_tenant(ctx)
        reminder = self._get_reminders(tenant).get(reminder_id)
        if reminder and reminder.status == ReminderStatus.ACTIVE:
            reminder.status = ReminderStatus.PAUSED
            return reminder
        return None

    def resume_reminder(self, reminder_id: str, ctx: Any = None) -> Optional[Reminder]:
        tenant = self._get_tenant(ctx)
        reminder = self._get_reminders(tenant).get(reminder_id)
        if reminder and reminder.status == ReminderStatus.PAUSED:
            reminder.status = ReminderStatus.ACTIVE
            return reminder
        return None

    def cancel_reminder(self, reminder_id: str, ctx: Any = None) -> Optional[Reminder]:
        tenant = self._get_tenant(ctx)
        reminder = self._get_reminders(tenant).get(reminder_id)
        if reminder and reminder.status in (ReminderStatus.ACTIVE, ReminderStatus.PAUSED):
            reminder.status = ReminderStatus.CANCELLED
            return reminder
        return None

    def generate_daily_schedule(self, patient_id: str, today: Optional[date] = None, ctx: Any = None) -> list[dict]:
        due = self.get_due_reminders(patient_id, today, ctx=ctx)
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
        return sum(len(d) for d in self._tenant_reminders.values())

    @property
    def active_reminders(self) -> int:
        return sum(
            sum(1 for r in d.values() if r.status == ReminderStatus.ACTIVE)
            for d in self._tenant_reminders.values()
        )
