"""FastAPI application for intellicare-geralda — Patient Accompaniment Agent."""

from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from geralda.config import GeraldaConfig
from geralda.engine.care_manager import CareManager
from geralda.engine.education.content_loader import ContentLoader
from geralda.engine.models import (
    ReminderFrequency,
    TaskCategory,
    TaskStatus,
)
from geralda.engine.reminder_engine import ReminderEngine

# Auth integration (opcional)
try:
    from intellicare_auth.fastapi import configure_auth
    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False

# ── App setup ──────────────────────────────────────────────────

config = GeraldaConfig()

app = FastAPI(
    title="IntelliCare Geralda",
    description="Agente de Acompanhamento do Paciente — planos de cuidado, lembretes e educacao em saude",
    version=config.module_version,
)

if _HAS_AUTH:
    configure_auth(app, secrets_path="keycloak_client_secrets.json")

# ── Engine instances (in-memory for v1.0.0) ────────────────────

care_manager = CareManager()
reminder_engine = ReminderEngine(default_advance_minutes=config.default_reminder_advance_minutes)
content_loader = ContentLoader(data_dir=config.education_data_dir)


# ── Request/Response models ────────────────────────────────────

class CreatePlanRequest(BaseModel):
    patient_id: str
    conditions: list[str]
    goals: list[str] = []
    patient_name: str = ""


class AddTaskRequest(BaseModel):
    description: str
    category: str = "other"
    due_date: Optional[str] = None
    due_time: Optional[str] = None
    notes: str = ""


class CreateReminderRequest(BaseModel):
    patient_id: str
    title: str
    message: str
    reminder_time: str  # HH:MM
    frequency: str = "daily"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    days_of_week: list[int] = []


# ── Contract endpoints ─────────────────────────────────────────

@app.get("/api/v1/health")
async def health():
    return {
        "status": "healthy",
        "module_name": config.module_name,
        "version": config.module_version,
    }


@app.get("/api/v1/info")
async def info():
    return {
        "name": config.module_name,
        "version": config.module_version,
        "description": "Agente de acompanhamento do paciente — Geralda Lopes da Silva",
        "capabilities": [
            "care-plans",
            "task-management",
            "reminders",
            "education",
            "adherence-tracking",
        ],
    }


# ── Care Plan endpoints ───────────────────────────────────────

@app.post("/api/v1/plans")
async def create_plan(req: CreatePlanRequest):
    plan = care_manager.create_plan(
        patient_id=req.patient_id,
        conditions=req.conditions,
        goals=req.goals,
        patient_name=req.patient_name,
    )
    return {"success": True, "data": plan.to_dict()}


@app.get("/api/v1/plans/{plan_id}")
async def get_plan(plan_id: str):
    plan = care_manager.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")
    return {"success": True, "data": plan.to_dict()}


@app.get("/api/v1/plans")
async def list_plans(patient_id: Optional[str] = Query(None)):
    plans = care_manager.list_plans(patient_id=patient_id)
    return {
        "success": True,
        "data": [p.to_dict() for p in plans],
        "total": len(plans),
    }


# ── Task endpoints ─────────────────────────────────────────────

