"""Excecoes do intellicare-pierre."""

from __future__ import annotations


class SuperZError(Exception):
    """Erro base do SuperZ."""


class TavilyUnavailableError(SuperZError):
    """Tavily API nao configurada ou fora do ar."""


class TavilyRateLimitError(SuperZError):
    """Rate limit atingido."""


class LLMUnavailableError(SuperZError):
    """Ollama / modelo LLM indisponivel."""


class NoResultsFoundError(SuperZError):
    """Query valida mas sem resultados."""
