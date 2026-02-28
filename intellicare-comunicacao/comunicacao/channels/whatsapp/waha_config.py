"""Configuração WAHA (WhatsApp HTTP API)."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class WAHAConfig:
    """Configuração de conexão para WAHA."""

    base_url: str
    session: str = "default"
    api_key: str | None = None
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "WAHAConfig":
        """Carrega configuração WAHA do ambiente."""
        return cls(
            base_url=os.getenv("WAHA_BASE_URL", "").strip(),
            session=os.getenv("WAHA_SESSION", "default").strip() or "default",
            api_key=(os.getenv("WAHA_API_KEY", "").strip() or None),
            timeout=int(os.getenv("WAHA_TIMEOUT_SECONDS", "30")),
        )

    def is_configured(self) -> bool:
        """Indica se WAHA está configurado para uso."""
        return bool(self.base_url)
