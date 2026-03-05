import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "IntelliCare Gestor"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1/gestor"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    KEYCLOAK_SERVER_URL: str = os.getenv("KEYCLOAK_SERVER_URL", "http://localhost:8080/")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "intellicare-gestor")
    KEYCLOAK_CLIENT_SECRET: str = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "bemcuidar")
    MULTI_TENANT_ENABLED: bool = os.getenv("INTELLICARE_MULTI_TENANT_ENABLED", "false").lower() == "true"
    
    # Aliases
    @property
    def multi_tenant_enabled(self) -> bool:
        return self.MULTI_TENANT_ENABLED

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
