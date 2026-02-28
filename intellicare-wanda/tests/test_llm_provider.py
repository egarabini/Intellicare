"""Tests for LLM provider layer (EF-W003) — OllamaProvider + exceptions."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from wanda.llm.exceptions import LLMParseError, LLMTimeoutError, LLMUnavailableError
from wanda.llm.ollama_provider import OllamaProvider
from wanda.llm.provider import LLMResponse


class TestLLMExceptions:
    def test_unavailable_error(self):
        e = LLMUnavailableError(url="http://localhost:11434", reason="Connection refused")
        assert "localhost:11434" in str(e)
        assert "Connection refused" in str(e)
        assert e.url == "http://localhost:11434"

    def test_timeout_error(self):
        e = LLMTimeoutError(timeout_seconds=5.0, model="llama3.1:8b")
        assert "5.0" in str(e)
        assert "llama3.1:8b" in str(e)
        assert e.timeout_seconds == 5.0

    def test_parse_error(self):
        e = LLMParseError(raw_response="not json", reason="Invalid JSON")
        assert "Invalid JSON" in str(e)
        assert e.raw_response == "not json"

    def test_parse_error_truncates_long_response(self):
        long_response = "x" * 300
        e = LLMParseError(raw_response=long_response, reason="too long")
        assert len(e.raw_response) == 200  # Truncated to 200


class TestOllamaProviderInit:
    def test_default_values(self):
        provider = OllamaProvider()
        assert provider.model_name == "llama3.1:8b"

    def test_custom_values(self):
        provider = OllamaProvider(
            url="http://myserver:11434",
            model="mistral:7b",
            timeout=10.0,
        )
        assert provider.model_name == "mistral:7b"

    def test_url_trailing_slash_stripped(self):
        provider = OllamaProvider(url="http://localhost:11434/")
        assert not provider._url.endswith("/")


class TestOllamaProviderChat:
    @pytest.mark.asyncio
    async def test_successful_chat(self):
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": '{"result": "ok"}'},
            "model": "llama3.1:8b",
            "eval_count": 50,
            "prompt_eval_count": 30,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("wanda.llm.ollama_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            response = await provider.chat(
                system_prompt="You are a router",
                user_message="Route this query",
            )

        assert response.success is True
        assert response.content == '{"result": "ok"}'
        assert response.tokens_used == 80

    @pytest.mark.asyncio
    async def test_timeout_raises_llm_timeout_error(self):
        import httpx
        provider = OllamaProvider()

        with patch("wanda.llm.ollama_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(LLMTimeoutError):
                await provider.chat(system_prompt="system", user_message="user")

    @pytest.mark.asyncio
    async def test_connect_error_raises_llm_unavailable(self):
        import httpx
        provider = OllamaProvider()

        with patch("wanda.llm.ollama_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(LLMUnavailableError):
                await provider.chat(system_prompt="system", user_message="user")


class TestOllamaHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("wanda.llm.ollama_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        import httpx
        provider = OllamaProvider()

        with patch("wanda.llm.ollama_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("refused")
            mock_client_cls.return_value.__aenter__.return_value = mock_client
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.health_check()

        assert result is False


class TestLLMResponse:
    def test_failed_property(self):
        r = LLMResponse(content="ok", model="llama3.1:8b", success=True)
        assert r.failed is False

    def test_failed_property_when_error(self):
        r = LLMResponse(content="", model="llama3.1:8b", success=False, error="timeout")
        assert r.failed is True
