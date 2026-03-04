"""Gerenciador de planos de cuidado do paciente com isolamento por tenant."""

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
