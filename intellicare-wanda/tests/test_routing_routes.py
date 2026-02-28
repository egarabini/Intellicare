"""Tests for routing API endpoints (EF-W003)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from wanda.api.routing_routes import router as routing_router, init_routing_routes
from wanda.discovery.models import ModuleInfo, ModuleStatus, RoutingDecision
from fastapi import FastAPI


# ── Test App ───────────────────────────────────────────────────────────────

def make_test_app(intent_router=None, keyword_router=None, registry=None):
    app = FastAPI()
    app.include_router(routing_router)
    init_routing_routes(
        intent_router=intent_router,
        keyword_router=keyword_router,
        registry=registry,
    )
    return app


def make_mock_registry(modules=None):
    registry = MagicMock()
    registry.get_online_modules.return_value = modules or [
        ModuleInfo(
            name="intellicare-oswaldo",
            base_url="http://localhost:8001",
            capabilities=["chronic-disease-monitoring"],
            status=ModuleStatus.ONLINE,
        )
    ]
    return registry


def make_mock_keyword_router():
    router = MagicMock()
    router.route.return_value = RoutingDecision(
        target_modules=["intellicare-oswaldo"],
        reason="Keyword match: diabetes",
        confidence=0.8,
        routing_method="keyword",
    )
    return router


# ── Tests ──────────────────────────────────────────────────────────────────

class TestRoutingExplain:
    def test_explain_with_keyword_router(self):
        app = make_test_app(
            keyword_router=make_mock_keyword_router(),
            registry=make_mock_registry(),
        )
        client = TestClient(app)

        response = client.post("/api/v1/routing/explain", json={
            "query": "Como esta o diabetes do paciente?"
        })

        assert response.status_code == 200
        data = response.json()
        assert "target_modules" in data
        assert "routing_method" in data
        assert data["routing_method"] == "keyword"

    def test_explain_no_modules_available(self):
        registry = MagicMock()
        registry.get_online_modules.return_value = []

        app = make_test_app(registry=registry, keyword_router=make_mock_keyword_router())
        client = TestClient(app)

        response = client.post("/api/v1/routing/explain", json={
            "query": "Alguma consulta"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["target_modules"] == []

    def test_explain_no_registry_returns_503(self):
        from wanda.api import routing_routes
        # Reset registry to None
        routing_routes._registry = None
        routing_routes._intent_router = None
        routing_routes._keyword_router = None

        app = FastAPI()
        app.include_router(routing_router)

        client = TestClient(app)
        response = client.post("/api/v1/routing/explain", json={
            "query": "Alguma consulta"
        })
        assert response.status_code == 503

    def test_explain_with_patient_id(self):
        app = make_test_app(
            keyword_router=make_mock_keyword_router(),
            registry=make_mock_registry(),
        )
        client = TestClient(app)

        response = client.post("/api/v1/routing/explain", json={
            "query": "Avaliacao do paciente",
            "patient_id": "P001",
        })

        assert response.status_code == 200


class TestRoutingMethod:
    def test_returns_keyword_method_by_default(self):
        app = make_test_app(registry=make_mock_registry())
        client = TestClient(app)

        response = client.get("/api/v1/routing/method")

        assert response.status_code == 200
        data = response.json()
        assert "routing_method" in data
        assert "llm_available" in data
        assert data["llm_available"] is False

    def test_returns_llm_method_when_intent_router_available(self):
        mock_intent_router = AsyncMock()
        app = make_test_app(
            intent_router=mock_intent_router,
            registry=make_mock_registry(),
        )
        client = TestClient(app)

        response = client.get("/api/v1/routing/method")

        assert response.status_code == 200
        data = response.json()
        assert data["llm_available"] is True
        assert data["routing_method"] == "llm"
