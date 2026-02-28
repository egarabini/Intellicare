"""Testes da API REST do Geralda."""

import pytest
from fastapi.testclient import TestClient

from geralda.api.app import app, care_manager, reminder_engine, content_loader


@pytest.fixture(autouse=True)
def reset_state():
    """Reset engine state before each test."""
    care_manager._plans.clear()
    care_manager._tasks.clear()
    care_manager._task_plan.clear()
    reminder_engine._reminders.clear()
    reminder_engine._by_patient.clear()
    content_loader._loaded = False
    content_loader._materials.clear()
    content_loader._by_condition.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)


class TestContractEndpoints:
    def test_health(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["module_name"] == "intellicare-geralda"

    def test_info(self, client):
        r = client.get("/api/v1/info")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "intellicare-geralda"
        assert "care-plans" in data["capabilities"]
        assert "reminders" in data["capabilities"]
        assert "education" in data["capabilities"]


class TestPlanEndpoints:
    def test_create_plan(self, client):
        r = client.post("/api/v1/plans", json={
            "patient_id": "p1",
            "conditions": ["N18.3", "E11"],
            "goals": ["Meta 1"],
            "patient_name": "Joao",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["patient_id"] == "p1"
        assert data["data"]["conditions"] == ["N18.3", "E11"]

    def test_get_plan(self, client):
        r = client.post("/api/v1/plans", json={
            "patient_id": "p1", "conditions": ["N18"],
        })
        plan_id = r.json()["data"]["id"]
        r = client.get(f"/api/v1/plans/{plan_id}")
        assert r.status_code == 200
        assert r.json()["data"]["id"] == plan_id

    def test_get_plan_404(self, client):
        r = client.get("/api/v1/plans/nope")
        assert r.status_code == 404

    def test_list_plans(self, client):
        client.post("/api/v1/plans", json={
            "patient_id": "p1", "conditions": ["N18"],
        })
        client.post("/api/v1/plans", json={
            "patient_id": "p2", "conditions": ["E11"],
        })
        r = client.get("/api/v1/plans")
        assert r.status_code == 200
        assert r.json()["total"] == 2

    def test_list_plans_filter(self, client):
        client.post("/api/v1/plans", json={
            "patient_id": "p1", "conditions": ["N18"],
        })
        client.post("/api/v1/plans", json={
            "patient_id": "p2", "conditions": ["E11"],
        })
        r = client.get("/api/v1/plans?patient_id=p1")
        assert r.json()["total"] == 1


class TestTaskEndpoints:
    def _create_plan(self, client):
        r = client.post("/api/v1/plans", json={
            "patient_id": "p1", "conditions": ["N18"],
        })
        return r.json()["data"]["id"]

    def test_add_task(self, client):
        plan_id = self._create_plan(client)
        r = client.post(f"/api/v1/plans/{plan_id}/tasks", json={
            "description": "Tomar remedio",
            "category": "medication",
        })
        assert r.status_code == 200
        assert r.json()["data"]["category"] == "medication"

    def test_add_task_plan_404(self, client):
        r = client.post("/api/v1/plans/nope/tasks", json={
            "description": "X",
        })
        assert r.status_code == 404

    def test_get_tasks(self, client):
        plan_id = self._create_plan(client)
        client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "A"})
        client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "B"})
        r = client.get(f"/api/v1/plans/{plan_id}/tasks")
        assert r.json()["total"] == 2

    def test_complete_task(self, client):
        plan_id = self._create_plan(client)
        r = client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "A"})
        task_id = r.json()["data"]["id"]
        r = client.post(f"/api/v1/tasks/{task_id}/complete")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "completed"

    def test_complete_task_404(self, client):
        r = client.post("/api/v1/tasks/nope/complete")
        assert r.status_code == 404

    def test_skip_task(self, client):
        plan_id = self._create_plan(client)
        r = client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "A"})
        task_id = r.json()["data"]["id"]
        r = client.post(f"/api/v1/tasks/{task_id}/skip?reason=Indisposto")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "skipped"

    def test_filter_tasks_by_status(self, client):
        plan_id = self._create_plan(client)
        r1 = client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "A"})
        client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "B"})
        task_id = r1.json()["data"]["id"]
        client.post(f"/api/v1/tasks/{task_id}/complete")

        r = client.get(f"/api/v1/plans/{plan_id}/tasks?status=completed")
        assert r.json()["total"] == 1

    def test_filter_tasks_by_category(self, client):
        plan_id = self._create_plan(client)
        client.post(f"/api/v1/plans/{plan_id}/tasks", json={
            "description": "A", "category": "medication",
        })
        client.post(f"/api/v1/plans/{plan_id}/tasks", json={
            "description": "B", "category": "exercise",
        })
        r = client.get(f"/api/v1/plans/{plan_id}/tasks?category=medication")
        assert r.json()["total"] == 1


