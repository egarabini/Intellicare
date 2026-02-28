"""Rotas operacionais para diagnostico de canais."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from comunicacao.dispatchers import ChannelMessage, DispatcherManager, RenderedContent, ResolvedRecipient


class ChannelTestRequest(BaseModel):
    recipient_id: str = Field(default="test-recipient")
    room_id: str | None = Field(default=None)
    message: str = Field(default="Mensagem de teste IntelliCare", min_length=1, max_length=1000)


def create_channel_router(get_state: Callable[[], dict[str, Any]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/channels", tags=["channels"])

    @router.get("")
    async def list_channels() -> dict[str, Any]:
        state = get_state()
        manager: DispatcherManager | None = state.get("dispatcher_manager")
        if manager is None:
            return {"ok": True, "count": 0, "items": []}

        channels = manager.list_channels()
        items: list[dict[str, Any]] = []
        for channel in channels:
            health = await manager.get_health(channel=channel)
            capabilities = await manager.get_capabilities(channel=channel)
            items.append(
                {
                    "channel": channel,
                    "available": bool(health.available) if health is not None else False,
                    "status": health.status if health is not None else "unknown",
                    "supports_read_receipt": bool(capabilities.supports_read_receipt) if capabilities else False,
                    "supports_rich_content": bool(capabilities.supports_rich_content) if capabilities else False,
                }
            )
        return {"ok": True, "count": len(items), "items": items}

    @router.get("/{channel}/health")
    async def channel_health(channel: str) -> dict[str, Any]:
        state = get_state()
        manager: DispatcherManager | None = state.get("dispatcher_manager")
        if manager is None:
            raise HTTPException(status_code=404, detail=f"canal nao registrado: {channel}")
        health = await manager.get_health(channel=channel)
        if health is None:
            raise HTTPException(status_code=404, detail=f"canal nao registrado: {channel}")
        return {
            "ok": True,
            "channel": health.channel,
            "available": health.available,
            "status": health.status,
            "details": health.details,
            "checked_at": health.checked_at.isoformat(),
        }

    @router.post("/{channel}/test")
    async def channel_test(channel: str, payload: ChannelTestRequest) -> dict[str, Any]:
        state = get_state()
        manager: DispatcherManager | None = state.get("dispatcher_manager")
        if manager is None or manager.get_dispatcher(channel=channel) is None:
            raise HTTPException(status_code=404, detail=f"canal nao registrado: {channel}")

        recipient = ResolvedRecipient(
            recipient_id=payload.recipient_id,
            recipient_type="test",
            channels={channel: payload.room_id} if payload.room_id else {},
        )
        message = ChannelMessage(
            intent_id="test-intent",
            correlation_id="test-correlation",
            channel=channel,
            recipient=recipient,
            content=RenderedContent(format="plain", body=payload.message),
            metadata={"room_id": payload.room_id} if payload.room_id else {},
        )
        result = await manager.dispatch(channel=channel, message=message)
        return {
            "ok": result.success,
            "channel": channel,
            "success": result.success,
            "channel_message_id": result.channel_message_id,
            "channel_room_id": result.channel_room_id,
            "error_code": result.error_code,
            "error_message": result.error_message,
            "timestamp": result.timestamp.isoformat(),
        }

    return router
