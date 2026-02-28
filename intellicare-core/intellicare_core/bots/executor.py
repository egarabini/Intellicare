"""BotExecutor — orchestrates a single bot execution end-to-end."""

from __future__ import annotations

import time
from typing import Any, Optional

from .client import IntelliCareClient
from .context import BotExecutionContext
from .models import BotExecutionResult, BotRecord, EventMetadata
from .sandbox import BotSandbox
from .secrets_manager import SecretsManager


class BotExecutor:
    """Orchestrate one bot execution: load context → run sandbox → return result."""

    def __init__(self, grahame_url: Optional[str] = None) -> None:
        self._sandbox = BotSandbox()
        self._secrets_mgr = SecretsManager()
        self._grahame_url = grahame_url

    async def execute(
        self,
        bot: BotRecord,
        input_resource: dict[str, Any],
        *,
        encrypted_secrets: Optional[dict[str, str]] = None,
        event_metadata: Optional[EventMetadata] = None,
    ) -> BotExecutionResult:
        """Execute *bot* with *input_resource* and return a structured result.

        Args:
            bot:               Bot definition (code, timeout, etc.)
            input_resource:    The FHIR resource that triggered the bot.
            encrypted_secrets: {name: ciphertext} from the DB — decrypted here.
            event_metadata:    Subscription/interaction context.
        """
        start = time.monotonic()
        meta = event_metadata or EventMetadata(tenant_id=bot.tenant_id)

        # Decrypt secrets
        secrets: dict[str, str] = {}
        if encrypted_secrets:
            try:
                secrets = self._secrets_mgr.decrypt_all(encrypted_secrets)
            except Exception:
                pass  # Silently skip if decryption fails

        # Build context
        fhir_client = IntelliCareClient(
            tenant_id=bot.tenant_id,
            base_url=self._grahame_url,
        )
        ctx = BotExecutionContext(
            input_resource=input_resource,
            fhir_client=fhir_client,
            secrets=secrets,
            event_metadata=meta,
        )

        # Run in sandbox
        sandbox_result = self._sandbox.execute(
            bot.code, ctx.as_globals(), timeout=bot.timeout_seconds
        )

        elapsed = (time.monotonic() - start) * 1000

        return BotExecutionResult(
            bot_id=bot.id,
            tenant_id=bot.tenant_id,
            subscription_id=meta.subscription_id,
            interaction=meta.interaction,
            input_resource_type=input_resource.get("resourceType"),
            input_resource_id=input_resource.get("id"),
            success=sandbox_result.success,
            log_output=sandbox_result.log_output,
            duration_ms=elapsed,
            error_message=sandbox_result.error,
        )
