"""Testes da API REST do Wanda."""

import pytest
import respx
import httpx
from fastapi.testclient import TestClient

from wanda.api.app import app, orchestrator


@pytest.fixture(autouse=True)
def reset_state():
    """Reset orchestrator state before each test."""
    orchestrator._discovered = False
    orchestrator.registry._modules.clear()
    orchestrator.registry._last_discovery = None
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
        assert data["module_name"] == "intellicare-wanda"

    def test_info(self, client):
        r = client.get("/api/v1/info")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "intellicare-wanda"
        assert "orchestration" in data["capabilities"]
        assert "module-discovery" in data["capabilities"]
        assert "safety-rules" in data["capabilities"]


class TestChatEndpoint:
    @respx.mock
    def test_chat_no_modules_online(self, client):
        # Mock all modules as offline
        respx.get(url__regex=r".*").mock(
            side_effect=httpx.ConnectError("refused")
        )

        r = client.post("/api/v1/chat", json={
            "message": "Como esta o paciente?",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert "Nenhum modulo" in data["response"]

    @respx.mock
    def test_chat_with_module(self, client):
        # Mock Oswaldo online
        respx.get("http://localhost:8001/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "intellicare-oswaldo", "version": "1.0.0",
                "capabilities": ["chronic-disease-monitoring"],
            })
        )
        respx.get("http://localhost:8001/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        # All other modules offline
        respx.get(url__regex=r"http://localhost:800[2-6].*").mock(
            side_effect=httpx.ConnectError("refused")
        )
        # Mock the analysis call
        respx.get("http://localhost:8001/api/v1/diseases").mock(
            return_value=httpx.Response(200, json={
                "data": ["CKD", "DM2", "HAS"],
            })
        )

        r = client.post("/api/v1/chat", json={
            "message": "Quais doencas cronicas voce monitora?",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data["modules_used"]) >= 1


class TestRouteEndpoint:
    @respx.mock
    def test_route_preview(self, client):
        # Mock Oswaldo online
        respx.get("http://localhost:8001/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "intellicare-oswaldo", "version": "1.0.0",
                "capabilities": ["chronic-disease-monitoring"],
            })
        )
        respx.get("http://localhost:8001/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get(url__regex=r"http://localhost:800[2-6].*").mock(
            side_effect=httpx.ConnectError("refused")
        )

        r = client.post("/api/v1/route", json={
            "message": "Como esta a creatinina do paciente renal?",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert "intellicare-oswaldo" in data["target_modules"]


class TestModuleEndpoints:
    @respx.mock
    def test_list_modules(self, client):
        respx.get(url__regex=r".*").mock(
            side_effect=httpx.ConnectError("refused")
        )

        r = client.get("/api/v1/modules")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "total" in data
        assert "modules" in data

    @respx.mock
    def test_discover(self, client):
        respx.get("http://localhost:8001/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "intellicare-oswaldo", "version": "1.0.0",
                "capabilities": [],
            })
        )
        respx.get("http://localhost:8001/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get(url__regex=r"http://localhost:800[2-6].*").mock(
            side_effect=httpx.ConnectError("refused")
        )

        r = client.post("/api/v1/modules/discover")
        assert r.status_code == 200
        assert r.json()["online_count"] == 1

    @respx.mock
    def test_get_module_404(self, client):
        respx.get(url__regex=r".*").mock(
            side_effect=httpx.ConnectError("refused")
        )
        # Need to trigger discovery first
        client.post("/api/v1/modules/discover")

        r = client.get("/api/v1/modules/nope")
        assert r.status_code == 404


class TestCapabilities:
    @respx.mock
    def test_list_all_capabilities(self, client):
        respx.get("http://localhost:8001/api/v1/info").mock(
            return_value=httpx.Response(200, json={
                "name": "intellicare-oswaldo", "version": "1.0.0",
                "capabilities": ["chronic-disease"],
            })
        )
        respx.get("http://localhost:8001/api/v1/health").mock(
            return_value=httpx.Response(200, json={"status": "healthy"})
        )
        respx.get(url__regex=r"http://localhost:800[2-6].*").mock(
            side_effect=httpx.ConnectError("refused")
        )

        r = client.get("/api/v1/capabilities")
        assert r.status_code == 200
        assert r.json()["total"] >= 1
