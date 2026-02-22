"""Testes para API FastAPI do Florence."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from florence.api.app import _state, create_app
from florence.config import FlorenceConfig
from florence.engine.clinical_analyzer import ClinicalAnalyzer
from florence.engine.correlations.detector import CorrelationDetector
from florence.engine.reference_ranges.loader import ReferenceRangeLoader
from florence.engine.trend_detector import TrendDetector


REFERENCE_RANGES_DIR = Path(__file__).parent.parent / "florence" / "engine" / "reference_ranges" / "data"
CORRELATIONS_DIR = Path(__file__).parent.parent / "florence" / "engine" / "correlations" / "data"


@pytest.fixture
def app_client() -> TestClient:
    """Cria client de teste com estado injetado."""
    app = create_app()
    config = FlorenceConfig()
    ref_loader = ReferenceRangeLoader(REFERENCE_RANGES_DIR)
    ref_loader.load_all()
    corr_detector = CorrelationDetector(CORRELATIONS_DIR)
    corr_detector.load_all()
    trend_detector = TrendDetector(min_data_points=3)
    analyzer = ClinicalAnalyzer(ref_loader, corr_detector, trend_detector)

    _state["config"] = config
    _state["ref_loader"] = ref_loader
    _state["corr_detector"] = corr_detector
    _state["analyzer"] = analyzer

    client = TestClient(app, raise_server_exceptions=False)
    yield client
    _state.clear()


class TestHealthEndpoint:
    def test_health_ok(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module_name"] == "intellicare-florence"

    def test_health_degraded(self, app_client: TestClient) -> None:
        _state["ref_loader"] = ReferenceRangeLoader("/nonexistent")
        response = app_client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "degraded"


class TestInfoEndpoint:
    def test_info(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "intellicare-florence"
        assert "lab-interpretation" in data["capabilities"]
        assert "labs_available" in data["metadata"]


class TestPanelsEndpoint:
    def test_list_panels(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/panels")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 6
        panel_ids = [p["id"] for p in data]
        assert "renal_panel" in panel_ids


class TestLabsEndpoint:
    def test_list_labs(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/labs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 20
        lab_ids = [l["id"] for l in data]
        assert "creatinine" in lab_ids


class TestInterpretEndpoint:
    def test_interpret_normal(self, app_client: TestClient) -> None:
        response = app_client.post("/api/v1/interpret", json={
            "patient_id": "p-1",
            "results": {"creatinine": 1.0, "hemoglobin": 14.0},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "p-1"
        assert len(data["interpretations"]) == 2
        assert data["significance"] == "routine"

    def test_interpret_abnormal(self, app_client: TestClient) -> None:
        response = app_client.post("/api/v1/interpret", json={
            "patient_id": "p-1",
            "results": {"creatinine": 5.0, "urea": 120.0},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["significance"] in ("urgent", "critical")
        assert len(data["correlations"]) >= 1


class TestAnalyzeEndpoint:
    def test_analyze_simple(self, app_client: TestClient) -> None:
        response = app_client.post("/api/v1/analyze", json={
            "patient_id": "p-1",
            "results": {"creatinine": 1.0, "glucose_fasting": 85.0},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "p-1"
        assert "summary" in data

    def test_analyze_with_trends(self, app_client: TestClient) -> None:
        response = app_client.post("/api/v1/analyze", json={
            "patient_id": "p-1",
            "results": {"creatinine": 2.5},
            "historical": {
                "creatinine": [
                    {"timestamp": "2024-01-01T00:00:00+00:00", "value": 1.0},
                    {"timestamp": "2024-02-01T00:00:00+00:00", "value": 1.5},
                    {"timestamp": "2024-03-01T00:00:00+00:00", "value": 2.0},
                    {"timestamp": "2024-04-01T00:00:00+00:00", "value": 2.5},
                ],
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["trends"]) == 1


class TestKnowledgeIntegration:
    def test_rag_query_with_external_knowledge(self, app_client: TestClient) -> None:
        _state["rag_retriever"] = None
        knowledge_client = AsyncMock()
        knowledge_client.query_rag.return_value = [
            {
                "id": "proto-1",
                "source": "protocol",
                "score": 0.87,
                "metadata": {"title": "KDIGO CKD"},
                "text": "conteudo do protocolo",
            }
        ]
        _state["knowledge_client"] = knowledge_client

        response = app_client.post(
            "/api/v1/rag/query",
            json={"query": "DRC KDIGO", "top_k": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "DRC KDIGO"
        assert data["total_results"] == 1
        assert data["results"][0]["protocol_id"] == "proto-1"
