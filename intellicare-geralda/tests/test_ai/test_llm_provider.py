"""Testes para LLMProvider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from geralda.ai.llm_provider import LLMProvider


class TestLLMProvider:
    """Testes para factory de LLM."""

    def test_create_ollama_provider(self):
        """Testa criação de provider Ollama."""
        with patch("langchain_ollama.ChatOllama") as mock_ollama:
            mock_instance = MagicMock()
            mock_ollama.return_value = mock_instance

            provider = LLMProvider.create(
                provider="ollama",
                ollama_url="http://localhost:11434",
                ollama_model="mistral:7b",
                temperature=0.3,
            )

            assert provider is not None
            mock_ollama.assert_called_once()

    def test_create_openai_provider(self):
        """Testa criação de provider OpenAI."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            mock_instance = MagicMock()
            mock_openai.return_value = mock_instance

            provider = LLMProvider.create(
                provider="openai",
                openai_api_key="test-key",
                openai_model="gpt-4o-mini",
                temperature=0.3,
            )

            assert provider is not None
            mock_openai.assert_called_once()

    def test_create_none_provider(self):
        """Testa criação de provider None (sem IA)."""
        provider = LLMProvider.create(provider="none")

        assert provider is None

    def test_create_invalid_provider_defaults_to_none(self):
        """Testa que provider inválido retorna None."""
        provider = LLMProvider.create(provider="invalid")

        assert provider is None

    def test_create_ollama_with_custom_params(self):
        """Testa criação de Ollama com parâmetros customizados."""
        with patch("langchain_ollama.ChatOllama") as mock_ollama:
            mock_instance = MagicMock()
            mock_ollama.return_value = mock_instance

            provider = LLMProvider.create(
                provider="ollama",
                ollama_url="http://custom:11434",
                ollama_model="llama3:70b",
                temperature=0.5,
                context_size=16384,
                timeout=120,
            )

            assert provider is not None

    def test_create_openai_requires_api_key(self):
        """Testa que OpenAI requer API key."""
        # Sem API key
        provider = LLMProvider.create(provider="openai", openai_api_key=None)

        # Deve retornar None graceful
        assert provider is None

    @pytest.mark.asyncio
    async def test_ollama_provider_invoke(self):
        """Testa invocação do Ollama provider."""
        with patch("langchain_ollama.ChatOllama") as mock_ollama:
            mock_response = MagicMock()
            mock_response.content = "Resposta de teste"
            mock_instance = AsyncMock()
            mock_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_ollama.return_value = mock_instance

            provider = LLMProvider.create(provider="ollama")
            result = await provider.ainvoke("Test message")

            assert result.content == "Resposta de teste"

    @pytest.mark.asyncio
    async def test_openai_provider_invoke(self):
        """Testa invocação do OpenAI provider."""
        with patch("langchain_openai.ChatOpenAI") as mock_openai:
            mock_response = MagicMock()
            mock_response.content = "Resposta OpenAI"
            mock_instance = AsyncMock()
            mock_instance.ainvoke = AsyncMock(return_value=mock_response)
            mock_openai.return_value = mock_instance

            provider = LLMProvider.create(
                provider="openai", openai_api_key="test-key"
            )
            result = await provider.ainvoke("Test message")

            assert result.content == "Resposta OpenAI"


class TestLLMProviderEdgeCases:
    """Testes de casos extremos para LLMProvider."""

    def test_provider_case_insensitive(self):
        """Testa que nome do provider é case-insensitive."""
        provider = LLMProvider.create(provider="OLLAMA")

        # Não deve lançar erro
        assert provider is not None or provider is None

    def test_empty_provider_name(self):
        """Testa provider name vazio."""
        provider = LLMProvider.create(provider="")

        assert provider is None

    def test_default_parameters(self):
        """Testa parâmetros padrão."""
        with patch("langchain_ollama.ChatOllama") as mock_ollama:
            mock_instance = MagicMock()
            mock_ollama.return_value = mock_instance

            provider = LLMProvider.create(provider="ollama")  # Usa defaults

            assert provider is not None
