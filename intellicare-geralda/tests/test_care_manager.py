"""Testes do CareManager."""

from datetime import date

from geralda.engine.care_manager import CareManager
from geralda.engine.models import TaskCategory, TaskStatus


class TestCreatePlan:
    def test_create_plan(self, care_manager):
        plan = care_manager.create_plan(
            patient_id="p1",
            conditions=["N18.3"],
            goals=["Meta 1"],
            patient_name="Joao",
        )
        assert plan.id is not None
        assert plan.patient_id == "p1"
        assert plan.conditions == ["N18.3"]
        assert plan.active is True

    def test_create_plan_default_name(self, care_manager):
        plan = care_manager.create_plan(patient_id="p2", conditions=["E11"])
        assert plan.patient_name == ""
        assert plan.goals == []

    def test_create_multiple_plans(self, care_manager):
        p1 = care_manager.create_plan(patient_id="p1", conditions=["N18"])
        p2 = care_manager.create_plan(patient_id="p1", conditions=["E11"])
        assert p1.id != p2.id
        assert len(care_manager.list_plans(patient_id="p1")) == 2


class TestGetPlan:
    def test_get_existing_plan(self, care_manager):
        plan = care_manager.create_plan(patient_id="p1", conditions=["N18"])
        found = care_manager.get_plan(plan.id)
        assert found is not None
        assert found.id == plan.id

    def test_get_nonexistent_plan(self, care_manager):
        assert care_manager.get_plan("nope") is None


class TestListPlans:
    def test_list_all(self, care_manager):
        care_manager.create_plan(patient_id="p1", conditions=["N18"])
        care_manager.create_plan(patient_id="p2", conditions=["E11"])
        assert len(care_manager.list_plans()) == 2

    def test_list_by_patient(self, care_manager):
        care_manager.create_plan(patient_id="p1", conditions=["N18"])
        care_manager.create_plan(patient_id="p2", conditions=["E11"])
        assert len(care_manager.list_plans(patient_id="p1")) == 1

    def test_list_empty(self, care_manager):
        assert care_manager.list_plans() == []


class TestTasks:
    def test_add_task(self, care_manager, sample_plan):
        tasks = care_manager.get_tasks(sample_plan.id)
        assert len(tasks) == 3

    def test_add_task_to_nonexistent_plan(self, care_manager):
        result = care_manager.add_task(plan_id="nope", description="X")
        assert result is None

    def test_complete_task(self, care_manager, sample_plan):
        tasks = care_manager.get_tasks(sample_plan.id)
        task = care_manager.complete_task(tasks[0].id, notes="Feito")
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.notes == "Feito"

    def test_complete_nonexistent_task(self, care_manager):
        assert care_manager.complete_task("nope") is None

    def test_skip_task(self, care_manager, sample_plan):
        tasks = care_manager.get_tasks(sample_plan.id)
        task = care_manager.skip_task(tasks[1].id, reason="Indisposicao")
        assert task is not None
        assert task.status == TaskStatus.SKIPPED
        assert task.notes == "Indisposicao"

    def test_skip_nonexistent_task(self, care_manager):
        assert care_manager.skip_task("nope") is None

    def test_filter_by_status(self, care_manager, sample_plan):
        tasks = care_manager.get_tasks(sample_plan.id)
        care_manager.complete_task(tasks[0].id)
        pending = care_manager.get_tasks(sample_plan.id, status=TaskStatus.PENDING)
        completed = care_manager.get_tasks(sample_plan.id, status=TaskStatus.COMPLETED)
        assert len(pending) == 2
        assert len(completed) == 1

    def test_filter_by_category(self, care_manager, sample_plan):
        meds = care_manager.get_tasks(sample_plan.id, category=TaskCategory.MEDICATION)
        assert len(meds) == 1
        assert meds[0].category == TaskCategory.MEDICATION

    def test_get_tasks_nonexistent_plan(self, care_manager):
        assert care_manager.get_tasks("nope") == []

    def test_add_task_with_due_date(self, care_manager, sample_plan):
        task = care_manager.add_task(
            plan_id=sample_plan.id,
            description="Exame de sangue",
            category=TaskCategory.EXAM,
            due_date=date(2026, 3, 1),
            due_time="10:00",
        )
        assert task.due_date == date(2026, 3, 1)
        assert task.due_time == "10:00"


class TestAdherence:
    def test_adherence_all_pending(self, care_manager, sample_plan):
        adh = care_manager.get_adherence(sample_plan.id)
        assert adh is not None
        assert adh.total_tasks == 3
        assert adh.adherence_rate == 0.0

    def test_adherence_partial(self, care_manager, sample_plan):
        tasks = care_manager.get_tasks(sample_plan.id)
        care_manager.complete_task(tasks[0].id)
        care_manager.complete_task(tasks[1].id)
        adh = care_manager.get_adherence(sample_plan.id)
        assert adh.completed_tasks == 2
        assert abs(adh.adherence_rate - 2 / 3) < 0.01

    def test_adherence_nonexistent(self, care_manager):
        assert care_manager.get_adherence("nope") is None

    def test_adherence_empty_plan(self, care_manager):
        plan = care_manager.create_plan(patient_id="p1", conditions=["N18"])
        adh = care_manager.get_adherence(plan.id)
        assert adh.total_tasks == 0
        assert adh.adherence_rate == 0.0
