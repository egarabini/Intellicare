"""Tests for Registry API routes (EF-W001)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from wanda.api.registry_routes import router, init_registry_routes
from wanda.discovery.models import ModuleInfo, ModuleStatus


@pytest.fixture
def mock_registry():
    """Mock PersistentModuleRegistry."""
    reg = MagicMock()
    reg.total_modules = 2
    reg.online_count = 1
    reg.has_persistence = False

    reg.get_all_modules_dict = AsyncMock(return_value=[
        {"name": "intellicare-oswaldo", "status": "online", "version": "1.0.0"},
        {"name": "intellicare-florence", "status": "offline", "version": "0.9.0"},
    ])

    reg.get_routing_table = AsyncMock(return_value={
        "routing": {"monitoring": ["intellicare-oswaldo"]},
        "last_updated": None,
        "total_modules": 2,
        "online_modules": 1,
    })

    m = MagicMock()
    m.to_dict.return_value = {
        "name": "intellicare-oswaldo",
        "status": "online",
        "version": "1.0.0",
    }
    reg.get_module = MagicMock(side_effect=lambda n: m if n == "intellicare-oswaldo" else None)

    reg.get_health_history = AsyncMock(return_value=[
        {"event_type": "unhealthy", "reason": "timeout"}
    ])

    reg.get_capabilities_history = AsyncMock(return_value=[
        {"version": "1.0.0", "capabilities": ["monitoring"]}
    ])

    return reg


@pytest.fixture
def mock_discovery():
    return MagicMock()


@pytest.fixture
def app(mock_registry, mock_discovery):
    test_app = FastAPI()
    test_app.include_router(router)
    init_registry_routes(mock_registry, mock_discovery)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestListAllModules:
    def test_list(self, client):
        resp = client.get("/api/v1/registry")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["total"] == 2
        assert data["data"]["online"] == 1
        assert len(data["data"]["modules"]) == 2


class TestRoutingTable:
    def test_routing_table(self, client):
        resp = client.get("/api/v1/registry/routing-table")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "routing" in data["data"]


class TestGetModuleDetail:
    def test_found(self, client):
        resp = client.get("/api/v1/registry/intellicare-oswaldo")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["name"] == "intellicare-oswaldo"

    def test_not_found(self, client):
        resp = client.get("/api/v1/registry/nonexistent")
        assert resp.status_code == 404


class TestHealthHistory:
    def test_history(self, client):
        resp = client.get("/api/v1/registry/intellicare-oswaldo/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["count"] == 1


class TestCapabilitiesHistory:
    def test_capabilities_history(self, client):
        resp = client.get("/api/v1/registry/intellicare-oswaldo/capabilities-history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert len(data["data"]["versions"]) == 1


class TestRegistryNotInitialized:
    def test_503_when_no_registry(self):
        """When registry is None, all endpoints return 503."""
        test_app = FastAPI()
        test_app.include_router(router)
        init_registry_routes(None, None)
        c = TestClient(test_app)
        resp = c.get("/api/v1/registry")
        assert resp.status_code == 503
