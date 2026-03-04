import os

base_dir = r"c:\Users\egara\INTELLICARE\intellicare-geralda\geralda"

def create_auth_fallback():
    auth_code = '''"""Módulo de integração de autenticação e multitenancy para Geralda."""

import logging
from typing import Any

from fastapi import Depends, Header

try:
    from intellicare_auth.tenant.context import TenantContext, get_tenant_context
    from intellicare_auth.fastapi.middleware import check_module_active
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False

logger = logging.getLogger(__name__)


if not _HAS_AUTH:
    class MockTenantContext:
        """Contexto de tenant local para fallback."""

        def __init__(self, tenant_id: str, tenant_name: str = "Local Tenant"):
            self.tenant_id = tenant_id
            self.tenant_name = tenant_name
            self.schema_name = f"tenant_{tenant_id}"
            self.settings: dict[str, Any] = {}

    async def get_tenant_context(
        x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
    ) -> Any:
        """Fallback local."""
        if not x_tenant_id:
            return MockTenantContext("default")
        return MockTenantContext(x_tenant_id)
        
    def check_module_active(module_name: str) -> Any:
        async def mock_check_active(ctx: Any = Depends(get_tenant_context)) -> Any:
            return ctx
        return mock_check_active
'''
    with open(os.path.join(base_dir, "api", "auth.py"), "w", encoding="utf-8") as f:
        f.write(auth_code)


def rewrite_care_manager():
    content = '''"""Gerenciador de planos de cuidado do paciente com isolamento por tenant."""

import uuid
from datetime import datetime, date
from typing import Optional, Any

from geralda.engine.models import (
    CarePlan,
    CareTask,
    PatientAdherence,
    ReminderStatus,
    TaskCategory,
    TaskStatus,
)


class CareManager:
    """Orquestra planos de cuidado, tarefas e adesao do paciente com suporte multi-tenant."""

    def __init__(self) -> None:
        self._tenant_plans: dict[str, dict[str, CarePlan]] = {}
        self._tenant_tasks: dict[str, dict[str, CareTask]] = {}
        self._tenant_task_plan: dict[str, dict[str, str]] = {}

    def _gen_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def _get_tenant(self, ctx: Any) -> str:
        if ctx and hasattr(ctx, "tenant_id"):
            return ctx.tenant_id
        return "default"

    def _get_plans(self, tenant: str) -> dict[str, CarePlan]:
        return self._tenant_plans.setdefault(tenant, {})

    def _get_tasks(self, tenant: str) -> dict[str, CareTask]:
        return self._tenant_tasks.setdefault(tenant, {})

    def _get_task_plan(self, tenant: str) -> dict[str, str]:
        return self._tenant_task_plan.setdefault(tenant, {})

    # --- Care Plans ---

    def create_plan(
        self,
        patient_id: str,
        conditions: list[str],
        goals: list[str] | None = None,
        patient_name: str = "",
        ctx: Any = None,
    ) -> CarePlan:
        tenant = self._get_tenant(ctx)
        plans = self._get_plans(tenant)
        
        plan = CarePlan(
            id=self._gen_id(),
            patient_id=patient_id,
            patient_name=patient_name,
            conditions=conditions,
            goals=goals or [],
        )
        plans[plan.id] = plan
        return plan

    def get_plan(self, plan_id: str, ctx: Any = None) -> Optional[CarePlan]:
        tenant = self._get_tenant(ctx)
        return self._get_plans(tenant).get(plan_id)

    def list_plans(self, patient_id: Optional[str] = None, ctx: Any = None) -> list[CarePlan]:
        tenant = self._get_tenant(ctx)
        plans_dict = self._get_plans(tenant)
        plans = [p for p in plans_dict.values() if p.active]
        if patient_id:
            plans = [p for p in plans if p.patient_id == patient_id]
        return plans

    # --- Tasks ---

    def add_task(
        self,
        plan_id: str,
        description: str,
        category: TaskCategory = TaskCategory.OTHER,
        due_date: Optional[date] = None,
        due_time: Optional[str] = None,
        notes: str = "",
        ctx: Any = None,
    ) -> Optional[CareTask]:
        tenant = self._get_tenant(ctx)
        plans = self._get_plans(tenant)
        tasks = self._get_tasks(tenant)
        task_plan = self._get_task_plan(tenant)

        plan = plans.get(plan_id)
        if not plan:
            return None

        task = CareTask(
            id=self._gen_id(),
            patient_id=plan.patient_id,
            title=description,
            description=description,
            category=category,
            due_date=due_date,
            due_time=due_time,
            notes=notes,
        )
        plan.tasks.append(task)
        plan.updated_at = datetime.now()
        tasks[task.id] = task
        task_plan[task.id] = plan_id
        return task

    def complete_task(self, task_id: str, notes: str = "", ctx: Any = None) -> Optional[CareTask]:
        tenant = self._get_tenant(ctx)
        plans = self._get_plans(tenant)
        tasks = self._get_tasks(tenant)
        task_plan = self._get_task_plan(tenant)

        task = tasks.get(task_id)
        if not task:
            return None
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        if notes:
            task.notes = notes
        plan_id = task_plan.get(task_id)
        if plan_id and plan_id in plans:
            plans[plan_id].updated_at = datetime.now()
        return task

    def skip_task(self, task_id: str, reason: str = "", ctx: Any = None) -> Optional[CareTask]:
        tenant = self._get_tenant(ctx)
        plans = self._get_plans(tenant)
        tasks = self._get_tasks(tenant)
        task_plan = self._get_task_plan(tenant)

        task = tasks.get(task_id)
        if not task:
            return None
        task.status = TaskStatus.SKIPPED
        if reason:
            task.notes = reason
        plan_id = task_plan.get(task_id)
        if plan_id and plan_id in plans:
            plans[plan_id].updated_at = datetime.now()
        return task

    def get_tasks(
        self,
        plan_id: str,
        status: Optional[TaskStatus] = None,
        category: Optional[TaskCategory] = None,
        ctx: Any = None,
    ) -> list[CareTask]:
        tenant = self._get_tenant(ctx)
        plan = self._get_plans(tenant).get(plan_id)
        if not plan:
            return []

        tasks_list = plan.tasks
        if status:
            tasks_list = [t for t in tasks_list if t.status == status]
        if category:
            tasks_list = [t for t in tasks_list if t.category == category]
        return tasks_list

    # --- Adherence ---

    def get_adherence(self, plan_id: str, ctx: Any = None) -> Optional[PatientAdherence]:
        tenant = self._get_tenant(ctx)
        plan = self._get_plans(tenant).get(plan_id)
        if not plan:
            return None

        total = len(plan.tasks)
        completed = sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED)
        skipped = sum(1 for t in plan.tasks if t.status == TaskStatus.SKIPPED)
        overdue = sum(1 for t in plan.tasks if t.status == TaskStatus.OVERDUE)

        rate = completed / total if total > 0 else 0.0

        return PatientAdherence(
            patient_id=plan.patient_id,
            total_tasks=total,
            completed_tasks=completed,
            skipped_tasks=skipped,
            overdue_tasks=overdue,
            adherence_rate=rate,
            active_reminders=0,
            conditions=plan.conditions,
        )
'''
    with open(os.path.join(base_dir, "engine", "care_manager.py"), "w", encoding="utf-8") as f:
        f.write(content)