@app.post("/api/v1/plans/{plan_id}/tasks")
async def add_task(plan_id: str, req: AddTaskRequest):
    try:
        category = TaskCategory(req.category)
    except ValueError:
        category = TaskCategory.OTHER

    due = date.fromisoformat(req.due_date) if req.due_date else None

    task = care_manager.add_task(
        plan_id=plan_id,
        description=req.description,
        category=category,
        due_date=due,
        due_time=req.due_time,
        notes=req.notes,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")
    return {"success": True, "data": task.to_dict()}


@app.get("/api/v1/plans/{plan_id}/tasks")
async def get_tasks(
    plan_id: str,
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    try:
        task_status = TaskStatus(status) if status else None
    except ValueError:
        task_status = None

    try:
        task_category = TaskCategory(category) if category else None
    except ValueError:
        task_category = None

    tasks = care_manager.get_tasks(
        plan_id=plan_id,
        status=task_status,
        category=task_category,
    )
    return {
        "success": True,
        "data": [t.to_dict() for t in tasks],
        "total": len(tasks),
    }


@app.post("/api/v1/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    task = care_manager.complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa nao encontrada")
    return {"success": True, "data": task.to_dict()}


@app.post("/api/v1/tasks/{task_id}/skip")
async def skip_task(task_id: str, reason: str = Query("")):
    task = care_manager.skip_task(task_id, reason=reason)
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa nao encontrada")
    return {"success": True, "data": task.to_dict()}


# ── Reminder endpoints ─────────────────────────────────────────

@app.post("/api/v1/reminders")
async def create_reminder(req: CreateReminderRequest):
    try:
        freq = ReminderFrequency(req.frequency)
    except ValueError:
        freq = ReminderFrequency.DAILY

    start = date.fromisoformat(req.start_date) if req.start_date else None
    end = date.fromisoformat(req.end_date) if req.end_date else None

    reminder = reminder_engine.create_reminder(
        patient_id=req.patient_id,
        title=req.title,
        message=req.message,
        reminder_time=req.reminder_time,
        frequency=freq,
        start_date=start,
        end_date=end,
        days_of_week=req.days_of_week,
    )
    return {"success": True, "data": reminder.to_dict()}


@app.get("/api/v1/reminders")
async def get_reminders(patient_id: str = Query(...)):
    reminders = reminder_engine.get_patient_reminders(patient_id)
    return {
        "success": True,
        "data": [r.to_dict() for r in reminders],
        "total": len(reminders),
    }


@app.get("/api/v1/reminders/due")
async def get_due_reminders(patient_id: str = Query(...)):
    reminders = reminder_engine.get_due_reminders(patient_id)
    return {
        "success": True,
        "data": [r.to_dict() for r in reminders],
        "total": len(reminders),
    }


@app.get("/api/v1/reminders/schedule")
async def get_daily_schedule(patient_id: str = Query(...)):
    schedule = reminder_engine.generate_daily_schedule(patient_id)
    return {"success": True, "data": schedule, "total": len(schedule)}


@app.post("/api/v1/reminders/{reminder_id}/pause")
async def pause_reminder(reminder_id: str):
    reminder = reminder_engine.pause_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Lembrete nao encontrado ou nao pode ser pausado")
    return {"success": True, "data": reminder.to_dict()}


@app.post("/api/v1/reminders/{reminder_id}/resume")
async def resume_reminder(reminder_id: str):
    reminder = reminder_engine.resume_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Lembrete nao encontrado ou nao pode ser retomado")
    return {"success": True, "data": reminder.to_dict()}


@app.post("/api/v1/reminders/{reminder_id}/cancel")
async def cancel_reminder(reminder_id: str):
    reminder = reminder_engine.cancel_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Lembrete nao encontrado")
    return {"success": True, "data": reminder.to_dict()}


# ── Adherence endpoints ───────────────────────────────────────

@app.get("/api/v1/adherence/{plan_id}")
async def get_adherence(plan_id: str):
    adherence = care_manager.get_adherence(plan_id)
    if not adherence:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")
    return {"success": True, "data": adherence.to_dict()}


# ── Education endpoints ───────────────────────────────────────

@app.get("/api/v1/education/conditions")
async def list_conditions():
    conditions = content_loader.get_all_conditions()
    return {"success": True, "data": conditions, "total": len(conditions)}


@app.get("/api/v1/education/search")
async def search_education(q: str = Query(..., min_length=2)):
    results = content_loader.search(q)
    return {
        "success": True,
        "data": [m.to_dict() for m in results],
        "total": len(results),
    }


@app.get("/api/v1/education/material/{material_id}")
async def get_material(material_id: str):
    material = content_loader.get_material(material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material nao encontrado")
    return {"success": True, "data": material.to_dict()}


@app.get("/api/v1/education/{condition_code}")
async def get_education_materials(
    condition_code: str,
    reading_level: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
):
    materials = content_loader.get_by_condition(
        condition_code=condition_code,
        reading_level=reading_level,
        tag=tag,
    )
    return {
        "success": True,
        "data": [m.to_dict() for m in materials],
        "total": len(materials),
    }
