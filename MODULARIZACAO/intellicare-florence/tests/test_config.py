"""Testes para FlorenceConfig."""

import pytest

from florence.config import FlorenceConfig


class TestFlorenceConfig:
    def test_defaults(self) -> None:
        config = FlorenceConfig()
        assert config.module_name == "intellicare-florence"
        assert config.module_version == "1.0.0"
        assert config.trend_min_data_points == 3
        assert config.trend_default_period_days == 180
        assert config.enable_rag is False
        assert config.enable_knowledge_integration is False

    def test_custom_values(self) -> None:
        config = FlorenceConfig(
            trend_min_data_points=5,
            enable_rag=True,
        )
        assert config.trend_min_data_points == 5
        assert config.enable_rag is True

    def test_invalid_min_data_points(self) -> None:
        with pytest.raises(ValueError):
            FlorenceConfig(trend_min_data_points=1)

    def test_inherits_base_config(self) -> None:
        config = FlorenceConfig()
        assert hasattr(config, "fhir_server_url")
        assert hasattr(config, "database_url")
        assert hasattr(config, "environment")
