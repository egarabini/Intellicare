"""Ollama LLM provider for WANDA — uses httpx (no ollama package needed)."""

import json
import logging
import time
from typing import Optional

import httpx

from wanda.llm.exceptions import LLMParseError, LLMTimeoutError, LLMUnavailableError
from wanda.llm.provider import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """LLM provider that calls Ollama via its REST API.

    Uses httpx async client — no external ``ollama`` package required.
    Supports JSON mode for structured outputs (routing + aggregation).
    """

    def __init__(
        self,
        url: str = "http://localhost:11434",
        model: str = "llama3.1:8b",
        timeout: float = 10.0,
        temperature: float = 0.1,
    ):
        self._url = url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._temperature = temperature

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        json_mode: bool = True,
    ) -> LLMResponse:
        """Send a chat completion request to Ollama.

        Ollama REST endpoint: POST /api/chat
        Uses ``stream=false`` for a single synchronous response.
        """
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {
                "temperature": self._temperature,
                "num_predict": 1024,
            },
        }
        if json_mode:
            payload["format"] = "json"

        start = time.monotonic()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._url}/api/chat",
                    json=payload,
                    timeout=self._timeout,
                )
                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as e:
            raise LLMTimeoutError(timeout_seconds=self._timeout, model=self._model) from e

        except httpx.ConnectError as e:
            raise LLMUnavailableError(url=self._url, reason=str(e)) from e

        except httpx.HTTPStatusError as e:
            raise LLMUnavailableError(
                url=self._url, reason=f"HTTP {e.response.status_code}"
            ) from e

        latency_ms = int((time.monotonic() - start) * 1000)

        # Ollama response format: {"message": {"content": "..."}, "model": "...", ...}
        try:
            content = data["message"]["content"]
        except (KeyError, TypeError) as e:
            raise LLMParseError(
                raw_response=str(data), reason=f"Missing message.content: {e}"
            ) from e

        tokens_used = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

        logger.debug(
            "Ollama %s response: %d tokens, %dms",
            self._model,
            tokens_used,
            latency_ms,
        )

        return LLMResponse(
            content=content,
            model=self._model,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            success=True,
            metadata={"ollama_url": self._url},
        )

    async def health_check(self) -> bool:
        """Check if Ollama is running by hitting GET /api/tags."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._url}/api/tags", timeout=3.0
                )
                return resp.status_code == 200
        except Exception:
            return False
