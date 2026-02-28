"""FastAPI app persistente para Geralda (PostgreSQL)."""

from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
import os
from typing import Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from geralda.config import GeraldaConfig
from geralda.database.base import Base, get_engine, get_session_factory
from geralda.database.deps import get_db
from geralda.models.care_task import TaskCategory, TaskStatus
from geralda.services.care_plan_service import CarePlanService
from geralda.services.care_task_service import CareTaskService
from geralda.services.reminder_service import ReminderService


config = GeraldaConfig()
DATABASE_URL = os.getenv(
    "INTELLICARE_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql+asyncpg://intellicare:intellicare@postgres:5432/intellicare"),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine(DATABASE_URL)
    session_factory = get_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="IntelliCare Geralda",
    description="Agente de Acompanhamento do Paciente com persistencia PostgreSQL",
    version=config.module_version,
    lifespan=lifespan,
)


class CreatePlanRequest(BaseModel):
    patient_id: str
    conditions: list[str] = []
    goals: list[str] = []
    patient_name: str = ""


class AddTaskRequest(BaseModel):
    description: str
    category: str = "other"
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    notes: str = ""


class CreateReminderRequest(BaseModel):
    plan_id: str
    patient_id: str
    message: str
    scheduled_at: Optional[str] = None
    channel: str = "whatsapp"
    task_id: Optional[str] = None


@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "module_name": config.module_name,
        "version": config.module_version,
        "persistence": "postgresql",
    }


@app.get("/api/v1/info")
async def info():
    return {
        "name": config.module_name,
        "version": config.module_version,
        "description": "Agente de acompanhamento do paciente — persistente",
        "capabilities": ["care-plans", "task-management", "reminders", "adherence-tracking"],
    }


@app.post("/api/v1/plans")
async def create_plan(req: CreatePlanRequest, db: AsyncSession = Depends(get_db)):
    service = CarePlanService(db=db)
    plan = await service.create_plan(
        patient_id=req.patient_id,
        patient_name=req.patient_name or req.patient_id,
        conditions=[{"description": c} for c in req.conditions],
        goals=[{"title": g} for g in req.goals],
    )
    return {"success": True, "data": plan.to_dict()}


@app.get("/api/v1/plans/{plan_id}")
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    service = CarePlanService(db=db)
    plan = await service.get_plan(UUID(plan_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")
    return {"success": True, "data": plan.to_dict()}


@app.get("/api/v1/plans")
async def list_plans(patient_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    service = CarePlanService(db=db)
    if patient_id:
        plans = await service.list_plans_by_patient(patient_id=patient_id, active_only=False)
    else:
        plans = await service.list_all_plans(active_only=False, limit=500, offset=0)
    return {"success": True, "data": [plan.to_dict() for plan in plans], "total": len(plans)}


@app.post("/api/v1/plans/{plan_id}/tasks")
async def add_task(plan_id: str, req: AddTaskRequest, db: AsyncSession = Depends(get_db)):
    plan_service = CarePlanService(db=db)
    plan = await plan_service.get_plan(UUID(plan_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")

    due = date.fromisoformat(req.due_date) if req.due_date else None
    category = req.category if req.category in TaskCategory._value2member_map_ else TaskCategory.OTHER.value

    service = CareTaskService(db=db)
    task = await service.create_task(
        plan_id=plan.id,
        patient_id=plan.patient_id,
        title=req.description,
        description=req.description,
        category=category,
        due_date=due,
        due_time=req.due_time,
        notes=req.notes,
    )
    return {"success": True, "data": task.to_dict()}


@app.get("/api/v1/plans/{plan_id}/tasks")
async def get_tasks(
    plan_id: str,
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    service = CareTaskService(db=db)
    task_status = TaskStatus(status) if status in TaskStatus._value2member_map_ else None
    tasks = await service.list_tasks_by_plan(UUID(plan_id), status=task_status)
    return {"success": True, "data": [task.to_dict() for task in tasks], "total": len(tasks)}


@app.post("/api/v1/tasks/{task_id}/complete")
async def complete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    service = CareTaskService(db=db)
    task = await service.complete_task(UUID(task_id), completed_by="system")
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa nao encontrada")
    return {"success": True, "data": task.to_dict()}


@app.post("/api/v1/tasks/{task_id}/skip")
async def skip_task(task_id: str, reason: str = Query(""), db: AsyncSession = Depends(get_db)):
    service = CareTaskService(db=db)
    task = await service.skip_task(UUID(task_id), notes=reason)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa nao encontrada")
    return {"success": True, "data": task.to_dict()}


@app.get("/api/v1/adherence/{plan_id}")
async def get_adherence(plan_id: str, db: AsyncSession = Depends(get_db)):
    service = CareTaskService(db=db)
    tasks = await service.list_tasks_by_plan(UUID(plan_id))
    if not tasks:
        return {"success": True, "data": {"completed_tasks": 0, "pending_tasks": 0, "adherence_rate": 0}}
    completed = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
    pending = sum(1 for task in tasks if task.status == TaskStatus.PENDING)
    adherence = round((completed / len(tasks)) * 100, 2)
    return {
        "success": True,
        "data": {"completed_tasks": completed, "pending_tasks": pending, "adherence_rate": adherence},
    }


@app.post("/api/v1/reminders")
async def create_reminder(req: CreateReminderRequest, db: AsyncSession = Depends(get_db)):
    service = ReminderService(db=db)
    scheduled_at = (
        datetime.fromisoformat(req.scheduled_at).astimezone(UTC)
        if req.scheduled_at
        else datetime.now(UTC)
    )
    reminder = await service.schedule_reminder(
        plan_id=UUID(req.plan_id),
        patient_id=req.patient_id,
        message=req.message,
        scheduled_at=scheduled_at,
        channel=req.channel,
        task_id=UUID(req.task_id) if req.task_id else None,
    )
    return {"success": True, "data": reminder.to_dict()}

