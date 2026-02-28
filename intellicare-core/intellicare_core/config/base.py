"""Configuracao base para modulos IntelliCare.

Todos os modulos IntelliCare herdam desta classe para ter configuracao
padronizada via variaveis de ambiente.

Exemplo de uso:
    class OswaldoConfig(BaseModuleConfig):
        module_name: str = "intellicare-oswaldo"
        module_version: str = "1.0.0"
        profiles_dir: str = "./profiles/diseases"

    config = OswaldoConfig()  # Carrega de .env e variaveis de ambiente
"""

from __future__ import annotations

from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Ambientes de execucao."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Niveis de log suportados."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class BaseModuleConfig(BaseSettings):
    """Configuracao base que todo modulo IntelliCare deve estender.

    Carrega configuracoes de variaveis de ambiente com prefixo INTELLICARE_.
    Exemplo: INTELLICARE_FHIR_SERVER_URL=http://localhost:8080/fhir
    """

    model_config = SettingsConfigDict(
        env_prefix="INTELLICARE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Identificacao do modulo (cada modulo sobrescreve)
    module_name: str = "intellicare-module"
    module_version: str = "0.0.0"

    # Ambiente
    environment: Environment = Environment.DEVELOPMENT
    log_level: LogLevel = LogLevel.INFO

    # FHIR Server
    fhir_server_url: str = "http://localhost:8080/fhir"
    fhir_timeout_seconds: int = 30

    # Database (cada modulo define seu proprio banco)
    database_url: str = ""

    # Redis (para eventos entre modulos)
    redis_url: str = "redis://localhost:6379"

    # Multi-tenancy
    multi_tenant_enabled: bool = False
    default_tenant_id: str = "default"

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_debug(self) -> bool:
        return self.log_level == LogLevel.DEBUG
