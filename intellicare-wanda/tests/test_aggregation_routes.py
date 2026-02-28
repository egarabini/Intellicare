"""Tests for aggregation API endpoint (EF-W004)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from wanda.api.aggregation_routes import router as aggregation_router, init_aggregation_routes
from wanda.orchestrator.aggregator import ResponseAggregator


# ── Test App ───────────────────────────────────────────────────────────────

def make_test_app(intelligent_aggregator=None, simple_aggregator=None):
    simple = simple_aggregator or ResponseAggregator()
    app = FastAPI()
    app.include_router(aggregation_router)
    init_aggregation_routes(
        intelligent_aggregator=intelligent_aggregator,
        simple_aggregator=simple,
    )
    return app


# ── Tests ──────────────────────────────────────────────────────────────────

class TestAggregateEndpoint:
    def test_aggregate_with_simple_fallback(self):
        app = make_test_app()
        client = TestClient(app)

        response = client.post("/api/v1/aggregate", json={
            "query": "Como esta o paciente?",
            "responses": [
                {
                    "module_name": "intellicare-oswaldo",
                    "data": {"data": "DRC G3a estavel"},
                    "success": True,
                },
                {
                    "module_name": "intellicare-florence",
                    "data": {"data": "Exames normais"},
                    "success": True,
                },
            ]
        })

        assert response.status_code == 200
        data = response.json()
        assert "aggregated_response" in data
        assert data["aggregation_method"] == "simple"

    def test_aggregate_empty_responses_returns_400(self):
        app = make_test_app()
        client = TestClient(app)

        response = client.post("/api/v1/aggregate", json={
            "query": "Alguma pergunta",
            "responses": []
        })

        assert response.status_code == 400

    def test_aggregate_with_patient_context(self):
        app = make_test_app()
        client = TestClient(app)

        response = client.post("/api/v1/aggregate", json={
            "query": "Avaliacao do paciente",
            "responses": [
                {
                    "module_name": "intellicare-oswaldo",
                    "data": {"data": "OK"},
                    "success": True,
                }
            ],
            "patient_context": "Paciente com DRC G3",
        })

        assert response.status_code == 200
