"""FastAPI app persistente para Geralda (PostgreSQL).

Versão v2.0 — unifica endpoints do app.py (in-memory) com persistência DB,
monta rotas de chat e eventos, e implementa o contrato BaseAgent.
"""

from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
import os
import time
from typing import Any, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from geralda.config import GeraldaConfig
from geralda.database.base import Base, get_engine, get_session_factory
from geralda.database.deps import get_db
from geralda.engine.education.content_loader import ContentLoader
from geralda.engine.reminder_engine import ReminderEngine
from geralda.models.care_task import TaskCategory, TaskStatus
from geralda.services.care_plan_service import CarePlanService
from geralda.services.care_task_service import CareTaskService
from geralda.services.reminder_service import ReminderService

# Contracts IntelliCare Core
try:
    from intellicare_core.contracts.base_agent import AnalysisRequest, AnalysisResponse
    from intellicare_core.contracts.health import DependencyStatus, HealthCheck
    from intellicare_core.contracts.module_info import ModuleInfo

    _HAS_CORE = True
except ImportError:
    _HAS_CORE = False

# Prometheus metrics (opcional)
try:
    from intellicare_core.monitoring import setup_metrics

    _HAS_METRICS = True
except ImportError:
    _HAS_METRICS = False

# Auth integration (opcional)
try:
    from intellicare_auth.fastapi import configure_auth

    _HAS_AUTH = True
except ImportError:
    _HAS_AUTH = False

config = GeraldaConfig()
DATABASE_URL = os.getenv(
    "INTELLICARE_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        config.database_url or "postgresql+asyncpg://intellicare:intellicare@postgres:5432/intellicare",
    ),
)

# In-memory engines (lembretes legado e educação não dependem de DB)
reminder_engine = ReminderEngine(default_advance_minutes=config.default_reminder_advance_minutes)
content_loader = ContentLoader(data_dir=config.education_data_dir)

_start_time: float = 0.0
_db_connected: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time, _db_connected
    _start_time = time.monotonic()

    engine = get_engine(DATABASE_URL)
    session_factory = get_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _db_connected = True
    except Exception:
        _db_connected = False

    try:
        yield
    finally:
        await engine.dispose()


app = FastAPI(
    title="IntelliCare Geralda",
    description="Agente de Acompanhamento do Paciente — planos de cuidado, lembretes e educação em saúde",
    version=config.module_version,
    lifespan=lifespan,
)

if _HAS_AUTH:
    configure_auth(app, secrets_path="keycloak_client_secrets.json")

if _HAS_METRICS:
    setup_metrics(app, module_name="geralda")


# ── Request models ─────────────────────────────────────────────


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


class CreateReminderDBRequest(BaseModel):
    plan_id: str
    patient_id: str
    message: str
    scheduled_at: Optional[str] = None
    channel: str = "whatsapp"
    task_id: Optional[str] = None


class CreateReminderRequest(BaseModel):
    """Formato legado compatível com in-memory app."""

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
    uptime = time.monotonic() - _start_time if _start_time else 0.0

    if _HAS_CORE:
        deps = [
            DependencyStatus(
                name="postgresql",
                status="connected" if _db_connected else "disconnected",
            )
        ]
        return HealthCheck(
            status="healthy" if _db_connected else "degraded",
            module_name=config.module_name,
            version=config.module_version,
            uptime_seconds=uptime,
            dependencies=deps,
        ).model_dump(mode="json")

    return {
        "status": "healthy" if _db_connected else "degraded",
        "module_name": config.module_name,
        "version": config.module_version,
        "persistence": "postgresql",
        "uptime_seconds": uptime,
    }


