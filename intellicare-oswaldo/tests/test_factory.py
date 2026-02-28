"""Testes para StagingStrategyFactory."""

from oswaldo.engine.staging.factory import StagingStrategyFactory
from oswaldo.engine.staging.ckd_staging import KDIGOStagingStrategy
from oswaldo.engine.staging.dm2_staging import ADAStagingStrategy
from oswaldo.engine.staging.has_staging import ESCESHStagingStrategy
from oswaldo.profiles.registry import DiseaseProfileRegistry


class TestStagingStrategyFactory:
    def test_creates_kdigo(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("ckd")
        strategy = StagingStrategyFactory.create(profile)
        assert isinstance(strategy, KDIGOStagingStrategy)

    def test_creates_ada(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("dm2")
        strategy = StagingStrategyFactory.create(profile)
        assert isinstance(strategy, ADAStagingStrategy)

    def test_creates_escesh(self, registry: DiseaseProfileRegistry) -> None:
        profile = registry.get("has")
        strategy = StagingStrategyFactory.create(profile)
        assert isinstance(strategy, ESCESHStagingStrategy)

    def test_list_strategies(self) -> None:
        strategies = StagingStrategyFactory.list_strategies()
        assert "kdigo" in strategies
        assert "ada" in strategies
        assert "escesh" in strategies
        assert "generic_range" in strategies
