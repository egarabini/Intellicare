"""WebSocket handler for FHIR Subscription notifications.

Clients connect to ``/ws/subscriptions/{subscription_id}`` and receive
real-time FHIR resource notifications pushed via Redis Pub/Sub.

Architecture:
    Grahame (dispatch) -> Redis Pub/Sub -> ws_handler -> WebSocket client
    Channel key: fhir:subscriptions:{tenant_id}:{subscription_id}

W11-A: Supports token lifecycle for long-lived websocket sessions:
  - client message ``token-refresh``
  - server message ``token-refresh-ack``
  - server message ``refresh-required``
  - close ``4001`` when token expires without refresh
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

logger = logging.getLogger(__name__)

router = APIRouter(tags=["FHIR Subscriptions WebSocket"])

_CHANNEL_PREFIX = "fhir:subscriptions"
_PING_INTERVAL = 30
_REDIS_POLL_TIMEOUT = 1.0
_WS_REFRESH_REQUIRED_THRESHOLD = int(os.getenv("WS_REFRESH_REQUIRED_THRESHOLD", "300"))
_WS_TOKEN_REFRESH_RATE_LIMIT = int(os.getenv("WS_TOKEN_REFRESH_RATE_LIMIT", "60"))
_WS_TOKEN_ISSUER = os.getenv("WS_TOKEN_ISSUER", "").strip()


@router.websocket("/ws/subscriptions/{subscription_id}")
async def ws_subscription(
    websocket: WebSocket,
    subscription_id: str,
    tenant_id: str = Query(default="default", alias="tenant"),
    redis_url: str = Query(default="redis://localhost:6379/0", alias="redis"),
    token: str | None = Query(default=None, alias="token"),
):
    """WebSocket endpoint for real-time FHIR Subscription notifications."""
    await websocket.accept()

    token_context: dict[str, object] = {
        "token": token,
        "token_exp": None,
        "last_refresh_ts": 0.0,
        "refresh_required_sent": False,
    }
    if token:
        parsed = _parse_and_validate_token(token)
        if parsed.get("ok"):
            token_context["token_exp"] = parsed["exp"]

    channel = f"{_CHANNEL_PREFIX}:{tenant_id}:{subscription_id}"
    logger.info(
        "ws.subscriptions.connect subscription_id=%s tenant=%s channel=%s",
        subscription_id,
        tenant_id,
        channel,
    )

    try:
        import redis.asyncio as aioredis  # type: ignore[import]
    except ImportError:
        await _send_json(websocket, {"type": "error", "message": "Redis not available"})
        await websocket.close(code=1011)
        return

    try:
        redis_client = aioredis.from_url(redis_url, decode_responses=True)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(channel)
    except Exception as exc:
        logger.error("ws.subscriptions.redis_error error=%s", exc)
        await _send_json(websocket, {"type": "error", "message": f"Redis connection failed: {exc}"})
        await websocket.close(code=1011)
        return

    await _send_json(
        websocket,
        {
            "type": "connected",
            "subscriptionId": subscription_id,
            "tenantId": tenant_id,
            "channel": channel,
        },
    )

    ping_task = asyncio.create_task(_ping_loop(websocket))
    recv_task = asyncio.create_task(_receive_client_messages(websocket, token_context))

    try:
        async for message in _message_stream(pubsub, websocket):
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            should_close = await _enforce_token_lifecycle(websocket, token_context)
            if should_close:
                break
            if message is None:
                continue
            await _send_json(websocket, message)
    except WebSocketDisconnect:
        logger.info("ws.subscriptions.disconnect subscription_id=%s tenant=%s", subscription_id, tenant_id)
    except Exception as exc:
        logger.error("ws.subscriptions.error error=%s", exc)
    finally:
        ping_task.cancel()
        recv_task.cancel()
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            await redis_client.aclose()
        except Exception:
            pass
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close()


async def _message_stream(pubsub, websocket: WebSocket):
    """Yield parsed notification dicts from Redis Pub/Sub."""
    while websocket.client_state == WebSocketState.CONNECTED:
        try:
            msg = await asyncio.wait_for(
                pubsub.get_message(ignore_subscribe_messages=True),
                timeout=_REDIS_POLL_TIMEOUT,
            )
        except asyncio.TimeoutError:
            yield None
            continue
        except Exception as exc:
            logger.warning("ws.subscriptions.pubsub_error error=%s", exc)
            break

        if msg is None:
            yield None
            continue

        if msg.get("type") == "message":
            try:
                data = json.loads(msg["data"])
                yield data
            except (json.JSONDecodeError, KeyError) as exc:
                logger.warning("ws.subscriptions.parse_error error=%s raw=%s", exc, msg)


def _decode_jwt_payload(token: str) -> dict:
    raw = token.strip()
    if raw.lower().startswith("bearer "):
        raw = raw[7:].strip()
    parts = raw.split(".")
    if len(parts) < 2:
        raise ValueError("Malformed token")
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(payload).decode("utf-8")
    data = json.loads(decoded)
    if not isinstance(data, dict):
        raise ValueError("Invalid token payload")
    return data


def _parse_and_validate_token(token: str) -> dict[str, object]:
    try:
        payload = _decode_jwt_payload(token)
    except Exception as exc:
        return {"ok": False, "error": f"Invalid token format: {exc}"}

    exp = payload.get("exp")
    if exp is None:
        return {"ok": False, "error": "Token missing exp claim"}
    try:
        exp_ts = float(exp)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Invalid exp claim"}
    if exp_ts <= time.time():
        return {"ok": False, "error": "Token expired"}

    if _WS_TOKEN_ISSUER:
        if payload.get("iss") != _WS_TOKEN_ISSUER:
            return {"ok": False, "error": "Invalid token issuer"}

    return {"ok": True, "exp": exp_ts}


async def _receive_client_messages(websocket: WebSocket, token_context: dict[str, object]) -> None:
    """Receive client messages (W11-A token-refresh)."""
    while websocket.client_state == WebSocketState.CONNECTED:
        try:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
        except asyncio.TimeoutError:
            continue
        except WebSocketDisconnect:
            break
        except Exception:
            break

        if not isinstance(data, dict) or data.get("type") != "token-refresh":
            continue

        now = time.time()
        last_refresh = float(token_context.get("last_refresh_ts", 0.0) or 0.0)
        if now - last_refresh < _WS_TOKEN_REFRESH_RATE_LIMIT:
            await _send_json(
                websocket,
                {
                    "type": "token-refresh-ack",
                    "success": False,
                    "error": "Token refresh rate limit exceeded",
                },
            )
            continue

        token = str(data.get("token") or "")
        parsed = _parse_and_validate_token(token)
        if not parsed.get("ok"):
            await _send_json(
                websocket,
                {
                    "type": "token-refresh-ack",
                    "success": False,
                    "error": parsed.get("error", "Token invalid"),
                },
            )
            continue

        token_context["token"] = token
        token_context["token_exp"] = parsed["exp"]
        token_context["last_refresh_ts"] = now
        token_context["refresh_required_sent"] = False
        await _send_json(websocket, {"type": "token-refresh-ack", "success": True})


async def _enforce_token_lifecycle(websocket: WebSocket, token_context: dict[str, object]) -> bool:
    token_exp = token_context.get("token_exp")
    if token_exp is None:
        return False

    try:
        token_exp_ts = float(token_exp)
    except (TypeError, ValueError):
        return False

    now = time.time()
    expires_in = int(token_exp_ts - now)
    if expires_in <= 0:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.close(code=4001, reason="Token expired")
        return True

    if expires_in <= _WS_REFRESH_REQUIRED_THRESHOLD and not bool(token_context.get("refresh_required_sent", False)):
        await _send_json(websocket, {"type": "refresh-required", "expires_in": expires_in})
        token_context["refresh_required_sent"] = True

    return False


async def _ping_loop(websocket: WebSocket) -> None:
    """Send periodic ping frames to keep the WebSocket alive."""
    while True:
        await asyncio.sleep(_PING_INTERVAL)
        if websocket.client_state != WebSocketState.CONNECTED:
            break
        try:
            await _send_json(websocket, {"type": "ping"})
        except Exception:
            break


async def _send_json(websocket: WebSocket, data: dict) -> None:
    try:
        await websocket.send_json(data)
    except Exception as exc:
        logger.debug("ws.subscriptions.send_failed error=%s", exc)
