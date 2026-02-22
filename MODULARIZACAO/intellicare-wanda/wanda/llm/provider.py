"""Abstract LLM provider interface for WANDA (EF-W003 + EF-W004)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""

    content: str                          # Raw text content from the LLM
    model: str                            # Model used
    latency_ms: int = 0                   # Call latency in milliseconds
    tokens_used: int = 0                  # Approximate token count
    success: bool = True
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        return not self.success


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM integrations (Ollama, OpenAI, etc.) implement this interface,
    enabling transparent swapping and consistent fallback behavior.
    """

    @abstractmethod
    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        json_mode: bool = True,
    ) -> LLMResponse:
        """Send a chat message and return the LLM response.

        Args:
            system_prompt: Instructions for the LLM role/behavior.
            user_message: The user's question or content to process.
            json_mode: If True, request JSON-formatted output.

        Returns:
            LLMResponse with the content and metadata.

        Raises:
            LLMUnavailableError: If the provider cannot be reached.
            LLMTimeoutError: If the call exceeds configured timeout.
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the LLM provider is available.

        Returns:
            True if the provider is reachable and ready.
        """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the configured model name."""
