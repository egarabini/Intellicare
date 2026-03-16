"""Endpoints REST + SSE + WebSocket para notificacoes."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from intellicare_core.auth.jwt import get_current_tenant, verify_token
from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error

from .redis_pubsub import subscribe_user
from .schemas import (
    NotificationBroadcast,
    NotificationCreate,
    NotificationListResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from .service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()

_service = NotificationService()

Authenticated = Annotated[TenantContext, Depends(get_current_tenant)]


# ── Health ───────────────────────────────────────────────────

@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "module": "notifications", "version": "1.0.0"}


# ── CRUD ─────────────────────────────────────────────────────

@router.post("/send", response_model=NotificationResponse, status_code=201)
async def send_notification(
    data: NotificationCreate,
    ctx: Authenticated,
) -> NotificationResponse:
    """Cria e envia notificacao para um usuario."""
    notif = await _service.send(ctx, data)
    return NotificationResponse(**notif)


@router.post("/broadcast", status_code=201)
async def broadcast_notification(
    data: NotificationBroadcast,
    ctx: Authenticated,
) -> dict:
    """Envia notificacao broadcast para todo o tenant."""
    result = await _service.broadcast(ctx, data)
    return {"status": "sent", "notification": result}


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    ctx: Authenticated,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
) -> NotificationListResponse:
    """Lista notificacoes do usuario autenticado."""
    items, total = await _service.list_for_user(ctx, page, size, unread_only)
    return NotificationListResponse(
        items=[NotificationResponse(**i) for i in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(ctx: Authenticated) -> UnreadCountResponse:
    """Retorna contagem de notificacoes nao lidas."""
    count = await _service.unread_count(ctx)
    return UnreadCountResponse(count=count)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    ctx: Authenticated,
) -> NotificationResponse:
    """Retorna detalhe de uma notificacao."""
    notif = await _service.get_by_id(ctx, notification_id)
    if not notif:
        raise api_error(404, "not_found", "Notificacao nao encontrada")
    return NotificationResponse(**notif)


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    ctx: Authenticated,
) -> dict:
    """Marca notificacao como lida."""
    found = await _service.mark_read(ctx, notification_id)
    if not found:
        raise api_error(404, "not_found", "Notificacao nao encontrada ou ja lida")
    return {"status": "ok"}


@router.patch("/read-all")
async def mark_all_read(ctx: Authenticated) -> dict:
    """Marca todas as notificacoes como lidas."""
    count = await _service.mark_all_read(ctx)
    return {"status": "ok", "marked": count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    ctx: Authenticated,
) -> dict:
    """Remove uma notificacao."""
    found = await _service.delete(ctx, notification_id)
    if not found:
        raise api_error(404, "not_found", "Notificacao nao encontrada")
    return {"status": "deleted"}


# ── Preferences ──────────────────────────────────────────────

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(ctx: Authenticated) -> NotificationPreferencesResponse:
    """Retorna preferencias de notificacao do usuario."""
    return await _service.get_preferences(ctx)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    data: NotificationPreferencesUpdate,
    ctx: Authenticated,
) -> NotificationPreferencesResponse:
    """Atualiza preferencias de notificacao."""
    return await _service.update_preferences(ctx, data)


# ── SSE (Server-Sent Events) ────────────────────────────────

@router.get("/stream")
async def notification_stream(ctx: Authenticated):
    """
    Endpoint SSE para notificacoes em tempo real.

    Uso: GET /notifications/stream
    Header: Authorization: Bearer {token}
    Accept: text/event-stream
    """

    async def _event_generator():
        heartbeat_interval = 30  # seconds
        last_heartbeat = asyncio.get_event_loop().time()

        async for notification in subscribe_user(ctx.tenant_id, ctx.user_id):
            now = asyncio.get_event_loop().time()

            # Enviar heartbeat periodicamente
            if now - last_heartbeat >= heartbeat_interval:
                yield {"event": "keepalive", "data": ""}
                last_heartbeat = now

            if notification:
                yield {
                    "event": "notification",
                    "data": json.dumps(notification, default=str),
                }

    return EventSourceResponse(_event_generator())


# ── WebSocket ────────────────────────────────────────────────

@router.websocket("/ws")
async def notification_websocket(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket para notificacoes em tempo real.

    Uso: WS /notifications/ws?token={jwt}
    """
    # Autenticar via query param
    try:
        ctx = await verify_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Token invalido")
        return

    await websocket.accept()
    logger.info("WebSocket conectado: tenant=%s user=%s", ctx.tenant_id, ctx.user_id)

    # Tarefa para receber mensagens do cliente (ping/pong, ack)
    async def _receive_loop():
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif msg.get("type") == "ack" and msg.get("id"):
                        # Cliente confirmou recebimento — marcar como lida
                        await _service.mark_read(ctx, UUID(msg["id"]))
                except (json.JSONDecodeError, ValueError):
                    pass
        except WebSocketDisconnect:
            pass

    # Tarefa para enviar notificacoes do Redis
    async def _send_loop():
        try:
            async for notification in subscribe_user(ctx.tenant_id, ctx.user_id):
                if notification:
                    await websocket.send_json({
                        "type": "notification",
                        "data": notification,
                    })
        except WebSocketDisconnect:
            pass
        except Exception:
            logger.warning("Erro no send_loop WebSocket", exc_info=True)

    # Tarefa de keepalive
    async def _keepalive():
        try:
            while True:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
        except (WebSocketDisconnect, Exception):
            pass

    # Executar loops concorrentemente
    tasks = [
        asyncio.create_task(_receive_loop()),
        asyncio.create_task(_send_loop()),
        asyncio.create_task(_keepalive()),
    ]

    try:
        # Aguarda qualquer tarefa finalizar (geralmente disconnect)
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
    except Exception:
        for task in tasks:
            task.cancel()
    finally:
        logger.info("WebSocket desconectado: tenant=%s user=%s", ctx.tenant_id, ctx.user_id)
