"""REST-hook channel: HTTP POST with HMAC-SHA256 signature."""

from __future__ import annotations

import hashlib
import hmac
import json

import httpx

from ..models import ChannelResult, SubscriptionRecord


async def send_rest_hook(
    subscription: SubscriptionRecord,
    resource: dict,
) -> ChannelResult:
    """POST the FHIR resource to the subscription endpoint with HMAC signature."""
    url = subscription.channel_endpoint
    if not url:
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error="Missing channel_endpoint",
        )

    body = json.dumps(resource, ensure_ascii=False).encode()
    headers: dict[str, str] = {
        "Content-Type": "application/fhir+json",
        "X-IntelliCare-Subscription": subscription.id,
        "X-IntelliCare-Interaction": "notification",
    }
    if subscription.channel_header:
        headers.update(subscription.channel_header)

    secret = (subscription.channel_header or {}).get("X-Secret", "")
    if secret:
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        headers["X-Signature-SHA256"] = f"sha256={sig}"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, content=body, headers=headers)
            return ChannelResult(
                subscription_id=subscription.id,
                success=resp.is_success,
                status_code=resp.status_code,
                error=None if resp.is_success else f"HTTP {resp.status_code}",
            )
    except Exception as exc:
        return ChannelResult(
            subscription_id=subscription.id,
            success=False,
            error=str(exc),
        )
