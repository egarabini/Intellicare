"""Gerenciador de conexao Redis Pub/Sub para notificacoes."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis

from intellicare_core.config.settings import get_settings

logger = logging.getLogger(__name__)

_redis_pool: aioredis.Redis | None = None


def _get_redis_url() -> str:
    s = get_settings()
    redis_pass = os.getenv("REDIS_PASSWORD_URLENC") or s.redis_password
    return f"redis://:{redis_pass}@{s.redis_host}:{s.redis_port}/0"


async def get_redis() -> aioredis.Redis:
    """Retorna conexao Redis reutilizavel."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            _get_redis_url(),
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis() -> None:
    """Fecha pool Redis (chamado no shutdown)."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


def _channel_for_user(tenant_id: str, user_id: str) -> str:
    """Canal Redis para um usuario especifico."""
    return f"notif:{tenant_id}:{user_id}"


def _channel_for_tenant(tenant_id: str) -> str:
    """Canal Redis broadcast para todo o tenant."""
    return f"notif:{tenant_id}:broadcast"


async def publish_notification(
    tenant_id: str,
    user_id: str,
    payload: dict[str, Any],
) -> int:
    """Publica notificacao no canal do usuario via Redis."""
    r = await get_redis()
    channel = _channel_for_user(tenant_id, user_id)
    message = json.dumps(payload, default=str)
    return await r.publish(channel, message)


async def publish_broadcast(
    tenant_id: str,
    payload: dict[str, Any],
) -> int:
    """Publica notificacao broadcast para todo o tenant."""
    r = await get_redis()
    channel = _channel_for_tenant(tenant_id)
    message = json.dumps(payload, default=str)
    return await r.publish(channel, message)


async def subscribe_user(
    tenant_id: str,
    user_id: str,
) -> AsyncGenerator[dict[str, Any], None]:
    """Assina canais do usuario e broadcast, yield de mensagens."""
    r = await get_redis()
    pubsub = r.pubsub()

    user_channel = _channel_for_user(tenant_id, user_id)
    broadcast_channel = _channel_for_tenant(tenant_id)

    await pubsub.subscribe(user_channel, broadcast_channel)
    logger.info("Subscribed: %s, %s", user_channel, broadcast_channel)

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if message and message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    yield data
                except (json.JSONDecodeError, TypeError):
                    logger.warning("Mensagem Redis invalida: %s", message["data"])
            else:
                # yield None periodicamente para permitir heartbeat
                await asyncio.sleep(0.1)
    finally:
        await pubsub.unsubscribe(user_channel, broadcast_channel)
        await pubsub.aclose()
