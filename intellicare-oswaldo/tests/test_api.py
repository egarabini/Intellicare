"""Testes para API FastAPI do Oswaldo."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from oswaldo.api.app import _state, create_app
from oswaldo.config import OswaldoConfig
from oswaldo.engine.models import SeverityLevel, StagingResult
from oswaldo.profiles.registry import DiseaseProfileRegistry


PROFILES_DIR = Path(__file__).parent.parent / "oswaldo" / "profiles" / "diseases"


@pytest.fixture
def app_client(registry: DiseaseProfileRegistry) -> TestClient:
    """Cria client de teste com estado injetado (sem lifespan)."""
    app = create_app()
    mock_engine = MagicMock()
    mock_config = OswaldoConfig()
    _state["config"] = mock_config
    _state["registry"] = registry
    _state["engine"] = mock_engine
    _state["datastore"] = MagicMock()

    client = TestClient(app, raise_server_exceptions=False)
    yield client
    _state.clear()


@pytest.fixture
def mock_engine() -> MagicMock:
    return _state.get("engine")


class TestHealthEndpoint:
    def test_health_ok(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module_name"] == "intellicare-oswaldo"
        assert data["version"] == "1.0.0"
        assert "uptime_seconds" in data

    def test_health_degraded_no_registry(self, app_client: TestClient) -> None:
        _state["registry"] = DiseaseProfileRegistry(PROFILES_DIR)
        response = app_client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "degraded"


class TestInfoEndpoint:
    def test_info(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "intellicare-oswaldo"
        assert "chronic-disease-monitoring" in data["capabilities"]
        assert "diseases" in data["metadata"]
        assert "ckd" in data["metadata"]["diseases"]


class TestDiseasesEndpoint:
    def test_list_diseases(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/diseases")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        ids = [d["id"] for d in data]
        assert "ckd" in ids
        assert "dm2" in ids
        assert "has" in ids


class TestStagingEndpoint:
    def test_staging_single_disease(self, app_client: TestClient) -> None:
        engine = _state["engine"]
        engine.calculate_staging.return_value = StagingResult(
            disease_id="ckd",
            stage="G3a",
            stage_label="Moderately decreased",
            severity=SeverityLevel.WARNING,
            axes={"gfr": "G3a", "acr": "A1"},
            timestamp=datetime.now(timezone.utc),
            observations_used={"egfr": 45.0, "acr": 20.0},
        )
        response = app_client.get("/api/v1/staging/p-1?disease=ckd")
        assert response.status_code == 200
        data = response.json()
        assert data["stage"] == "G3a"
        assert data["disease_id"] == "ckd"

    def test_staging_all_diseases(self, app_client: TestClient) -> None:
        engine = _state["engine"]
        engine.calculate_staging.return_value = StagingResult(
            disease_id="ckd",
            stage="G1",
            stage_label="Normal",
            severity=SeverityLevel.INFO,
            axes={},
            timestamp=datetime.now(timezone.utc),
            observations_used={},
        )
        response = app_client.get("/api/v1/staging/p-1")
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "p-1"
        assert "staging" in data


class TestAlertsEndpoint:
    def test_alerts_empty(self, app_client: TestClient) -> None:
        engine = _state["engine"]
        engine.calculate_staging.return_value = StagingResult(
            disease_id="ckd",
            stage="G1",
            stage_label="Normal",
            severity=SeverityLevel.INFO,
            axes={},
            timestamp=datetime.now(timezone.utc),
            observations_used={},
        )
        engine.calculate_trends.return_value = {}
        engine.generate_alerts.return_value = []
        response = app_client.get("/api/v1/alerts/p-1")
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "p-1"
        assert isinstance(data["alerts"], list)
        assert data["total"] >= 0


class TestAnalyzeEndpoint:
    def test_analyze(self, app_client: TestClient) -> None:
        engine = _state["engine"]
        from oswaldo.engine.models import OswaldoPatientSummary
        engine.get_patient_summary.return_value = OswaldoPatientSummary(
            patient_id="p-1",
            diseases=["ckd"],
            staging_results={},
            trend_results={},
            alerts=[],
            last_updated=datetime.now(timezone.utc),
        )
        response = app_client.post("/api/v1/analyze?patient_id=p-1")
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == "p-1"
        assert "staging_results" in data

    def test_analyze_with_knowledge_context(self, app_client: TestClient) -> None:
        engine = _state["engine"]
        from oswaldo.engine.models import OswaldoPatientSummary
        engine.get_patient_summary.return_value = OswaldoPatientSummary(
            patient_id="p-1",
            diseases=["ckd"],
            staging_results={},
            trend_results={},
            alerts=[],
            last_updated=datetime.now(timezone.utc),
        )
        knowledge_client = AsyncMock()
        knowledge_client.query_rag.return_value = [{"id": "proto-1", "text": "conteudo"}]
        _state["knowledge_client"] = knowledge_client

        response = app_client.post("/api/v1/analyze?patient_id=p-1")
        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data
        assert "knowledge_context" in data["metadata"]
        assert data["metadata"]["knowledge_context"]["results_count"] == 1