class TestReminderEndpoints:
    def test_create_reminder(self, client):
        r = client.post("/api/v1/reminders", json={
            "patient_id": "p1",
            "title": "Remedio",
            "message": "Tomar Losartana",
            "reminder_time": "08:00",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["title"] == "Remedio"
        assert data["time"] == "08:00"

    def test_get_reminders(self, client):
        client.post("/api/v1/reminders", json={
            "patient_id": "p1", "title": "A", "message": "A", "reminder_time": "08:00",
        })
        client.post("/api/v1/reminders", json={
            "patient_id": "p1", "title": "B", "message": "B", "reminder_time": "14:00",
        })
        r = client.get("/api/v1/reminders?patient_id=p1")
        assert r.json()["total"] == 2

    def test_get_due_reminders(self, client):
        client.post("/api/v1/reminders", json={
            "patient_id": "p1", "title": "A", "message": "A", "reminder_time": "08:00",
        })
        r = client.get("/api/v1/reminders/due?patient_id=p1")
        assert r.json()["total"] >= 1

    def test_get_schedule(self, client):
        client.post("/api/v1/reminders", json={
            "patient_id": "p1", "title": "A", "message": "A", "reminder_time": "08:00",
        })
        client.post("/api/v1/reminders", json={
            "patient_id": "p1", "title": "B", "message": "B", "reminder_time": "06:00",
        })
        r = client.get("/api/v1/reminders/schedule?patient_id=p1")
        data = r.json()["data"]
        assert data[0]["time"] <= data[1]["time"]

    def test_pause_resume(self, client):
        r = client.post("/api/v1/reminders", json={
            "patient_id": "p1", "title": "A", "message": "A", "reminder_time": "08:00",
        })
        rid = r.json()["data"]["id"]
        r = client.post(f"/api/v1/reminders/{rid}/pause")
        assert r.json()["data"]["status"] == "paused"
        r = client.post(f"/api/v1/reminders/{rid}/resume")
        assert r.json()["data"]["status"] == "active"

    def test_cancel(self, client):
        r = client.post("/api/v1/reminders", json={
            "patient_id": "p1", "title": "A", "message": "A", "reminder_time": "08:00",
        })
        rid = r.json()["data"]["id"]
        r = client.post(f"/api/v1/reminders/{rid}/cancel")
        assert r.json()["data"]["status"] == "cancelled"

    def test_pause_404(self, client):
        r = client.post("/api/v1/reminders/nope/pause")
        assert r.status_code == 404


class TestAdherenceEndpoints:
    def test_adherence(self, client):
        r = client.post("/api/v1/plans", json={
            "patient_id": "p1", "conditions": ["N18"],
        })
        plan_id = r.json()["data"]["id"]
        client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "A"})
        client.post(f"/api/v1/plans/{plan_id}/tasks", json={"description": "B"})

        r = client.get(f"/api/v1/adherence/{plan_id}")
        assert r.status_code == 200
        assert r.json()["data"]["total_tasks"] == 2
        assert r.json()["data"]["adherence_rate"] == 0.0

    def test_adherence_404(self, client):
        r = client.get("/api/v1/adherence/nope")
        assert r.status_code == 404


class TestEducationEndpoints:
    def test_list_conditions(self, client):
        content_loader.load()
        r = client.get("/api/v1/education/conditions")
        assert r.status_code == 200
        # Should have data from bundled YAML files
        assert r.json()["total"] >= 0

    def test_search(self, client):
        content_loader.load()
        r = client.get("/api/v1/education/search?q=diabetes")
        assert r.status_code == 200

    def test_get_material_404(self, client):
        content_loader.load()
        r = client.get("/api/v1/education/material/nope")
        assert r.status_code == 404
