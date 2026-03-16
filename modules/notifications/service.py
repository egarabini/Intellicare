"""Servico de notificacoes — logica de negocio + persistencia."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import TenantAwareSessionFactory

from .redis_pubsub import publish_broadcast, publish_notification
from .schemas import (
    NotificationCreate,
    NotificationBroadcast,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    NotificationResponse,
)

logger = logging.getLogger(__name__)

_factory = TenantAwareSessionFactory()


def _tenant_session(ctx: TenantContext):
    return _factory.session(ctx)


class NotificationService:
    """CRUD de notificacoes + pub/sub Redis."""

    # ── CREATE ───────────────────────────────────────────────

    async def send(
        self,
        ctx: TenantContext,
        data: NotificationCreate,
    ) -> dict[str, Any]:
        """Cria notificacao no banco e publica via Redis."""
        async with _tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text("""
                        INSERT INTO notifications (user_id, type, priority, title, body, data)
                        VALUES (:user_id, :type, :priority, :title, :body, :data::jsonb)
                        RETURNING id, user_id, type, priority, title, body, data,
                                  read, read_at, created_at
                    """),
                    {
                        "user_id": data.user_id,
                        "type": data.type,
                        "priority": data.priority,
                        "title": data.title,
                        "body": data.body,
                        "data": _json_dumps(data.data),
                    },
                )
            ).mappings().first()

        notif = dict(row) if row else {}

        # Publicar via Redis para clientes conectados
        try:
            await publish_notification(
                tenant_id=ctx.tenant_id,
                user_id=data.user_id,
                payload=_serialize_notification(notif),
            )
        except Exception:
            logger.warning("Falha ao publicar notificacao via Redis", exc_info=True)

        return notif

    async def broadcast(
        self,
        ctx: TenantContext,
        data: NotificationBroadcast,
    ) -> dict[str, Any]:
        """Envia notificacao broadcast para todo o tenant."""
        payload = {
            "type": data.type,
            "priority": data.priority,
            "title": data.title,
            "body": data.body,
            "data": data.data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            await publish_broadcast(
                tenant_id=ctx.tenant_id,
                payload=payload,
            )
        except Exception:
            logger.warning("Falha ao publicar broadcast via Redis", exc_info=True)

        return payload

    # ── READ ─────────────────────────────────────────────────

    async def list_for_user(
        self,
        ctx: TenantContext,
        page: int = 1,
        size: int = 20,
        unread_only: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        """Lista notificacoes do usuario autenticado."""
        where = "user_id = :user_id"
        params: dict[str, Any] = {
            "user_id": ctx.user_id,
            "limit": size,
            "offset": (page - 1) * size,
        }

        if unread_only:
            where += " AND read = FALSE"

        async with _tenant_session(ctx) as db:
            total = (
                await db.execute(
                    text(f"SELECT COUNT(*) FROM notifications WHERE {where}"),
                    params,
                )
            ).scalar_one()

            rows = (
                await db.execute(
                    text(f"""
                        SELECT id, user_id, type, priority, title, body, data,
                               read, read_at, created_at
                        FROM notifications
                        WHERE {where}
                        ORDER BY created_at DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    params,
                )
            ).mappings().all()

        return [dict(r) for r in rows], total

    async def get_by_id(
        self,
        ctx: TenantContext,
        notification_id: UUID,
    ) -> dict[str, Any] | None:
        """Retorna uma notificacao por ID (apenas do usuario autenticado)."""
        async with _tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text("""
                        SELECT id, user_id, type, priority, title, body, data,
                               read, read_at, created_at
                        FROM notifications
                        WHERE id = :id AND user_id = :user_id
                    """),
                    {"id": str(notification_id), "user_id": ctx.user_id},
                )
            ).mappings().first()
        return dict(row) if row else None

    async def unread_count(self, ctx: TenantContext) -> int:
        """Retorna contagem de notificacoes nao lidas."""
        async with _tenant_session(ctx) as db:
            return (
                await db.execute(
                    text("""
                        SELECT COUNT(*) FROM notifications
                        WHERE user_id = :user_id AND read = FALSE
                    """),
                    {"user_id": ctx.user_id},
                )
            ).scalar_one()

    # ── UPDATE ───────────────────────────────────────────────

    async def mark_read(
        self,
        ctx: TenantContext,
        notification_id: UUID,
    ) -> bool:
        """Marca notificacao como lida. Retorna True se encontrou."""
        async with _tenant_session(ctx) as db:
            result = await db.execute(
                text("""
                    UPDATE notifications
                    SET read = TRUE, read_at = NOW()
                    WHERE id = :id AND user_id = :user_id AND read = FALSE
                """),
                {"id": str(notification_id), "user_id": ctx.user_id},
            )
        return result.rowcount > 0

    async def mark_all_read(self, ctx: TenantContext) -> int:
        """Marca todas as notificacoes do usuario como lidas. Retorna quantidade."""
        async with _tenant_session(ctx) as db:
            result = await db.execute(
                text("""
                    UPDATE notifications
                    SET read = TRUE, read_at = NOW()
                    WHERE user_id = :user_id AND read = FALSE
                """),
                {"user_id": ctx.user_id},
            )
        return result.rowcount

    # ── DELETE ───────────────────────────────────────────────

    async def delete(
        self,
        ctx: TenantContext,
        notification_id: UUID,
    ) -> bool:
        """Remove notificacao. Retorna True se encontrou."""
        async with _tenant_session(ctx) as db:
            result = await db.execute(
                text("""
                    DELETE FROM notifications
                    WHERE id = :id AND user_id = :user_id
                """),
                {"id": str(notification_id), "user_id": ctx.user_id},
            )
        return result.rowcount > 0

    # ── PREFERENCES ──────────────────────────────────────────

    async def get_preferences(
        self,
        ctx: TenantContext,
    ) -> NotificationPreferencesResponse:
        """Retorna preferencias do usuario (cria default se nao existir)."""
        async with _tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text("""
                        SELECT user_id, enabled, types_enabled, priority_min, updated_at
                        FROM notification_preferences
                        WHERE user_id = :user_id
                    """),
                    {"user_id": ctx.user_id},
                )
            ).mappings().first()

        if row:
            return NotificationPreferencesResponse(**dict(row))

        # Retorna defaults
        return NotificationPreferencesResponse(
            user_id=ctx.user_id,
            enabled=True,
            types_enabled=["appointment", "clinical", "system", "message", "alert"],
            priority_min="low",
        )

    async def update_preferences(
        self,
        ctx: TenantContext,
        data: NotificationPreferencesUpdate,
    ) -> NotificationPreferencesResponse:
        """Atualiza preferencias (upsert)."""
        current = await self.get_preferences(ctx)

        enabled = data.enabled if data.enabled is not None else current.enabled
        types_enabled = data.types_enabled if data.types_enabled is not None else current.types_enabled
        priority_min = data.priority_min if data.priority_min is not None else current.priority_min

        async with _tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text("""
                        INSERT INTO notification_preferences (user_id, enabled, types_enabled, priority_min, updated_at)
                        VALUES (:user_id, :enabled, :types_enabled, :priority_min, NOW())
                        ON CONFLICT (user_id) DO UPDATE SET
                            enabled = EXCLUDED.enabled,
                            types_enabled = EXCLUDED.types_enabled,
                            priority_min = EXCLUDED.priority_min,
                            updated_at = NOW()
                        RETURNING user_id, enabled, types_enabled, priority_min, updated_at
                    """),
                    {
                        "user_id": ctx.user_id,
                        "enabled": enabled,
                        "types_enabled": list(types_enabled),
                        "priority_min": priority_min,
                    },
                )
            ).mappings().first()

        return NotificationPreferencesResponse(**dict(row))


# ── Helpers ──────────────────────────────────────────────────

def _json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj, default=str)


def _serialize_notification(notif: dict[str, Any]) -> dict[str, Any]:
    """Serializa notificacao para envio via Redis (converte UUID/datetime)."""
    return {
        k: (str(v) if isinstance(v, UUID) else v.isoformat() if isinstance(v, datetime) else v)
        for k, v in notif.items()
    }
