"""LLM-specific exceptions for WANDA (EF-W003)."""


class LLMUnavailableError(Exception):
    """Raised when the LLM provider (Ollama) is not reachable."""

    def __init__(self, url: str, reason: str = ""):
        self.url = url
        self.reason = reason
        super().__init__(f"LLM unavailable at {url}: {reason}")


class LLMTimeoutError(Exception):
    """Raised when the LLM call exceeds the configured timeout."""

    def __init__(self, timeout_seconds: float, model: str = ""):
        self.timeout_seconds = timeout_seconds
        self.model = model
        super().__init__(
            f"LLM call timed out after {timeout_seconds}s (model={model})"
        )


class LLMParseError(Exception):
    """Raised when the LLM response cannot be parsed as expected JSON."""

    def __init__(self, raw_response: str, reason: str = ""):
        self.raw_response = raw_response[:200]  # Truncate for safety
        self.reason = reason
        super().__init__(f"LLM response parse error: {reason}")
