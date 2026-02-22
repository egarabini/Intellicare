"""Configuracao do Florence."""

from pathlib import Path

from pydantic import field_validator

from intellicare_core.config import BaseModuleConfig


class FlorenceConfig(BaseModuleConfig):
    """Configuracao especifica do Florence."""

    module_name: str = "intellicare-florence"
    module_version: str = "1.0.0"

    # Diretorio de reference ranges
    reference_ranges_dir: str = str(Path(__file__).parent / "engine" / "reference_ranges" / "data")

    # Diretorio de correlacoes
    correlations_dir: str = str(Path(__file__).parent / "engine" / "correlations" / "data")

    # Analise de tendencias
    trend_min_data_points: int = 3
    trend_default_period_days: int = 180

    # RAG (Retrieval-Augmented Generation)
    rag_chroma_dir: str = "./data/chroma"
    rag_protocols_dir: str = str(Path(__file__).parent / "engine" / "rag" / "data" / "protocols")
    rag_top_k_default: int = 3

    # Feature flags
    enable_rag: bool = False
    enable_diagnostic_support: bool = False
    enable_knowledge_integration: bool = False

    # Integracao intellicare-conhecimento
    knowledge_base_url: str = "http://localhost:8010"
    knowledge_timeout_seconds: float = 3.0

    @field_validator("trend_min_data_points")
    @classmethod
    def validate_min_data_points(cls, v: int) -> int:
        if v < 2:
            raise ValueError("trend_min_data_points deve ser >= 2")
        return v
