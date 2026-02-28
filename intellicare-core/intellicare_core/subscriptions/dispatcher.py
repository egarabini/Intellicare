"""SubscriptionDispatcher — async dispatch to the correct channel."""

from __future__ import annotations

import time

from .channels.bot_channel import send_bot_notification
from .channels.rest_hook import send_rest_hook
from .channels.websocket_channel import publish_websocket
from .models import AuditRecord, ChannelResult, SubscriptionRecord


async def dispatch(
    subscription: SubscriptionRecord,
    resource: dict,
    tenant_id: str,
) -> tuple[ChannelResult, AuditRecord]:
    """Dispatch a notification to the appropriate channel.

    Returns ``(ChannelResult, AuditRecord)`` — the audit record reflects
    the *dispatch* outcome (``dispatched`` or ``failed``), not the match.
    """
    start = time.monotonic()
    result: ChannelResult

    try:
        if subscription.channel_type == "rest-hook":
            result = await send_rest_hook(subscription, resource)
        elif subscription.channel_type == "websocket":
            result = await publish_websocket(subscription, resource, tenant_id)
        elif subscription.channel_type == "bot":
            result = await send_bot_notification(subscription, resource)
        else:
            raise ValueError(f"Unknown channel type: {subscription.channel_type!r}")
    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        result = ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error=str(exc),
            duration_ms=elapsed,
        )

    elapsed = (time.monotonic() - start) * 1000
    result.duration_ms = elapsed

    event = "dispatched" if result.success else "failed"
    audit = AuditRecord(
        subscription_id=subscription.id,
        tenant_id=tenant_id,
        event_type=event,
        channel_type=subscription.channel_type,
        status_code=result.status_code,
        error=result.error,
        details={"duration_ms": round(elapsed, 2)},
    )
    return result, audit
