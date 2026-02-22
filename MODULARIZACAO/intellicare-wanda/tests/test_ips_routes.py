"""Tests for IPS API routes (EF-W002)."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI

from wanda.api.ips_routes import router, init_ips_routes
from wanda.ips.models import IPSBundle, ValidationResult


@pytest.fixture
def mock_ips_manager():
    mgr = MagicMock()
    mgr.get_stats = AsyncMock(return_value={
        "has_redis": False,
        "memory_cache_size": 3,
        "ips_ttl": 3600,
        "stale_ttl": 86400,
    })

    ips = IPSBundle(
        patient_id="P001",
        patient_name="João Silva",
        conditions=[{"code": "E11"}],
        medications=[{"code": "A10"}],
        source="florence",
    )
    mgr.get = AsyncMock(return_value=ips)
    mgr.invalidate = AsyncMock()

    val = ValidationResult(is_valid=True, errors=[], warnings=["No allergies registered"])
    mgr.validate = MagicMock(return_value=val)

    return mgr


@pytest.fixture
def app(mock_ips_manager):
    test_app = FastAPI()
    test_app.include_router(router)
    init_ips_routes(mock_ips_manager, ips_enricher=None)
    return test_app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestIPSStats:
    def test_stats(self, client):
        resp = client.get("/api/v1/ips/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["has_redis"] is False
        assert data["data"]["memory_cache_size"] == 3


class TestGetIPS:
    def test_get_ips(self, client):
        resp = client.get("/api/v1/ips/P001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["patient_id"] == "P001"
        assert data["data"]["source"] == "florence"


class TestInvalidateCache:
    def test_invalidate(self, client, mock_ips_manager):
        resp = client.delete("/api/v1/ips/P001/cache")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        mock_ips_manager.invalidate.assert_awaited_once_with("P001")


class TestValidateIPS:
    def test_validate(self, client):
        resp = client.get("/api/v1/ips/P001/validate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["validation"]["is_valid"] is True
        assert len(data["data"]["validation"]["warnings"]) == 1


class TestIPSNotInitialized:
    def test_503_when_no_manager(self):
        test_app = FastAPI()
        test_app.include_router(router)
        init_ips_routes(None)
        c = TestClient(test_app)
        resp = c.get("/api/v1/ips/stats")
        assert resp.status_code == 503
