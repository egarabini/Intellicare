"""Tests for AlertHub API routes (EF-W007)."""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import MagicMock, AsyncMock

from wanda.api.alert_routes import router


@pytest.fixture
def mock_hub():
    hub = MagicMock()
    hub.receive_alert = AsyncMock(return_value=MagicMock(
        alert_id="a1",
        status="accepted",
        priority_score=75,
        message="Alerta aceito",
    ))
    hub.get_pending_alerts = MagicMock(return_value=[
        {"alert_id": "a1", "title": "Teste", "severity": "high", "priority_score": 75}
    ])
    hub.acknowledge_alert = MagicMock(return_value=True)
    hub.resolve_alert = MagicMock(return_value=True)
    hub.get_stats = MagicMock(return_value={"pending": 1, "acknowledged": 0, "resolved": 0})
    return hub


@pytest.fixture
def app(mock_hub):
    _app = FastAPI()
    _app.include_router(router)
    _app.state.alert_hub = mock_hub
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def app_no_hub():
    _app = FastAPI()
    _app.include_router(router)
    _app.state.alert_hub = None
    return _app


@pytest.fixture
def client_no_hub(app_no_hub):
    return TestClient(app_no_hub)


class TestAlertRoutes:
    def test_receive_alert_success(self, client):
        payload = {
            "patient_id": "p1",
            "source_agent": "intellicare-florence",
            "alert_type": "vital_sign",
            "severity": "high",
            "title": "HR elevada",
        }
        resp = client.post("/api/v1/alerts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert data["alert_id"] == "a1"

    def test_receive_alert_invalid_severity(self, client):
        payload = {
            "patient_id": "p1",
            "source_agent": "florence",
            "alert_type": "vital_sign",
            "severity": "extreme",  # invalid
            "title": "Test",
        }
        resp = client.post("/api/v1/alerts", json=payload)
        assert resp.status_code == 422  # validation error

    def test_get_queue(self, client):
        resp = client.get("/api/v1/alerts/queue")
        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data
        assert data["total"] == 1

    def test_acknowledge_alert(self, client):
        resp = client.put("/api/v1/alerts/a1/acknowledge", json={"acknowledged_by": "nurse-1"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "acknowledged"

    def test_acknowledge_not_found(self, client, mock_hub):
        mock_hub.acknowledge_alert.return_value = False
        resp = client.put("/api/v1/alerts/unknown-id/acknowledge", json={"acknowledged_by": "u"})
        assert resp.status_code == 404

    def test_resolve_alert(self, client):
        resp = client.put("/api/v1/alerts/a1/resolve", json={"resolved_by": "dr-1"})
        assert resp.status_code == 200

    def test_resolve_alert_not_found(self, app):
        app.state.alert_hub.resolve_alert = MagicMock(return_value=False)
        with TestClient(app) as c:
            resp = c.put("/api/v1/alerts/unknown-id/resolve", json={"resolved_by": "dr-1"})
        assert resp.status_code == 404

    def test_get_patient_alerts(self, client):
        resp = client.get("/api/v1/alerts/patient/p1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["patient_id"] == "p1"

    def test_get_stats(self, client):
        resp = client.get("/api/v1/alerts/stats")
        assert resp.status_code == 200
        assert "pending" in resp.json()

    def test_hub_not_available_returns_503(self, client_no_hub):
        resp = client_no_hub.post("/api/v1/alerts", json={
            "patient_id": "p1", "source_agent": "f", "alert_type": "v",
            "severity": "low", "title": "T",
        })
        assert resp.status_code == 503
