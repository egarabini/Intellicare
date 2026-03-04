"""Testes para app_db.py — versão DB-backed do Geralda."""

import importlib.util

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from geralda.database.base import Base


# ── Fixtures ───────────────────────────────────────────────────

@pytest_asyncio.fixture
async def app_with_db():
    """Cria app_db com SQLite in-memory para testes."""
    has_aiosqlite = importlib.util.find_spec("aiosqlite") is not None
    if not has_aiosqlite:
        pytest.skip("aiosqlite not installed")

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Import app_db and override its lifespan state
    from geralda.api.app_db import app

    app.state.engine = engine
    app.state.session_factory = session_factory

    yield app

    await engine.dispose()


@pytest_asyncio.fixture
async def client(app_with_db):
    """AsyncClient for testing the DB-backed app."""
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Health & Info ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_returns_module_info(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["module_name"] == "intellicare-geralda"
    assert "version" in data


@pytest.mark.asyncio
async def test_info_lists_capabilities(client):
    response = await client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "care-plans" in data["capabilities"]
    assert "education" in data["capabilities"]
    assert "events" in data["capabilities"]


# ── Care Plans CRUD ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_get_plan(client):
    # Create
    resp = await client.post("/api/v1/plans", json={
        "patient_id": "patient-001",
        "conditions": ["DM2", "HAS"],
        "goals": ["HbA1c < 7%"],
        "patient_name": "Maria",
    })
    assert resp.status_code == 200
    plan = resp.json()["data"]
    assert plan["patient_id"] == "patient-001"
    plan_id = plan["id"]

    # Get
    resp = await client.get(f"/api/v1/plans/{plan_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["patient_id"] == "patient-001"

    # List
    resp = await client.get("/api/v1/plans?patient_id=patient-001")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_get_plan_404(client):
    resp = await client.get("/api/v1/plans/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ── Tasks ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_task_and_complete(client):
    # Create plan first
    resp = await client.post("/api/v1/plans", json={
        "patient_id": "patient-t",
        "conditions": ["HAS"],
    })
    plan_id = resp.json()["data"]["id"]

    # Add task
    resp = await client.post(f"/api/v1/plans/{plan_id}/tasks", json={
        "description": "Medir pressão arterial",
        "category": "monitoring",
        "due_date": "2025-06-15",
    })
    assert resp.status_code == 200
    task = resp.json()["data"]
    task_id = task["id"]

    # Complete
    resp = await client.post(f"/api/v1/tasks/{task_id}/complete")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_skip_task(client):
    resp = await client.post("/api/v1/plans", json={
        "patient_id": "patient-s",
        "conditions": [],
    })
    plan_id = resp.json()["data"]["id"]

    resp = await client.post(f"/api/v1/plans/{plan_id}/tasks", json={
        "description": "Tarefa skip",
    })
    task_id = resp.json()["data"]["id"]

    resp = await client.post(f"/api/v1/tasks/{task_id}/skip?reason=nao+aplicavel")
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "skipped"


# ── Adherence ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_adherence(client):
    resp = await client.post("/api/v1/plans", json={
        "patient_id": "patient-ad",
        "conditions": ["DM2"],
    })
    plan_id = resp.json()["data"]["id"]

    # Add 2 tasks, complete 1
    resp = await client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "T1"})
    t1_id = resp.json()["data"]["id"]
    await client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "T2"})
    await client.post(f"/api/v1/tasks/{t1_id}/complete")

    resp = await client.get(f"/api/v1/adherence/{plan_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["completed_tasks"] == 1
    assert data["adherence_rate"] == 50.0


# ── Analyze endpoint ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_no_plans(client):
    """Paciente sem planos retorna análise vazia."""
    resp = await client.post("/api/v1/analyze", json={
        "patient_id": "patient-none",
        "parameters": {},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["source"] == "geralda"
    assert data["analysis"]["total_plans"] == 0


@pytest.mark.asyncio
async def test_analyze_with_plans_and_tasks(client):
    """Análise com planos e tarefas retorna dados de aderência."""
    # Setup: plan + tasks
    resp = await client.post("/api/v1/plans", json={
        "patient_id": "patient-a",
        "conditions": ["HAS"],
        "patient_name": "João",
    })
    plan_id = resp.json()["data"]["id"]

    resp = await client.post(f"/api/v1/plans/{plan_id}/tasks", json={
        "description": "Tomar medicação",
        "due_date": "2024-01-01",
    })
    t_id = resp.json()["data"]["id"]
    await client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "Exercício"})

    # Analyze
    resp = await client.post("/api/v1/analyze", json={
        "patient_id": "patient-a",
        "parameters": {"include_tasks": True, "include_adherence": True},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["analysis"]["total_plans"] == 1
    assert data["analysis"]["total_tasks"] == 2
    assert data["confidence"] > 0


# ── Education endpoints ────────────────────────────────────────


@pytest.mark.asyncio
async def test_education_conditions(client):
    resp = await client.get("/api/v1/education/conditions")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_education_search(client):
    resp = await client.get("/api/v1/education/search?q=diabetes")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


# ── Reminder in-memory endpoints ───────────────────────────────


@pytest.mark.asyncio
async def test_reminders_list_empty(client):
    resp = await client.get("/api/v1/reminders?patient_id=nobody")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