@app.get("/api/v1/info")
async def info():
    capabilities = [
        "care-plans",
        "task-management",
        "reminders",
        "education",
        "adherence-tracking",
        "events",
        "ai-chat",
    ]

    if _HAS_CORE:
        return ModuleInfo(
            name=config.module_name,
            version=config.module_version,
            status="healthy",
            capabilities=capabilities,
            description="GERALDA — Acompanhamento longitudinal do paciente",
            metadata={
                "agent_name": "Geralda Lopes da Silva",
                "code_name": "GERALDA",
                "persistence": "postgresql",
            },
        ).model_dump()

    return {
        "name": config.module_name,
        "version": config.module_version,
        "description": "Agente de acompanhamento do paciente — persistente",
        "capabilities": capabilities,
    }


@app.post("/api/v1/analyze")
async def analyze(request: dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Endpoint de análise padrão IntelliCare (BaseAgent contract).

    Analisa situação de um paciente: planos, tarefas pendentes/vencidas,
    aderência ao tratamento.

    parameters aceitos:
      - include_tasks: bool (default True) — incluir tarefas
      - include_adherence: bool (default True) — incluir aderência
      - active_only: bool (default True) — apenas planos ativos
    """
    patient_id = request.get("patient_id", "")
    params = request.get("parameters", {})
    include_tasks = params.get("include_tasks", True)
    include_adherence = params.get("include_adherence", True)
    active_only = params.get("active_only", True)

    try:
        plan_service = CarePlanService(db=db)
        task_service = CareTaskService(db=db)

        plans = await plan_service.list_plans_by_patient(
            patient_id=patient_id, active_only=active_only
        )
        plans_data = [p.to_dict() for p in plans]

        analysis: dict[str, Any] = {
            "patient_id": patient_id,
            "total_plans": len(plans),
            "plans": plans_data,
        }
        recommendations: list[str] = []
        alerts: list[dict[str, Any]] = []

        if include_tasks and plans:
            all_tasks = []
            overdue_tasks = []
            for plan in plans:
                tasks = await task_service.list_tasks_by_plan(plan.id)
                all_tasks.extend(tasks)
                overdue = [t for t in tasks if t.is_overdue()]
                overdue_tasks.extend(overdue)

            analysis["total_tasks"] = len(all_tasks)
            analysis["overdue_tasks"] = len(overdue_tasks)
            analysis["pending_tasks"] = sum(
                1 for t in all_tasks if t.status == TaskStatus.PENDING
            )
            analysis["completed_tasks"] = sum(
                1 for t in all_tasks if t.status == TaskStatus.COMPLETED
            )

            if overdue_tasks:
                alerts.append({
                    "type": "overdue_tasks",
                    "count": len(overdue_tasks),
                    "message": f"Paciente tem {len(overdue_tasks)} tarefa(s) vencida(s)",
                    "tasks": [
                        {"id": str(t.id), "title": t.title, "due_date": str(t.due_date)}
                        for t in overdue_tasks[:5]
                    ],
                })
                recommendations.append(
                    f"Verificar {len(overdue_tasks)} tarefa(s) vencida(s) do paciente."
                )

        if include_adherence and plans:
            for plan in plans:
                tasks = await task_service.list_tasks_by_plan(plan.id)
                if tasks:
                    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
                    rate = round((completed / len(tasks)) * 100, 2)
                    if rate < 50:
                        alerts.append({
                            "type": "low_adherence",
                            "plan_id": str(plan.id),
                            "adherence_rate": rate,
                            "message": f"Aderência baixa ({rate}%) no plano {plan.patient_name}",
                        })
                        recommendations.append(
                            f"Aderência baixa ({rate}%) — considerar intervenção."
                        )

        confidence = 0.85 if plans else 0.3

        if _HAS_CORE:
            return AnalysisResponse(
                success=True,
                patient_id=patient_id,
                analysis=analysis,
                recommendations=recommendations,
                alerts=alerts,
                confidence=confidence,
                source="geralda",
            ).model_dump()

        return {
            "success": True,
            "patient_id": patient_id,
            "analysis": analysis,
            "recommendations": recommendations,
            "alerts": alerts,
            "confidence": confidence,
            "source": "geralda",
        }

    except Exception as exc:
        return {
            "success": False,
            "patient_id": patient_id,
            "analysis": {"error": str(exc)},
            "recommendations": [],
            "alerts": [],
            "confidence": 0.0,
            "source": "geralda",
        }


# ── Care Plan endpoints (DB-backed) ───────────────────────────


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


# ── Task endpoints (DB-backed) ────────────────────────────────


@app.post("/api/v1/plans/{plan_id}/tasks")
async def add_task(plan_id: str, req: AddTaskRequest, db: AsyncSession = Depends(get_db)):
    plan_service = CarePlanService(db=db)
    plan = await plan_service.get_plan(UUID(plan_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plano nao encontrado")

    due = date.fromisoformat(req.due_date) if req.due_date else None
    category = (
        req.category if req.category in TaskCategory._value2member_map_ else TaskCategory.OTHER.value
    )

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


# ── Adherence endpoints (DB-backed) ───────────────────────────


@app.get("/api/v1/adherence/{plan_id}")
async def get_adherence(plan_id: str, db: AsyncSession = Depends(get_db)):
    service = CareTaskService(db=db)
    tasks = await service.list_tasks_by_plan(UUID(plan_id))
    if not tasks:
        return {
            "success": True,
            "data": {"completed_tasks": 0, "pending_tasks": 0, "adherence_rate": 0},
        }
    completed = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
    pending = sum(1 for task in tasks if task.status == TaskStatus.PENDING)
    adherence = round((completed / len(tasks)) * 100, 2)
    return {
        "success": True,
        "data": {
            "completed_tasks": completed,
            "pending_tasks": pending,
            "adherence_rate": adherence,
        },
    }


# ── Reminder endpoints (DB-backed + in-memory legacy) ─────────


@app.post("/api/v1/reminders")
async def create_reminder(req: CreateReminderDBRequest, db: AsyncSession = Depends(get_db)):
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


@app.get("/api/v1/reminders")
async def get_reminders(patient_id: str = Query(...)):
    """Lista lembretes (in-memory engine)."""
    reminders = reminder_engine.get_patient_reminders(patient_id)
    return {
        "success": True,
        "data": [r.to_dict() for r in reminders],
        "total": len(reminders),
    }


@app.get("/api/v1/reminders/due")
async def get_due_reminders(patient_id: str = Query(...)):
    """Retorna lembretes que já estão no horário."""
    reminders = reminder_engine.get_due_reminders(patient_id)
    return {
        "success": True,
        "data": [r.to_dict() for r in reminders],
        "total": len(reminders),
    }


@app.get("/api/v1/reminders/schedule")
async def get_daily_schedule(patient_id: str = Query(...)):
    """Agenda diária do paciente."""
    schedule = reminder_engine.generate_daily_schedule(patient_id)
    return {"success": True, "data": schedule, "total": len(schedule)}


@app.post("/api/v1/reminders/{reminder_id}/pause")
async def pause_reminder(reminder_id: str):
    reminder = reminder_engine.pause_reminder(reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=404, detail="Lembrete nao encontrado ou nao pode ser pausado"
        )
    return {"success": True, "data": reminder.to_dict()}


@app.post("/api/v1/reminders/{reminder_id}/resume")
async def resume_reminder(reminder_id: str):
    reminder = reminder_engine.resume_reminder(reminder_id)
    if not reminder:
        raise HTTPException(
            status_code=404, detail="Lembrete nao encontrado ou nao pode ser retomado"
        )
    return {"success": True, "data": reminder.to_dict()}


@app.post("/api/v1/reminders/{reminder_id}/cancel")
async def cancel_reminder(reminder_id: str):
    reminder = reminder_engine.cancel_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Lembrete nao encontrado")
    return {"success": True, "data": reminder.to_dict()}


# ── Education endpoints (file-backed) ─────────────────────────


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


# ── Mount chat and event routers ──────────────────────────────

try:
    from geralda.api.chat_routes import router as chat_router

    app.include_router(chat_router)
except ImportError:
    pass

try:
    from geralda.api.event_routes import router as event_router

    app.include_router(event_router)
except ImportError:
    pass