def rewrite_reminder_engine():
    content = '''"""Reminder engine com suporte multi-tenant."""

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
'''
    with open(os.path.join(base_dir, "engine", "reminder_engine.py"), "w", encoding="utf-8") as f:
        f.write(content)


def refactor_app():
    filepath = os.path.join(base_dir, "api", "app.py")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Import
    import_stmt = "\nfrom fastapi import Depends\nfrom typing import Any\nfrom geralda.api.auth import get_tenant_context, check_module_active\n"
    content = content.replace("from fastapi import FastAPI", import_stmt + "from fastapi import FastAPI")

    depends_str = ", ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-geralda'))"

    content = content.replace("async def health():", f"async def health(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-geralda'))):")
    content = content.replace("async def info():", f"async def info(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-geralda'))):")
    
    # Care Plan
    content = content.replace("async def create_plan(req: CreatePlanRequest):", f"async def create_plan(req: CreatePlanRequest{depends_str}):")
    content = content.replace("async def get_plan(plan_id: str):", f"async def get_plan(plan_id: str{depends_str}):")
    content = content.replace("async def list_plans(patient_id: Optional[str] = Query(None)):", f"async def list_plans(patient_id: Optional[str] = Query(None){depends_str}):")
    
    # Task
    content = content.replace("async def add_task(plan_id: str, req: AddTaskRequest):", f"async def add_task(plan_id: str, req: AddTaskRequest{depends_str}):")
    content = content.replace("category: Optional[str] = Query(None),\n):", f"category: Optional[str] = Query(None),\n    ctx: Any = Depends(get_tenant_context),\n    _check: Any = Depends(check_module_active('intellicare-geralda')),\n):")
    content = content.replace("async def complete_task(task_id: str):", f"async def complete_task(task_id: str{depends_str}):")
    content = content.replace('async def skip_task(task_id: str, reason: str = Query("")):', f'async def skip_task(task_id: str, reason: str = Query(""){depends_str}):')
    
    # Reminder
    content = content.replace("async def create_reminder(req: CreateReminderRequest):", f"async def create_reminder(req: CreateReminderRequest{depends_str}):")
    content = content.replace("async def get_reminders(patient_id: str = Query(...)):", f"async def get_reminders(patient_id: str = Query(...){depends_str}):")
    content = content.replace("async def get_due_reminders(patient_id: str = Query(...)):", f"async def get_due_reminders(patient_id: str = Query(...){depends_str}):")
    content = content.replace("async def get_daily_schedule(patient_id: str = Query(...)):", f"async def get_daily_schedule(patient_id: str = Query(...){depends_str}):")
    content = content.replace("async def pause_reminder(reminder_id: str):", f"async def pause_reminder(reminder_id: str{depends_str}):")
    content = content.replace("async def resume_reminder(reminder_id: str):", f"async def resume_reminder(reminder_id: str{depends_str}):")
    content = content.replace("async def cancel_reminder(reminder_id: str):", f"async def cancel_reminder(reminder_id: str{depends_str}):")
    
    # Adherence
    content = content.replace("async def get_adherence(plan_id: str):", f"async def get_adherence(plan_id: str{depends_str}):")
    
    # Education
    content = content.replace("async def list_conditions():", f"async def list_conditions(ctx: Any = Depends(get_tenant_context), _check: Any = Depends(check_module_active('intellicare-geralda'))):")
    content = content.replace("async def search_education(q: str = Query(..., min_length=2)):", f"async def search_education(q: str = Query(..., min_length=2){depends_str}):")
    content = content.replace("async def get_material(material_id: str):", f"async def get_material(material_id: str{depends_str}):")
    content = content.replace("tag: Optional[str] = Query(None),\n):", f"tag: Optional[str] = Query(None),\n    ctx: Any = Depends(get_tenant_context),\n    _check: Any = Depends(check_module_active('intellicare-geralda')),\n):")


    # Injections
    # Care Plan
    content = content.replace("plan = care_manager.create_plan(\n        patient_id=req.patient_id,\n        conditions=req.conditions,\n        goals=req.goals,\n        patient_name=req.patient_name,\n    )", "plan = care_manager.create_plan(\n        patient_id=req.patient_id,\n        conditions=req.conditions,\n        goals=req.goals,\n        patient_name=req.patient_name,\n        ctx=ctx,\n    )")
    content = content.replace("plan = care_manager.get_plan(plan_id)", "plan = care_manager.get_plan(plan_id, ctx=ctx)")
    content = content.replace("plans = care_manager.list_plans(patient_id=patient_id)", "plans = care_manager.list_plans(patient_id=patient_id, ctx=ctx)")
    
    # Task
    content = content.replace("task = care_manager.add_task(\n        plan_id=plan_id,\n        description=req.description,\n        category=category,\n        due_date=due,\n        due_time=req.due_time,\n        notes=req.notes,\n    )", "task = care_manager.add_task(\n        plan_id=plan_id,\n        description=req.description,\n        category=category,\n        due_date=due,\n        due_time=req.due_time,\n        notes=req.notes,\n        ctx=ctx,\n    )")
    content = content.replace("tasks = care_manager.get_tasks(\n        plan_id=plan_id,\n        status=task_status,\n        category=task_category,\n    )", "tasks = care_manager.get_tasks(\n        plan_id=plan_id,\n        status=task_status,\n        category=task_category,\n        ctx=ctx,\n    )")
    content = content.replace("task = care_manager.complete_task(task_id)", "task = care_manager.complete_task(task_id, ctx=ctx)")
    content = content.replace("task = care_manager.skip_task(task_id, reason=reason)", "task = care_manager.skip_task(task_id, reason=reason, ctx=ctx)")
    
    # Reminder
    content = content.replace("reminder = reminder_engine.create_reminder(\n        patient_id=req.patient_id,\n        title=req.title,\n        message=req.message,\n        reminder_time=req.reminder_time,\n        frequency=freq,\n        start_date=start,\n        end_date=end,\n        days_of_week=req.days_of_week,\n    )", "reminder = reminder_engine.create_reminder(\n        patient_id=req.patient_id,\n        title=req.title,\n        message=req.message,\n        reminder_time=req.reminder_time,\n        frequency=freq,\n        start_date=start,\n        end_date=end,\n        days_of_week=req.days_of_week,\n        ctx=ctx,\n    )")
    content = content.replace("reminders = reminder_engine.get_patient_reminders(patient_id)", "reminders = reminder_engine.get_patient_reminders(patient_id, ctx=ctx)")
    content = content.replace("reminders = reminder_engine.get_due_reminders(patient_id)", "reminders = reminder_engine.get_due_reminders(patient_id, ctx=ctx)")
    content = content.replace("schedule = reminder_engine.generate_daily_schedule(patient_id)", "schedule = reminder_engine.generate_daily_schedule(patient_id, ctx=ctx)")
    content = content.replace("reminder = reminder_engine.pause_reminder(reminder_id)", "reminder = reminder_engine.pause_reminder(reminder_id, ctx=ctx)")
    content = content.replace("reminder = reminder_engine.resume_reminder(reminder_id)", "reminder = reminder_engine.resume_reminder(reminder_id, ctx=ctx)")
    content = content.replace("reminder = reminder_engine.cancel_reminder(reminder_id)", "reminder = reminder_engine.cancel_reminder(reminder_id, ctx=ctx)")

    # Adherence
    content = content.replace("adherence = care_manager.get_adherence(plan_id)", "adherence = care_manager.get_adherence(plan_id, ctx=ctx)")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    create_auth_fallback()
    rewrite_care_manager()
    rewrite_reminder_engine()
    refactor_app()
    print("Geralda refatorada.")
