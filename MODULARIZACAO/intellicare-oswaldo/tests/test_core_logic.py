"""Testes para ChronicDiseaseEngine com mocks."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from oswaldo.engine.core_logic import ChronicDiseaseEngine
from oswaldo.engine.models import SeverityLevel, StagingResult, TrendDirection, TrendResult
from oswaldo.profiles.models import AlertConfig, DiseaseProfile, ObservationConfig, StagingConfig
from oswaldo.profiles.registry import DiseaseProfileRegistry


@pytest.fixture
def mock_datastore() -> MagicMock:
    return MagicMock()


@pytest.fixture
def engine(mock_datastore: MagicMock, registry: DiseaseProfileRegistry) -> ChronicDiseaseEngine:
    return ChronicDiseaseEngine(mock_datastore, registry)


class TestChronicDiseaseEngine:
    def test_init(self, engine: ChronicDiseaseEngine, registry: DiseaseProfileRegistry) -> None:
        assert engine.registry is registry
        assert engine.datastore is not None

    def test_calculate_staging_ckd(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.search_resources.return_value = [
            {"valueQuantity": {"value": 45.0}},
        ]
        result = engine.calculate_staging("p-1", "ckd")
        assert isinstance(result, StagingResult)
        assert result.disease_id == "ckd"

    def test_calculate_staging_dm2(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.search_resources.return_value = [
            {"valueQuantity": {"value": 7.5}},
        ]
        result = engine.calculate_staging("p-1", "dm2")
        assert isinstance(result, StagingResult)
        assert result.disease_id == "dm2"

    def test_calculate_staging_has(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.search_resources.return_value = [
            {"valueQuantity": {"value": 150.0}},
        ]
        result = engine.calculate_staging("p-1", "has")
        assert isinstance(result, StagingResult)
        assert result.disease_id == "has"

    def test_calculate_staging_missing_profile(self, engine: ChronicDiseaseEngine) -> None:
        with pytest.raises(ValueError, match="nao encontrado"):
            engine.calculate_staging("p-1", "nonexistent")

    def test_calculate_trends_insufficient_data(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.search_resources.return_value = []
        trends = engine.calculate_trends("p-1", "ckd")
        assert len(trends) >= 5  # CKD has at least 5 observations
        for trend in trends.values():
            assert trend.direction == TrendDirection.INSUFFICIENT_DATA

    def test_calculate_trends_with_data(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.search_resources.return_value = [
            {"valueQuantity": {"value": 45.0}},
            {"valueQuantity": {"value": 55.0}},
        ]
        trends = engine.calculate_trends("p-1", "ckd")
        assert len(trends) >= 5
        for trend in trends.values():
            assert isinstance(trend, TrendResult)
            assert trend.data_points == 2

    def test_calculate_trends_missing_profile(self, engine: ChronicDiseaseEngine) -> None:
        with pytest.raises(ValueError, match="nao encontrado"):
            engine.calculate_trends("p-1", "nonexistent")

    def test_generate_alerts_empty(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.search_resources.return_value = []
        staging = StagingResult(
            disease_id="ckd",
            stage="G3a",
            stage_label="G3a",
            severity=SeverityLevel.WARNING,
            axes={"gfr": "G3a"},
            timestamp=datetime.now(timezone.utc),
            observations_used={},
        )
        alerts = engine.generate_alerts("p-1", "ckd", staging, {})
        assert isinstance(alerts, list)

    def test_generate_alerts_nonexistent_profile(self, engine: ChronicDiseaseEngine) -> None:
        staging = StagingResult(
            disease_id="nonexistent",
            stage="X",
            stage_label="X",
            severity=SeverityLevel.INFO,
            axes={},
            timestamp=datetime.now(timezone.utc),
            observations_used={},
        )
        alerts = engine.generate_alerts("p-1", "nonexistent", staging, {})
        assert alerts == []

    def test_get_patient_summary(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.get_resource_by_type.return_value = {
            "resourceType": "Patient",
            "id": "p-1",
            "name": [{"text": "Test Patient"}],
        }
        mock_datastore.search_resources.return_value = [
            {"valueQuantity": {"value": 45.0}},
        ]
        summary = engine.get_patient_summary("p-1", ["ckd"])
        assert summary.patient_id == "p-1"
        assert "ckd" in summary.diseases
        assert isinstance(summary.staging_results, dict)
        assert isinstance(summary.alerts, list)

    def test_get_patient_summary_patient_not_found(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.get_resource_by_type.return_value = None
        with pytest.raises(ValueError, match="nao encontrado"):
            engine.get_patient_summary("nonexistent")

    def test_get_patient_summary_all_diseases(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.get_resource_by_type.return_value = {
            "resourceType": "Patient",
            "id": "p-1",
        }
        mock_datastore.search_resources.return_value = [
            {"valueQuantity": {"value": 120.0}},
        ]
        summary = engine.get_patient_summary("p-1")
        assert len(summary.diseases) >= 3  # ckd, dm2, has

    def test_extract_observation_value_from_quantity(
        self, engine: ChronicDiseaseEngine
    ) -> None:
        obs = {"valueQuantity": {"value": 42.5}}
        value = engine._extract_observation_value(obs)
        assert value == 42.5

    def test_extract_observation_value_from_component(
        self, engine: ChronicDiseaseEngine
    ) -> None:
        obs = {
            "component": [
                {"valueQuantity": {"value": 130.0}},
            ]
        }
        value = engine._extract_observation_value(obs)
        assert value == 130.0

    def test_extract_observation_value_none(self, engine: ChronicDiseaseEngine) -> None:
        obs = {}
        value = engine._extract_observation_value(obs)
        assert value is None

    def test_determine_trend_direction_stable(self, engine: ChronicDiseaseEngine) -> None:
        direction = engine._determine_trend_direction(100.0, 100.5, "higher_is_better")
        assert direction == TrendDirection.STABLE

    def test_determine_trend_direction_improving_higher(self, engine: ChronicDiseaseEngine) -> None:
        direction = engine._determine_trend_direction(80.0, 50.0, "higher_is_better")
        assert direction == TrendDirection.IMPROVING

    def test_determine_trend_direction_worsening_higher(self, engine: ChronicDiseaseEngine) -> None:
        direction = engine._determine_trend_direction(30.0, 50.0, "higher_is_better")
        assert direction == TrendDirection.WORSENING

    def test_determine_trend_direction_improving_lower(self, engine: ChronicDiseaseEngine) -> None:
        direction = engine._determine_trend_direction(5.0, 10.0, "lower_is_better")
        assert direction == TrendDirection.IMPROVING

    def test_determine_trend_direction_worsening_lower(self, engine: ChronicDiseaseEngine) -> None:
        direction = engine._determine_trend_direction(15.0, 10.0, "lower_is_better")
        assert direction == TrendDirection.WORSENING

    def test_determine_trend_direction_unknown_desired(self, engine: ChronicDiseaseEngine) -> None:
        direction = engine._determine_trend_direction(50.0, 30.0, "unknown")
        assert direction == TrendDirection.STABLE

    def test_to_dict_summary(
        self, engine: ChronicDiseaseEngine, mock_datastore: MagicMock
    ) -> None:
        mock_datastore.get_resource_by_type.return_value = {"id": "p-1", "resourceType": "Patient"}
        mock_datastore.search_resources.return_value = [{"valueQuantity": {"value": 45.0}}]
        summary = engine.get_patient_summary("p-1", ["ckd"])
        d = summary.to_dict()
        assert d["patient_id"] == "p-1"
        assert "staging_results" in d
        assert "trend_results" in d
        assert "alerts" in d
