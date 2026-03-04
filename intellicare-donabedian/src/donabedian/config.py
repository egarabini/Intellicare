"""
Configuration module for intellicare-donabedian.

Uses Pydantic Settings for environment variable management.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    intellicare_database_url: str = (
        "postgresql+asyncpg://admin_intellicare:Crazy#57LB@161.97.141.186:5432/IntellicareDB"
    )

    # Database Schema (isolamento por módulo)
    # Use None for SQLite tests (set DATABASE_SCHEMA="NONE" in environment)
    database_schema: str | None = None  # None allows search_path MT isolation

    @property
    def db_schema(self) -> str | None:
        """Get database schema, converting 'NONE' string to None."""
        if self.database_schema == "NONE":
            return None
        return self.database_schema

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    # Dashboard
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8501
    api_url: str = "http://localhost:8003"

    # Module Info
    module_name: str = "intellicare-donabedian"
    module_version: str = "1.0.0"
    module_description: str = (
        "Módulo de avaliação de qualidade assistencial baseado no framework de Donabedian"
    )

    # Environment
    environment: str = "development"

    # Logging
    log_level: str = "INFO"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


# Global settings instance
settings = Settings()

