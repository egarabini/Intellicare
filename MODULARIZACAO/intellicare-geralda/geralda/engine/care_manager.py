"""Gerenciador de planos de cuidado do paciente."""

import uuid
from datetime import datetime, date
from typing import Optional

from geralda.engine.models import (
    CarePlan,
    CareTask,
    PatientAdherence,
    ReminderStatus,
    TaskCategory,
    TaskStatus,
)


class CareManager:
    """Orquestra planos de cuidado, tarefas e adesao do paciente."""

    def __init__(self) -> None:
        self._plans: dict[str, CarePlan] = {}  # plan_id -> CarePlan
        self._tasks: dict[str, CareTask] = {}  # task_id -> CareTask
        self._task_plan: dict[str, str] = {}  # task_id -> plan_id

    def _gen_id(self) -> str:
        return str(uuid.uuid4())[:8]

    # --- Care Plans ---

    def create_plan(
        self,
        patient_id: str,
        conditions: list[str],
        goals: list[str] | None = None,
        patient_name: str = "",
    ) -> CarePlan:
        """Cria um novo plano de cuidado para o paciente."""
        plan = CarePlan(
            id=self._gen_id(),
            patient_id=patient_id,
            patient_name=patient_name,
            conditions=conditions,
            goals=goals or [],
        )
        self._plans[plan.id] = plan
        return plan

    def get_plan(self, plan_id: str) -> Optional[CarePlan]:
        """Retorna um plano de cuidado pelo ID."""
        return self._plans.get(plan_id)

    def list_plans(self, patient_id: Optional[str] = None) -> list[CarePlan]:
        """Lista planos ativos, opcionalmente filtrados por paciente."""
        plans = [p for p in self._plans.values() if p.active]
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
    ) -> Optional[CareTask]:
        """Adiciona uma tarefa ao plano."""
        plan = self._plans.get(plan_id)
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
        self._tasks[task.id] = task
        self._task_plan[task.id] = plan_id
        return task

    def complete_task(self, task_id: str, notes: str = "") -> Optional[CareTask]:
        """Marca uma tarefa como concluida."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        if notes:
            task.notes = notes
        plan_id = self._task_plan.get(task_id)
        if plan_id and plan_id in self._plans:
            self._plans[plan_id].updated_at = datetime.now()
        return task

    def skip_task(self, task_id: str, reason: str = "") -> Optional[CareTask]:
        """Marca uma tarefa como pulada."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = TaskStatus.SKIPPED
        if reason:
            task.notes = reason
        plan_id = self._task_plan.get(task_id)
        if plan_id and plan_id in self._plans:
            self._plans[plan_id].updated_at = datetime.now()
        return task

    def get_tasks(
        self,
        plan_id: str,
        status: Optional[TaskStatus] = None,
        category: Optional[TaskCategory] = None,
    ) -> list[CareTask]:
        """Lista tarefas de um plano com filtros opcionais."""
        plan = self._plans.get(plan_id)
        if not plan:
            return []

        tasks = plan.tasks
        if status:
            tasks = [t for t in tasks if t.status == status]
        if category:
            tasks = [t for t in tasks if t.category == category]
        return tasks

    # --- Adherence ---

    def get_adherence(self, plan_id: str) -> Optional[PatientAdherence]:
        """Calcula a adesao do paciente baseada no plano."""
        plan = self._plans.get(plan_id)
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
