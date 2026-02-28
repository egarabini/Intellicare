"""WebSocket channel: publish notification to Redis Pub/Sub."""

from __future__ import annotations

import json

from ..models import ChannelResult, SubscriptionRecord

_CHANNEL_PREFIX = "fhir:subscriptions"


async def publish_websocket(
    subscription: SubscriptionRecord,
    resource: dict,
    tenant_id: str,
) -> ChannelResult:
    """Publish FHIR resource to a Redis Pub/Sub channel.

    Subscribers (intellicare-comunicacao ws_handler) listen on:
        fhir:subscriptions:{tenant_id}:{subscription_id}
    """
    try:
        import redis.asyncio as aioredis  # type: ignore[import]
    except ImportError:
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error="redis package not installed",
        )

    redis_url = (subscription.channel_header or {}).get(
        "X-Redis-URL", "redis://localhost:6379/0"
    )
    channel = f"{_CHANNEL_PREFIX}:{tenant_id}:{subscription.id}"
    payload = json.dumps(
        {
            "subscriptionId": subscription.id,
            "tenantId": tenant_id,
            "resourceType": resource.get("resourceType"),
            "resourceId": resource.get("id"),
            "resource": resource,
        },
        ensure_ascii=False,
    )

    try:
        client = aioredis.from_url(redis_url, decode_responses=True)
        async with client:
            await client.publish(channel, payload)
        return ChannelResult(subscription_id=subscription.id, success=True)
    except Exception as exc:
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error=str(exc),
        )
