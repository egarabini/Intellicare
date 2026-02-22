"""Configuracao do intellicare-superz."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class SuperZConfig:
    """Configuracao centralizada do modulo SuperZ / PIERRE."""

    # Tavily Web Search
    tavily_api_key: str = ""
    tavily_rate_limit_per_hour: int = 100
    tavily_search_depth: str = "advanced"

    # PubMed
    pubmed_api_key: str = ""
    pubmed_max_results: int = 10

    # Qwen / Ollama
    ollama_url: str = "http://ollama:11434"
    llm_model: str = "qwen2.5:72b"
    llm_model_fallback: str = "qwen2.5:7b"
    llm_timeout_seconds: int = 120
    llm_max_tokens: int = 500

    # Redis Cache
    redis_url: str = "redis://redis:6379/1"
    cache_enabled: bool = True

    # Limites
    max_text_length_chars: int = 100_000

    # API
    port: int = 8009
    workers: int = 2

    # Integracao intellicare-conhecimento
    enable_knowledge_integration: bool = False
    knowledge_base_url: str = "http://localhost:8010"
    knowledge_timeout_seconds: float = 3.0

    @classmethod
    def from_env(cls) -> SuperZConfig:
        """Cria configuracao a partir de variaveis de ambiente."""
        return cls(
            tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
            tavily_rate_limit_per_hour=int(os.getenv("SUPERZ_TAVILY_RATE_LIMIT_PER_HOUR", "100")),
            tavily_search_depth=os.getenv("SUPERZ_TAVILY_SEARCH_DEPTH", "advanced"),
            pubmed_api_key=os.getenv("NCBI_API_KEY", ""),
            pubmed_max_results=int(os.getenv("SUPERZ_PUBMED_MAX_RESULTS", "10")),
            ollama_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
            llm_model=os.getenv("SUPERZ_LLM_MODEL", "qwen2.5:72b"),
            llm_model_fallback=os.getenv("SUPERZ_LLM_MODEL_FALLBACK", "qwen2.5:7b"),
            llm_timeout_seconds=int(os.getenv("SUPERZ_LLM_TIMEOUT_SECONDS", "120")),
            llm_max_tokens=int(os.getenv("SUPERZ_LLM_MAX_TOKENS", "500")),
            redis_url=os.getenv("REDIS_URL", "redis://redis:6379/1"),
            cache_enabled=os.getenv("SUPERZ_CACHE_ENABLED", "true").lower() == "true",
            max_text_length_chars=int(os.getenv("SUPERZ_MAX_TEXT_LENGTH", "100000")),
            port=int(os.getenv("SUPERZ_PORT", "8009")),
            workers=int(os.getenv("SUPERZ_WORKERS", "2")),
            enable_knowledge_integration=(
                os.getenv("SUPERZ_ENABLE_KNOWLEDGE_INTEGRATION", "false").lower() == "true"
            ),
            knowledge_base_url=os.getenv("SUPERZ_KNOWLEDGE_BASE_URL", "http://localhost:8010"),
            knowledge_timeout_seconds=float(os.getenv("SUPERZ_KNOWLEDGE_TIMEOUT_SECONDS", "3.0")),
        )

    @property
    def tavily_configured(self) -> bool:
        """Verifica se Tavily API key esta configurada."""
        return bool(self.tavily_api_key and self.tavily_api_key != "tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

    @property
    def pubmed_has_key(self) -> bool:
        """Verifica se PubMed API key esta configurada (melhora rate limit)."""
        return bool(self.pubmed_api_key)
