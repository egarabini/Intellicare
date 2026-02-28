"""Testes de estadiamento ESC/ESH (HAS)."""

from oswaldo.engine.staging.has_staging import ESCESHStagingStrategy
from oswaldo.engine.models import SeverityLevel
from oswaldo.profiles.registry import DiseaseProfileRegistry


class TestESCESHStaging:
    def test_optimal(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("has")
        strategy = ESCESHStagingStrategy(profile)
        result = strategy.calculate_stage({"systolic_bp": 110.0, "diastolic_bp": 70.0})
        assert result.stage == "OPTIMAL"
        assert result.severity == SeverityLevel.INFO

    def test_grade1(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("has")
        strategy = ESCESHStagingStrategy(profile)
        result = strategy.calculate_stage({"systolic_bp": 150.0, "diastolic_bp": 92.0})
        assert result.stage == "GRADE1"
        assert result.severity == SeverityLevel.WARNING

    def test_grade3_crisis(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("has")
        strategy = ESCESHStagingStrategy(profile)
        result = strategy.calculate_stage({"systolic_bp": 190.0, "diastolic_bp": 115.0})
        assert result.stage == "GRADE3"
        assert result.severity == SeverityLevel.CRITICAL

    def test_no_data(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("has")
        strategy = ESCESHStagingStrategy(profile)
        result = strategy.calculate_stage({"systolic_bp": None, "diastolic_bp": None})
        assert result.stage == "UNKNOWN"

    def test_normal(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("has")
        strategy = ESCESHStagingStrategy(profile)
        result = strategy.calculate_stage({"systolic_bp": 125.0, "diastolic_bp": 78.0})
        assert result.stage == "NORMAL"
