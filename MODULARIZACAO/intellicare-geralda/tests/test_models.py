"""Testes dos modelos de dados do Geralda."""

from datetime import date, datetime

from geralda.engine.models import (
    CarePlan,
    CareTask,
    EducationContent,
    PatientAdherence,
    Reminder,
    ReminderFrequency,
    ReminderStatus,
    TaskCategory,
    TaskStatus,
)


class TestCareTask:
    def test_to_dict(self):
        task = CareTask(
            id="t1",
            patient_id="p1",
            title="Tomar remedio",
            description="Tomar remedio X",
            category=TaskCategory.MEDICATION,
        )
        d = task.to_dict()
        assert d["id"] == "t1"
        assert d["category"] == "medication"
        assert d["status"] == "pending"
        assert d["completed_at"] is None

    def test_to_dict_completed(self):
        now = datetime.now()
        task = CareTask(
            id="t2",
            patient_id="p1",
            title="Exame",
            description="Exame de sangue",
            category=TaskCategory.EXAM,
            status=TaskStatus.COMPLETED,
            completed_at=now,
            due_date=date(2026, 3, 1),
        )
        d = task.to_dict()
        assert d["status"] == "completed"
        assert d["completed_at"] is not None
        assert d["due_date"] == "2026-03-01"

    def test_default_status_is_pending(self):
        task = CareTask(
            id="t3", patient_id="p1", title="X",
            description="Y", category=TaskCategory.OTHER,
        )
        assert task.status == TaskStatus.PENDING


class TestCarePlan:
    def test_summary_empty(self):
        plan = CarePlan(
            id="pl1", patient_id="p1", patient_name="Joao",
            conditions=["N18"], goals=["Meta 1"],
        )
        assert plan.summary() == {}

    def test_summary_with_tasks(self):
        plan = CarePlan(
            id="pl2", patient_id="p1", patient_name="Joao",
            conditions=["N18"], goals=[],
            tasks=[
                CareTask(id="t1", patient_id="p1", title="A", description="A", category=TaskCategory.MEDICATION),
                CareTask(id="t2", patient_id="p1", title="B", description="B", category=TaskCategory.EXERCISE, status=TaskStatus.COMPLETED),
                CareTask(id="t3", patient_id="p1", title="C", description="C", category=TaskCategory.DIET, status=TaskStatus.COMPLETED),
            ],
        )
        summary = plan.summary()
        assert summary["pending"] == 1
        assert summary["completed"] == 2

    def test_to_dict_includes_summary(self):
        plan = CarePlan(
            id="pl3", patient_id="p1", patient_name="Joao",
            conditions=["E11"], goals=["Controlar glicose"],
        )
        d = plan.to_dict()
        assert "summary" in d
        assert d["conditions"] == ["E11"]
        assert d["active"] is True


class TestReminder:
    def test_to_dict(self):
        r = Reminder(
            id="r1", patient_id="p1", title="Remedio",
            message="Tomar X", frequency=ReminderFrequency.DAILY,
            time="08:00",
        )
        d = r.to_dict()
        assert d["frequency"] == "daily"
        assert d["time"] == "08:00"
        assert d["status"] == "active"

    def test_is_due_today_daily(self):
        r = Reminder(
            id="r1", patient_id="p1", title="X",
            message="Y", frequency=ReminderFrequency.DAILY,
            time="08:00", start_date=date(2026, 1, 1),
        )
        assert r.is_due_today(date(2026, 2, 11)) is True

    def test_is_due_today_before_start(self):
        r = Reminder(
            id="r2", patient_id="p1", title="X",
            message="Y", frequency=ReminderFrequency.DAILY,
            time="08:00", start_date=date(2026, 3, 1),
        )
        assert r.is_due_today(date(2026, 2, 11)) is False

    def test_is_due_today_after_end(self):
        r = Reminder(
            id="r3", patient_id="p1", title="X",
            message="Y", frequency=ReminderFrequency.DAILY,
            time="08:00", start_date=date(2026, 1, 1),
            end_date=date(2026, 2, 1),
        )
        assert r.is_due_today(date(2026, 2, 11)) is False

    def test_is_due_today_once_not_sent(self):
        r = Reminder(
            id="r4", patient_id="p1", title="X",
            message="Y", frequency=ReminderFrequency.ONCE,
            time="14:00", send_count=0,
        )
        assert r.is_due_today() is True

    def test_is_due_today_once_already_sent(self):
        r = Reminder(
            id="r5", patient_id="p1", title="X",
            message="Y", frequency=ReminderFrequency.ONCE,
            time="14:00", send_count=1,
        )
        assert r.is_due_today() is False

    def test_is_due_today_weekly_correct_day(self):
        # 2026-02-11 is a Wednesday (weekday=2)
        r = Reminder(
            id="r6", patient_id="p1", title="X",
            message="Y", frequency=ReminderFrequency.WEEKLY,
            time="10:00", days_of_week=[2],  # Wednesday
        )
        assert r.is_due_today(date(2026, 2, 11)) is True

    def test_is_due_today_weekly_wrong_day(self):
        r = Reminder(
            id="r7", patient_id="p1", title="X",
            message="Y", frequency=ReminderFrequency.WEEKLY,
            time="10:00", days_of_week=[0, 4],  # Mon, Fri
        )
        assert r.is_due_today(date(2026, 2, 11)) is False  # Wed

    def test_is_due_today_paused(self):
        r = Reminder(
            id="r8", patient_id="p1", title="X",
            message="Y", frequency=ReminderFrequency.DAILY,
            time="08:00", status=ReminderStatus.PAUSED,
        )
        assert r.is_due_today() is False

    def test_is_due_today_monthly(self):
        r = Reminder(
            id="r9", patient_id="p1", title="X",
            message="Y", frequency=ReminderFrequency.MONTHLY,
            time="10:00", start_date=date(2026, 1, 15),
        )
        assert r.is_due_today(date(2026, 2, 15)) is True
        assert r.is_due_today(date(2026, 2, 10)) is False


class TestEducationContent:
    def test_to_dict(self):
        ec = EducationContent(
            id="ckd-001",
            condition_code="N18",
            condition_name="DRC",
            title="O que e DRC",
            content="Texto educativo",
            tags=["renal", "introducao"],
        )
        d = ec.to_dict()
        assert d["id"] == "ckd-001"
        assert d["language"] == "pt-BR"
        assert "renal" in d["tags"]


class TestPatientAdherence:
    def test_to_dict(self):
        pa = PatientAdherence(
            patient_id="p1",
            total_tasks=10,
            completed_tasks=7,
            skipped_tasks=2,
            overdue_tasks=1,
            adherence_rate=0.7,
            active_reminders=3,
            conditions=["N18", "E11"],
        )
        d = pa.to_dict()
        assert d["adherence_rate"] == 0.7
        assert d["adherence_percent"] == "70%"
        assert d["total_tasks"] == 10

    def test_zero_tasks(self):
        pa = PatientAdherence(
            patient_id="p1",
            total_tasks=0,
            completed_tasks=0,
            skipped_tasks=0,
            overdue_tasks=0,
            adherence_rate=0.0,
            active_reminders=0,
            conditions=[],
        )
        assert pa.to_dict()["adherence_percent"] == "0%"
