"""
Configuracao centralizada via pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / "infra" / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    postgres_user: str = "intellicare"
    postgres_password: str = "intellicare_dev_password"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "intellicare"

    redis_password: str = "redis_dev_password"
    redis_host: str = "localhost"
    redis_port: int = 6379

    keycloak_url: str = "http://localhost:8080"
    keycloak_internal_url: str = ""
    keycloak_realm: str = "intellicare"
    keycloak_client_id: str = "intellicare-service"

    ollama_host: str = "0.0.0.0"
    ollama_api_url: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_generate_model: str = "qwen2.5:7b"

    secret_key: str = "dev-secret-key-change-in-production"
    environment: str = "development"
    log_level: str = "DEBUG"

    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@intellicare.ia.br"

    @property
    def database_url(self) -> str:
        password = quote(self.postgres_password, safe="")
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def sync_database_url(self) -> str:
        password = quote(self.postgres_password, safe="")
        return (
            f"postgresql://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def keycloak_base_url(self) -> str:
        """URL interna (docker) tem prioridade sobre a externa."""
        return self.keycloak_internal_url or self.keycloak_url

    @property
    def keycloak_jwks_url(self) -> str:
        return (
            f"{self.keycloak_base_url}/realms/{self.keycloak_realm}"
            f"/protocol/openid-connect/certs"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
