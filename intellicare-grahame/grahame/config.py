"""Configuração do módulo Grahame."""

from pydantic_settings import BaseSettings


class GrahameConfig(BaseSettings):
    module_name: str = "intellicare-grahame"
    module_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"

    grahame_database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"
    multi_tenant_enabled: bool = False

    # URL de servidor FHIR externo (opcional — para federation futura)
    fhir_server_url: str = ""

    wanda_url: str = "http://localhost:8002"
    florence_url: str = "http://localhost:8002"
    geralda_url: str = "http://localhost:8006"
    ai_operation_timeout: int = 120
    on_behalf_of_enabled: bool = True
    custom_op_default_timeout: int = 30
    custom_op_rate_limit: int = 60
    custom_op_sandbox_enabled: bool = True

    class Config:
        env_prefix = "INTELLICARE_"
        env_file = ".env"
        extra = "ignore"


config = GrahameConfig()
