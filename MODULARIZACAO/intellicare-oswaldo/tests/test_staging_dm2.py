"""Testes de estadiamento ADA (DM2)."""

from oswaldo.engine.staging.dm2_staging import ADAStagingStrategy
from oswaldo.engine.models import SeverityLevel
from oswaldo.profiles.registry import DiseaseProfileRegistry


class TestADAStaging:
    def test_controlled(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("dm2")
        strategy = ADAStagingStrategy(profile)
        result = strategy.calculate_stage({"hba1c": 6.5})
        assert result.stage == "CONTROLLED"
        assert result.severity == SeverityLevel.INFO

    def test_suboptimal(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("dm2")
        strategy = ADAStagingStrategy(profile)
        result = strategy.calculate_stage({"hba1c": 7.5})
        assert result.stage == "SUBOPTIMAL"
        assert result.severity == SeverityLevel.WARNING

    def test_poor(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("dm2")
        strategy = ADAStagingStrategy(profile)
        result = strategy.calculate_stage({"hba1c": 8.5})
        assert result.stage == "POOR"

    def test_very_poor(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("dm2")
        strategy = ADAStagingStrategy(profile)
        result = strategy.calculate_stage({"hba1c": 10.0})
        assert result.stage == "VERY_POOR"
        assert result.severity == SeverityLevel.CRITICAL

    def test_no_data(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("dm2")
        strategy = ADAStagingStrategy(profile)
        result = strategy.calculate_stage({"hba1c": None})
        assert result.stage == "UNKNOWN"
