"""Tools LangChain para operações de cuidado (modo in-memory para testes)."""

from datetime import date
from typing import Any

from geralda.engine.care_manager import CareManager
from geralda.engine.models import TaskCategory, TaskStatus


class AsyncTool:
    def __init__(self, name: str, description: str, handler):
        self.name = name
        self.description = description
        self._handler = handler

    async def arun(self, **kwargs):
        return await self._handler(**kwargs)


def create_care_plan_tool(care_manager: CareManager) -> AsyncTool:
    async def _arun(patient_id: str, conditions: list[str], goals: list[str], patient_name: str = "") -> dict[str, Any]:
        plan = care_manager.create_plan(
            patient_id=patient_id,
            conditions=conditions,
            goals=goals,
            patient_name=patient_name,
        )
        return {"success": True, "plan_id": plan.id, "conditions": plan.conditions, "goals": plan.goals}

    return AsyncTool(
        name="create_care_plan",
        description="Cria plano de cuidado em memória.",
        handler=_arun,
    )


def get_care_plan_tool(care_manager: CareManager) -> AsyncTool:
    async def _arun(plan_id: str) -> dict[str, Any]:
        plan = care_manager.get_plan(plan_id)
        if not plan:
            return {"success": False, "error": "Plano não encontrado"}
        return {"success": True, "plan": plan.to_dict()}

    return AsyncTool(
        name="get_care_plan",
        description="Busca plano de cuidado por id.",
        handler=_arun,
    )


def add_care_task_tool(care_manager: CareManager) -> AsyncTool:
    async def _arun(plan_id: str, description: str, category: str = "other", due_date: str | None = None, due_time: str | None = None) -> dict[str, Any]:
        normalized = category if category in TaskCategory._value2member_map_ else TaskCategory.OTHER.value
        category_enum = TaskCategory(normalized)
        parsed_due = date.fromisoformat(due_date) if due_date else None
        task = care_manager.add_task(plan_id=plan_id, description=description, category=category_enum, due_date=parsed_due, due_time=due_time)
        if not task:
            return {"success": False, "error": "Plano não encontrado"}
        data = task.to_dict()
        data["category"] = category_enum
        data["due_date"] = parsed_due
        return {"success": True, "task": data}

    return AsyncTool(
        name="add_care_task",
        description="Adiciona tarefa ao plano.",
        handler=_arun,
    )


def complete_task_tool(care_manager: CareManager) -> AsyncTool:
    async def _arun(task_id: str) -> dict[str, Any]:
        task = care_manager.complete_task(task_id)
        if not task:
            return {"success": False, "error": "Tarefa não encontrada"}
        data = task.to_dict()
        data["status"] = TaskStatus.COMPLETED
        return {"success": True, "task": data}

    return AsyncTool(
        name="complete_task",
        description="Completa tarefa por id.",
        handler=_arun,
    )


def get_adherence_tool(care_manager: CareManager) -> AsyncTool:
    async def _arun(plan_id: str) -> dict[str, Any]:
        adherence = care_manager.get_adherence(plan_id)
        if not adherence:
            return {"success": False, "error": "Plano não encontrado"}
        completion_rate = adherence.adherence_rate * 100
        return {
            "success": True,
            "adherence": {
                "total_tasks": adherence.total_tasks,
                "completed_tasks": adherence.completed_tasks,
                "completion_rate": completion_rate,
            },
        }

    return AsyncTool(
        name="get_adherence",
        description="Calcula adesão do plano.",
        handler=_arun,
    )


def get_care_tools(care_manager: CareManager) -> list[AsyncTool]:
    """Retorna conjunto padrão de tools de cuidado."""
    return [
        create_care_plan_tool(care_manager),
        get_care_plan_tool(care_manager),
        add_care_task_tool(care_manager),
        complete_task_tool(care_manager),
        get_adherence_tool(care_manager),
    ]
