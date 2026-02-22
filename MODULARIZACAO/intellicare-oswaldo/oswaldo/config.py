"""Configuracao do Oswaldo — estende BaseModuleConfig do intellicare-core."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import AliasChoices, SettingsConfigDict

from intellicare_core.config import BaseModuleConfig


class OswaldoConfig(BaseModuleConfig):
    """Configuracao do agente Oswaldo.

    Carrega de variaveis de ambiente com prefixo INTELLICARE_.
    """

    model_config = SettingsConfigDict(
        env_prefix="INTELLICARE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    module_name: str = "intellicare-oswaldo"
    module_version: str = "1.0.0"

    # Database URL - aceita INTELLICARE_OSWALDO_DATABASE_URL ou INTELLICARE_DATABASE_URL
    database_url: str = Field(
        default="",
        validation_alias=AliasChoices("INTELLICARE_OSWALDO_DATABASE_URL", "INTELLICARE_DATABASE_URL"),
    )

    # Diretorio com perfis YAML de doencas
    profiles_dir: str = str(Path(__file__).parent / "profiles" / "diseases")

    # Features
    enable_medication_advisor: bool = False
    enable_cv_risk_calculator: bool = False
    enable_knowledge_integration: bool = False

    # Integracao intellicare-conhecimento
    knowledge_base_url: str = "http://localhost:8010"
    knowledge_timeout_seconds: float = 3.0

    # Analise de tendencias
    trend_analysis_days: int = 90
    alert_threshold_critical: float = 0.9
    alert_threshold_warning: float = 0.7

    @field_validator("trend_analysis_days")
    @classmethod
    def validate_trend_days(cls, v: int) -> int:
        if v < 30:
            raise ValueError("trend_analysis_days deve ser >= 30")
        return v
