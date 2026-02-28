"""Bot channel: execute an IntelliCare Bot triggered by a FHIR Subscription.

channel_endpoint format: ``Bot/{bot_id}``

The channel fetches the Bot record from intellicare-grahame, builds a
BotExecutionContext and runs the bot code inside the sandbox engine.
Failures are handled by the caller's retry/audit logic.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from ..models import ChannelResult, SubscriptionRecord

logger = logging.getLogger(__name__)

_BOT_ID_RE = re.compile(r"^Bot/(.+)$")


def _extract_bot_id(endpoint: Optional[str]) -> Optional[str]:
    if not endpoint:
        return None
    m = _BOT_ID_RE.match(endpoint.strip())
    return m.group(1) if m else None


async def send_bot_notification(
    subscription: SubscriptionRecord,
    resource: dict,
) -> ChannelResult:
    """Execute the bot referenced by ``subscription.channel_endpoint``.

    Requires:
        - ``channel_endpoint`` = ``"Bot/{bot_id}"``
        - ``X-Grahame-URL`` in ``channel_header`` (optional — falls back to env)

    The bot execution is delegated to :class:`intellicare_core.bots.BotExecutor`.
    """
    bot_id = _extract_bot_id(subscription.channel_endpoint)
    if not bot_id:
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error=(
                f"Invalid bot channel_endpoint: {subscription.channel_endpoint!r}. "
                "Expected format: 'Bot/<bot_id>'"
            ),
        )

    grahame_url = (subscription.channel_header or {}).get("X-Grahame-URL")

    try:
        import os  # noqa: PLC0415

        import httpx  # noqa: PLC0415

        from intellicare_core.bots import BotExecutor, BotRecord, EventMetadata  # noqa: PLC0415

        executor = BotExecutor(grahame_url=grahame_url)
        base = (
            grahame_url or os.getenv("GRAHAME_URL", "http://intellicare-grahame:8000")
        ).rstrip("/")
        headers = {"X-Tenant-ID": subscription.tenant_id}

        async with httpx.AsyncClient(timeout=30.0) as client:
            bot_resp = await client.get(f"{base}/api/v1/fhir/Bot/{bot_id}", headers=headers)

        if not bot_resp.is_success:
            return ChannelResult(
                subscription_id=subscription.id,
                success=False,
                error=f"Bot/{bot_id} not found (HTTP {bot_resp.status_code})",
            )

        bot_data = bot_resp.json()
        bot = BotRecord(
            id=bot_data["id"],
            tenant_id=subscription.tenant_id,
            name=bot_data.get("name", ""),
            code=bot_data.get("code", ""),
            runtime=bot_data.get("runtime", "sandbox"),
            status=bot_data.get("status", "active"),
            timeout_seconds=bot_data.get("timeoutSeconds", 30),
        )

        if bot.status != "active":
            return ChannelResult(
                subscription_id=subscription.id,
                success=False,
                error=f"Bot/{bot_id} is not active (status={bot.status})",
            )

        meta = EventMetadata(
            subscription_id=subscription.id,
            interaction="create",
            resource_type=resource.get("resourceType"),
            resource_id=resource.get("id"),
            tenant_id=subscription.tenant_id,
        )

        result = await executor.execute(bot, resource, event_metadata=meta)
        logger.info(
            "bot.executed bot_id=%s success=%s duration_ms=%.1f",
            bot_id,
            result.success,
            result.duration_ms,
        )
        return ChannelResult(
            subscription_id=subscription.id,
            success=result.success,
            error=result.error_message,
        )

    except ImportError as exc:
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error=f"intellicare_core.bots not available: {exc}",
        )
    except Exception as exc:
        logger.error("bot.channel_error bot_id=%s error=%s", bot_id, exc)
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error=str(exc),
        )
