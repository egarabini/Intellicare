from __future__ import annotations

import inspect
import logging
from typing import Any, Awaitable, Callable

import httpx

from intellicare_core.config.settings import get_settings

logger = logging.getLogger("intellicare.marie.client")


def is_marie_enabled() -> bool:
    return get_settings().marie_enabled


async def _run_fallback(fallback_fn: Callable[[], Any] | Callable[[], Awaitable[Any]] | None) -> Any:
    if fallback_fn is None:
        return None
    result = fallback_fn()
    if inspect.isawaitable(result):
        return await result
    return result


async def call_marie(
    workflow_slug: str,
    inputs: dict[str, Any],
    fallback_fn: Callable[[], Any] | Callable[[], Awaitable[Any]] | None = None,
) -> Any:
    settings = get_settings()
    if not settings.marie_enabled or not settings.marie_api_key:
        return await _run_fallback(fallback_fn)

    url = f"{settings.marie_api_url.rstrip('/')}/v1/chat-messages"
    payload = {
        "inputs": {**inputs, "workflow_slug": workflow_slug},
        "query": inputs.get("query", workflow_slug),
        "response_mode": "blocking",
        "conversation_id": "",
        "user": "intellicare-api",
    }
    headers = {
        "Authorization": f"Bearer {settings.marie_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.marie_timeout_seconds) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
        logger.warning("Marie unavailable for workflow=%s: %s. Using fallback.", workflow_slug, exc)
        return await _run_fallback(fallback_fn)
