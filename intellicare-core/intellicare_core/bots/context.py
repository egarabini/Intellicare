"""BotExecutionContext — the execution environment passed to bot code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .client import IntelliCareClient
from .models import EventMetadata


@dataclass
class BotExecutionContext:
    """All context available to bot code at runtime.

    Bot code receives these as globals:
        ``input``   — FHIR resource that triggered the bot
        ``client``  — IntelliCareClient authenticated for the tenant
        ``secrets`` — dict of decrypted secret values
        ``event``   — EventMetadata (subscription_id, interaction, etc.)
    """

    input_resource: dict[str, Any]
    fhir_client: IntelliCareClient
    secrets: dict[str, str] = field(default_factory=dict)
    event_metadata: EventMetadata = field(default_factory=EventMetadata)

    def as_globals(self) -> dict[str, Any]:
        """Return the globals dict injected into the bot sandbox."""
        return {
            "input": self.input_resource,
            "client": self.fhir_client,
            "secrets": self.secrets,
            "event": self.event_metadata,
        }
