"""Testes para OswaldoConfig."""

import pytest

from oswaldo.config import OswaldoConfig


class TestOswaldoConfig:
    def test_defaults(self) -> None:
        config = OswaldoConfig()
        assert config.module_name == "intellicare-oswaldo"
        assert config.module_version == "1.0.0"
        assert config.trend_analysis_days == 90
        assert config.enable_medication_advisor is False
        assert config.enable_knowledge_integration is False

    def test_custom_values(self) -> None:
        config = OswaldoConfig(
            trend_analysis_days=180,
            enable_cv_risk_calculator=True,
        )
        assert config.trend_analysis_days == 180
        assert config.enable_cv_risk_calculator is True

    def test_invalid_trend_days(self) -> None:
        with pytest.raises(ValueError):
            OswaldoConfig(trend_analysis_days=10)

    def test_inherits_base_config(self) -> None:
        config = OswaldoConfig()
        assert hasattr(config, "fhir_server_url")
        assert hasattr(config, "database_url")
        assert hasattr(config, "environment")
        assert hasattr(config, "is_production")
