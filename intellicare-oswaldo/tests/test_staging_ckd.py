"""Testes de estadiamento KDIGO (CKD)."""

import pytest

from oswaldo.engine.staging.ckd_staging import KDIGOStagingStrategy
from oswaldo.engine.models import SeverityLevel
from oswaldo.profiles.registry import DiseaseProfileRegistry


class TestKDIGOStaging:
    def test_g1_a1(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("ckd")
        strategy = KDIGOStagingStrategy(profile)
        result = strategy.calculate_stage({"egfr": 95.0, "acr": 15.0})
        assert result.stage == "G1_A1"
        assert result.severity == SeverityLevel.INFO

    def test_g3a_a2(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("ckd")
        strategy = KDIGOStagingStrategy(profile)
        result = strategy.calculate_stage({"egfr": 52.3, "acr": 45.0})
        assert result.stage == "G3a_A2"
        assert result.severity == SeverityLevel.WARNING
        assert result.axes["gfr"] == "G3a"
        assert result.axes["acr"] == "A2"

    def test_g5_a3(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("ckd")
        strategy = KDIGOStagingStrategy(profile)
        result = strategy.calculate_stage({"egfr": 10.0, "acr": 500.0})
        assert result.stage == "G5_A3"
        assert result.severity == SeverityLevel.CRITICAL

    def test_only_egfr(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("ckd")
        strategy = KDIGOStagingStrategy(profile)
        result = strategy.calculate_stage({"egfr": 45.0, "acr": None})
        assert result.stage == "G3a"

    def test_no_data(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("ckd")
        strategy = KDIGOStagingStrategy(profile)
        result = strategy.calculate_stage({"egfr": None, "acr": None})
        assert result.stage == "UNKNOWN"

    def test_g4(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("ckd")
        strategy = KDIGOStagingStrategy(profile)
        result = strategy.calculate_stage({"egfr": 20.0, "acr": None})
        assert result.stage == "G4"
        assert result.severity == SeverityLevel.CRITICAL
