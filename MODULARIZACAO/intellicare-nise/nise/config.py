"""Configuração do NISE."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configurações do NISE."""
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False
    
    # Database
    database_url: str = "postgresql://intellicare:intellicare@localhost:5432/intellicare_nise"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 300  # 5 minutes
    
    # Oswaldo Integration
    oswaldo_base_url: str = "http://localhost:8002"
    oswaldo_timeout: float = 10.0
    
    # Flowise Integration
    flowise_url: str = "http://localhost:3000"
    flowise_api_key: str = ""
    flowise_password: str = "admin123"
    
    # Ollama Integration
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama2:7b"

    # Kestra Integration
    kestra_url: str = "http://localhost:8080"
    kestra_api_key: str = ""
    kestra_timeout: float = 30.0

    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "bemcuidar"
    keycloak_client_id: str = "intellicare-nise"
    keycloak_client_secret: str = ""
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    cors_allow_credentials: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Singleton instance
settings = Settings()

