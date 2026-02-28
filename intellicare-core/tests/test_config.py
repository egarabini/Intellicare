"""Testes para o modulo de configuracao."""

import os

import pytest

from intellicare_core.config.base import BaseModuleConfig, Environment, LogLevel


class TestBaseModuleConfig:
    """Testes para BaseModuleConfig."""

    def test_default_values(self) -> None:
        config = BaseModuleConfig()
        assert config.module_name == "intellicare-module"
        assert config.module_version == "0.0.0"
        assert config.environment == Environment.DEVELOPMENT
        assert config.log_level == LogLevel.INFO
        assert config.fhir_server_url == "http://localhost:8080/fhir"
        assert config.fhir_timeout_seconds == 30
        assert config.redis_url == "redis://localhost:6379"

    def test_custom_values(self) -> None:
        config = BaseModuleConfig(
            module_name="intellicare-oswaldo",
            module_version="1.0.0",
            environment=Environment.PRODUCTION,
            log_level=LogLevel.ERROR,
            fhir_server_url="http://fhir.example.com/fhir",
            database_url="postgresql://user:pass@localhost/db",
        )
        assert config.module_name == "intellicare-oswaldo"
        assert config.module_version == "1.0.0"
        assert config.environment == Environment.PRODUCTION
        assert config.is_production is True
        assert config.is_debug is False
        assert config.database_url == "postgresql://user:pass@localhost/db"

    def test_env_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("INTELLICARE_MODULE_NAME", "from-env")
        monkeypatch.setenv("INTELLICARE_LOG_LEVEL", "DEBUG")
        config = BaseModuleConfig()
        assert config.module_name == "from-env"
        assert config.log_level == LogLevel.DEBUG
        assert config.is_debug is True

    def test_is_production_false_by_default(self) -> None:
        config = BaseModuleConfig()
        assert config.is_production is False

    def test_inheritance(self) -> None:
        """Modulos devem poder herdar e adicionar campos."""

        class OswaldoConfig(BaseModuleConfig):
            module_name: str = "intellicare-oswaldo"
            profiles_dir: str = "./profiles"

        config = OswaldoConfig()
        assert config.module_name == "intellicare-oswaldo"
        assert config.profiles_dir == "./profiles"
        assert config.fhir_server_url == "http://localhost:8080/fhir"


class TestEnvironmentEnum:
    def test_values(self) -> None:
        assert Environment.DEVELOPMENT == "development"
        assert Environment.STAGING == "staging"
        assert Environment.PRODUCTION == "production"


class TestLogLevelEnum:
    def test_values(self) -> None:
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
