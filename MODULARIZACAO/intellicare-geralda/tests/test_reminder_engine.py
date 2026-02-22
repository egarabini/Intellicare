"""Testes do ReminderEngine."""

from datetime import date

from geralda.engine.models import ReminderFrequency, ReminderStatus
from geralda.engine.reminder_engine import ReminderEngine


class TestCreateReminder:
    def test_create_daily(self, reminder_engine):
        r = reminder_engine.create_reminder(
            patient_id="p1",
            title="Remedio",
            message="Tomar Losartana",
            reminder_time="08:00",
        )
        assert r.id is not None
        assert r.frequency == ReminderFrequency.DAILY
        assert r.time == "08:00"
        assert r.status == ReminderStatus.ACTIVE

    def test_create_weekly(self, reminder_engine):
        r = reminder_engine.create_reminder(
            patient_id="p1",
            title="Consulta",
            message="Fisioterapia",
            reminder_time="14:00",
            frequency=ReminderFrequency.WEEKLY,
            days_of_week=[1, 3],
        )
        assert r.frequency == ReminderFrequency.WEEKLY
        assert r.days_of_week == [1, 3]

    def test_create_with_dates(self, reminder_engine):
        r = reminder_engine.create_reminder(
            patient_id="p1",
            title="Tratamento",
            message="Sessao de dialise",
            reminder_time="07:00",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
        )
        assert r.start_date == date(2026, 1, 1)
        assert r.end_date == date(2026, 6, 30)


class TestGetReminders:
    def test_get_by_id(self, reminder_engine, sample_reminders):
        r = reminder_engine.get_reminder(sample_reminders[0].id)
        assert r is not None
        assert r.title == "Medicamento"

    def test_get_nonexistent(self, reminder_engine):
        assert reminder_engine.get_reminder("nope") is None

    def test_get_patient_reminders(self, reminder_engine, sample_reminders):
        reminders = reminder_engine.get_patient_reminders("pac-001")
        assert len(reminders) == 3

    def test_get_patient_reminders_empty(self, reminder_engine):
        assert reminder_engine.get_patient_reminders("unknown") == []

    def test_filter_by_status(self, reminder_engine, sample_reminders):
        reminder_engine.pause_reminder(sample_reminders[0].id)
        active = reminder_engine.get_patient_reminders("pac-001", status=ReminderStatus.ACTIVE)
        paused = reminder_engine.get_patient_reminders("pac-001", status=ReminderStatus.PAUSED)
        assert len(active) == 2
        assert len(paused) == 1


class TestDueReminders:
    def test_due_today(self, reminder_engine, sample_reminders):
        due = reminder_engine.get_due_reminders("pac-001")
        # All 3 should be due: 2 daily + 1 once (not yet sent)
        assert len(due) == 3

    def test_due_empty_patient(self, reminder_engine):
        assert reminder_engine.get_due_reminders("unknown") == []


class TestReminderActions:
    def test_pause(self, reminder_engine, sample_reminders):
        r = reminder_engine.pause_reminder(sample_reminders[0].id)
        assert r is not None
        assert r.status == ReminderStatus.PAUSED

    def test_pause_already_paused(self, reminder_engine, sample_reminders):
        reminder_engine.pause_reminder(sample_reminders[0].id)
        assert reminder_engine.pause_reminder(sample_reminders[0].id) is None

    def test_resume(self, reminder_engine, sample_reminders):
        reminder_engine.pause_reminder(sample_reminders[0].id)
        r = reminder_engine.resume_reminder(sample_reminders[0].id)
        assert r is not None
        assert r.status == ReminderStatus.ACTIVE

    def test_resume_not_paused(self, reminder_engine, sample_reminders):
        assert reminder_engine.resume_reminder(sample_reminders[0].id) is None

    def test_cancel(self, reminder_engine, sample_reminders):
        r = reminder_engine.cancel_reminder(sample_reminders[0].id)
        assert r is not None
        assert r.status == ReminderStatus.CANCELLED

    def test_cancel_already_cancelled(self, reminder_engine, sample_reminders):
        reminder_engine.cancel_reminder(sample_reminders[0].id)
        assert reminder_engine.cancel_reminder(sample_reminders[0].id) is None

    def test_cancel_nonexistent(self, reminder_engine):
        assert reminder_engine.cancel_reminder("nope") is None


class TestDailySchedule:
    def test_schedule_sorted(self, reminder_engine, sample_reminders):
        schedule = reminder_engine.generate_daily_schedule("pac-001")
        assert len(schedule) == 3
        # Should be sorted by time: 06:30, 08:00, 14:00
        assert schedule[0]["time"] == "06:30"
        assert schedule[1]["time"] == "08:00"
        assert schedule[2]["time"] == "14:00"

    def test_schedule_empty(self, reminder_engine):
        schedule = reminder_engine.generate_daily_schedule("unknown")
        assert schedule == []


class TestProperties:
    def test_total_reminders(self, reminder_engine, sample_reminders):
        assert reminder_engine.total_reminders == 3

    def test_active_reminders(self, reminder_engine, sample_reminders):
        assert reminder_engine.active_reminders == 3
        reminder_engine.cancel_reminder(sample_reminders[0].id)
        assert reminder_engine.active_reminders == 2
