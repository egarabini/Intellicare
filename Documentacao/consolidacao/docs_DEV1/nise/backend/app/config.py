"""
============================================================================
NISE TRAINING MODULE - CONFIGURATION
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Application Configuration
Versão: 1.0
Data: 04/03/2026
Responsável: DEV2
============================================================================
"""

from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # ========================================================================
    # APPLICATION
    # ========================================================================
    APP_NAME: str = "NISE Training Module"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Sistema de Treinamento Assistido para Profissionais de Saúde"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # ========================================================================
    # API
    # ========================================================================
    API_V1_PREFIX: str = "/api/v1"
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    
    # ========================================================================
    # DATABASE - POSTGRESQL
    # ========================================================================
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="postgres", env="DB_PASSWORD")
    DB_NAME: str = Field(default="intellicare", env="DB_NAME")
    DB_SCHEMA: str = Field(default="nise_training", env="DB_SCHEMA")
    
    # Connection pool
    DB_POOL_SIZE: int = Field(default=10, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=20, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construir URL de conexão PostgreSQL"""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """URL síncrona (para migrations)"""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    # ========================================================================
    # PGVECTOR (RAG)
    # ========================================================================
    VECTOR_DIMENSION: int = 1536  # OpenAI embeddings dimension
    VECTOR_SIMILARITY_THRESHOLD: float = 0.7  # Threshold para RAG
    
    # ========================================================================
    # FHIR
    # ========================================================================
    FHIR_VERSION: str = "R4"
    FHIR_BASE_URL: str = Field(default="http://localhost:8000/api/v1/fhir", env="FHIR_BASE_URL")
    
    # ========================================================================
    # FLOWISE (RAG + Chatbot)
    # ========================================================================
    FLOWISE_ENABLED: bool = Field(default=False, env="FLOWISE_ENABLED")
    FLOWISE_URL: str = Field(default="http://localhost:3000", env="FLOWISE_URL")
    FLOWISE_API_KEY: Optional[str] = Field(default=None, env="FLOWISE_API_KEY")
    FLOWISE_CHATBOT_ID: Optional[str] = Field(default=None, env="FLOWISE_CHATBOT_ID")
    FLOWISE_DR_NISE_CHATFLOW_ID: str = Field(default="", env="FLOWISE_DR_NISE_CHATFLOW_ID")
    FLOWISE_EVALUATION_CHATFLOW_ID: str = Field(default="", env="FLOWISE_EVALUATION_CHATFLOW_ID")

    # ========================================================================
    # OLLAMA (LLM Engine)
    # ========================================================================
    OLLAMA_ENABLED: bool = Field(default=False, env="OLLAMA_ENABLED")
    OLLAMA_URL: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    OLLAMA_DEFAULT_MODEL: str = Field(default="llama2:7b", env="OLLAMA_DEFAULT_MODEL")
    OLLAMA_MODEL: str = Field(default="llama2:7b", env="OLLAMA_MODEL")
    OLLAMA_TIMEOUT: int = Field(default=60, env="OLLAMA_TIMEOUT")
    
    # ========================================================================
    # INTEGRATIONS - INTELLICARE MODULES
    # ========================================================================
    FLORENCE_URL: Optional[str] = Field(default=None, env="FLORENCE_URL")
    OSWALDO_URL: Optional[str] = Field(default=None, env="OSWALDO_URL")
    GERALDA_URL: Optional[str] = Field(default=None, env="GERALDA_URL")
    WANDA_URL: Optional[str] = Field(default=None, env="WANDA_URL")
    
    # ========================================================================
    # SYNTHETIC DATA GENERATION
    # ========================================================================
    SYNTHETIC_PATIENTS_COUNT: int = 5000
    SYNTHETIC_OBSERVATIONS_COUNT: int = 20000
    SYNTHETIC_PRACTITIONERS_COUNT: int = 1000
    SYNTHETIC_ENCOUNTERS_COUNT: int = 500
    SYNTHETIC_SCENARIOS_COUNT: int = 100
    
    # ========================================================================
    # TRAINING SYSTEM
    # ========================================================================
    TRAINING_SESSION_TIMEOUT: int = 3600  # 1 hora em segundos
    TRAINING_MAX_SCORE: float = 100.0
    TRAINING_PASS_SCORE: float = 70.0
    
    # ========================================================================
    # SECURITY
    # ========================================================================
    SECRET_KEY: str = Field(
        default="CHANGE_THIS_IN_PRODUCTION_VERY_SECRET_KEY_123456789",
        env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ========================================================================
    # CORS
    # ========================================================================
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080"
    ]
    
    # ========================================================================
    # LOGGING
    # ========================================================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ========================================================================
    # PERFORMANCE
    # ========================================================================
    API_RATE_LIMIT: int = 100  # requests per minute
    API_TIMEOUT: int = 30  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================
settings = Settings()

