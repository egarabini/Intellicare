"""Repositorio da fundacao tecnica do CarePlanner."""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.db.session import tenant_session

from .contracts import (
    CareConversationRecord,
    CareConversationUpsert,
    CareEventCreate,
    CareEventRecord,
    CareTaskCreate,
    CareTaskRecord,
    CareTemplateCreate,
    CareTemplateRecord,
    CareVideoSessionRecord,
    TaskStatus,
    cast_channel_conversation_id,
)


class CareplannerRepository:
    async def _get_active_tenant_slugs(self) -> list[str]:
        from intellicare_core.db.session import get_engine
        async with get_engine().begin() as conn:
            tenants = (await conn.execute(text("SELECT slug FROM public.tenants"))).scalars().all()
        return list(tenants)

    async def find_active_task_by_phone(self, phone_e164: str) -> UUID | None:
        """Busca correlation_id de tarefa ativa pelo phone_e164 (cross-tenant)."""
        tenants = await self._get_active_tenant_slugs()
        for slug in tenants:
            ctx = TenantContext.from_slug(slug=slug, user_id="system")
            async with tenant_session(ctx) as db:
                row = (await db.execute(text("""
                    SELECT ct.correlation_id
                    FROM care_conversations cc
                    JOIN care_tasks ct ON ct.correlation_id = cc.correlation_id
                    WHERE cc.phone_e164 = :phone
                      AND ct.status NOT IN ('CLOSED', 'FAILED', 'EXPIRED')
                      AND ct.channel = 'whatsapp'
                    ORDER BY ct.created_at DESC
                    LIMIT 1
                """), {"phone": phone_e164})).mappings().first()
                if row:
                    return row["correlation_id"]
        return None

    async def get_tenant_by_correlation(self, correlation_id: UUID) -> str:
        """Retorna tenant_slug de uma care_task pelo correlation_id."""
        tenants = await self._get_active_tenant_slugs()
        for slug in tenants:
            ctx = TenantContext.from_slug(slug=slug, user_id="system")
            async with tenant_session(ctx) as db:
                row = (await db.execute(text("""
                    SELECT tenant_slug FROM care_tasks
                    WHERE correlation_id = :cid LIMIT 1
                """), {"cid": str(correlation_id)})).mappings().first()
                if row:
                    return row["tenant_slug"]
        raise ValueError(f"Tenant nao encontrado para correlation_id={correlation_id}")

    async def create_task(self, ctx: TenantContext, payload: CareTaskCreate) -> CareTaskRecord:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO care_tasks (
                            correlation_id, kestra_execution_id, patient_ref, task_type,
                            status, channel, tenant_slug, metadata
                        )
                        VALUES (
                            :correlation_id, :kestra_execution_id, :patient_ref, :task_type,
                            :status, :channel, :tenant_slug, CAST(:metadata AS jsonb)
                        )
                        RETURNING *
                        """
                    ),
                    {
                        "correlation_id": str(payload.correlation_id),
                        "kestra_execution_id": payload.kestra_execution_id,
                        "patient_ref": payload.patient_ref,
                        "task_type": payload.task_type,
                        "status": payload.status.value,
                        "channel": payload.channel.value,
                        "tenant_slug": ctx.tenant_id,
                        "metadata": json.dumps(payload.metadata),
                    },
                )
            ).mappings().first()
        return CareTaskRecord(**dict(row))

    async def get_task(self, ctx: TenantContext, correlation_id: UUID) -> CareTaskRecord | None:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text("SELECT * FROM care_tasks WHERE correlation_id = :correlation_id"),
                    {"correlation_id": str(correlation_id)},
                )
            ).mappings().first()
        return CareTaskRecord(**dict(row)) if row else None

    async def transition_task_status(
        self,
        ctx: TenantContext,
        correlation_id: UUID,
        next_status: TaskStatus,
    ) -> CareTaskRecord | None:
        current = await self.get_task(ctx, correlation_id)
        if not current:
            return None
        TaskStatus(current.status).ensure_transition(next_status)

        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        UPDATE care_tasks
                        SET status = :status, updated_at = NOW()
                        WHERE correlation_id = :correlation_id
                        RETURNING *
                        """
                    ),
                    {"status": next_status.value, "correlation_id": str(correlation_id)},
                )
            ).mappings().first()
        return CareTaskRecord(**dict(row)) if row else None

    async def record_event_if_new(
        self,
        ctx: TenantContext,
        payload: CareEventCreate,
    ) -> tuple[CareEventRecord, bool]:
        async with tenant_session(ctx) as db:
            existing = (
                await db.execute(
                    text("SELECT * FROM care_events WHERE event_id = :event_id"),
                    {"event_id": payload.event_id},
                )
            ).mappings().first()
            if existing:
                return CareEventRecord(**dict(existing)), False

            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO care_events (
                            event_id, correlation_id, event_type, status, payload, tenant_slug
                        )
                        VALUES (
                            :event_id, :correlation_id, :event_type, :status, CAST(:payload AS jsonb), :tenant_slug
                        )
                        RETURNING *
                        """
                    ),
                    {
                        "event_id": payload.event_id,
                        "correlation_id": str(payload.correlation_id) if payload.correlation_id else None,
                        "event_type": payload.event_type.value,
                        "status": payload.status.value if payload.status else None,
                        "payload": json.dumps(payload.payload),
                        "tenant_slug": ctx.tenant_id,
                    },
                )
            ).mappings().first()
        return CareEventRecord(**dict(row)), True

    async def list_events(
        self,
        ctx: TenantContext,
        correlation_id: UUID,
        limit: int = 10,
    ) -> list[CareEventRecord]:
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        """
                        SELECT *
                        FROM care_events
                        WHERE correlation_id = :correlation_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"correlation_id": str(correlation_id), "limit": limit},
                )
            ).mappings().all()
        return [CareEventRecord(**dict(row)) for row in rows]

    async def upsert_conversation(
        self,
        ctx: TenantContext,
        payload: CareConversationUpsert,
    ) -> CareConversationRecord:
        conversation_id = cast_channel_conversation_id(payload.channel_conversation_id)
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO care_conversations (
                            correlation_id, channel, channel_conversation_id, rc_room_id,
                            phone_e164, participant_role, tenant_slug, last_interaction_at
                        )
                        VALUES (
                            :correlation_id, :channel, :channel_conversation_id, :rc_room_id,
                            :phone_e164, :participant_role, :tenant_slug, :last_interaction_at
                        )
                        ON CONFLICT (correlation_id) DO UPDATE
                        SET channel_conversation_id = EXCLUDED.channel_conversation_id,
                            rc_room_id = EXCLUDED.rc_room_id,
                            phone_e164 = EXCLUDED.phone_e164,
                            participant_role = EXCLUDED.participant_role,
                            tenant_slug = EXCLUDED.tenant_slug,
                            last_interaction_at = EXCLUDED.last_interaction_at,
                            updated_at = NOW()
                        RETURNING *
                        """
                    ),
                    {
                        "correlation_id": str(payload.correlation_id),
                        "channel": payload.channel.value,
                        "channel_conversation_id": conversation_id,
                        "rc_room_id": payload.rc_room_id,
                        "phone_e164": payload.phone_e164,
                        "participant_role": payload.participant_role.value if payload.participant_role else None,
                        "tenant_slug": ctx.tenant_id,
                        "last_interaction_at": payload.last_interaction_at,
                    },
                )
            ).mappings().first()
        return CareConversationRecord(**dict(row))

    async def get_conversation(
        self,
        ctx: TenantContext,
        correlation_id: UUID,
    ) -> CareConversationRecord | None:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text("SELECT * FROM care_conversations WHERE correlation_id = :correlation_id"),
                    {"correlation_id": str(correlation_id)},
                )
            ).mappings().first()
        return CareConversationRecord(**dict(row)) if row else None

    async def find_conversation(
        self,
        ctx: TenantContext,
        *,
        rc_room_id: str | None = None,
        channel_conversation_id: int | str | None = None,
    ) -> CareConversationRecord | None:
        conversation_id = None
        if channel_conversation_id is not None:
            conversation_id = cast_channel_conversation_id(channel_conversation_id)

        clauses: list[str] = []
        params: dict[str, Any] = {}
        if rc_room_id:
            clauses.append("rc_room_id = :rc_room_id")
            params["rc_room_id"] = rc_room_id
        if conversation_id is not None:
            clauses.append("channel_conversation_id = :channel_conversation_id")
            params["channel_conversation_id"] = conversation_id
        if not clauses:
            return None

        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        f"""
                        SELECT *
                        FROM care_conversations
                        WHERE {" OR ".join(clauses)}
                        ORDER BY updated_at DESC
                        LIMIT 1
                        """
                    ),
                    params,
                )
            ).mappings().first()
        return CareConversationRecord(**dict(row)) if row else None

    async def create_template(self, ctx: TenantContext, payload: CareTemplateCreate) -> CareTemplateRecord:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO care_templates (
                            template_code, channel, content, variables, active, tenant_slug
                        )
                        VALUES (
                            :template_code, :channel, :content, CAST(:variables AS jsonb), :active, :tenant_slug
                        )
                        RETURNING *
                        """
                    ),
                    {
                        "template_code": payload.template_code,
                        "channel": payload.channel.value,
                        "content": payload.content,
                        "variables": json.dumps(payload.variables),
                        "active": payload.active,
                        "tenant_slug": ctx.tenant_id,
                    },
                )
            ).mappings().first()
        return CareTemplateRecord(**dict(row))

    async def list_templates(
        self, ctx: TenantContext, active_only: bool = False
    ) -> list[CareTemplateRecord]:
        async with tenant_session(ctx) as db:
            sql = "SELECT * FROM care_templates"
            if active_only:
                sql += " WHERE active = TRUE"
            sql += " ORDER BY template_code ASC"
            rows = (await db.execute(text(sql))).mappings().all()
        return [CareTemplateRecord(**dict(row)) for row in rows]

    async def get_template(
        self, ctx: TenantContext, template_id: UUID
    ) -> CareTemplateRecord | None:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text("SELECT * FROM care_templates WHERE id = :id"),
                    {"id": str(template_id)},
                )
            ).mappings().first()
        return CareTemplateRecord(**dict(row)) if row else None

    async def update_template(
        self,
        ctx: TenantContext,
        template_id: UUID,
        content: str,
        variables: list[str],
        active: bool,
    ) -> CareTemplateRecord | None:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        UPDATE care_templates
                        SET content   = :content,
                            variables = CAST(:variables AS jsonb),
                            active    = :active,
                            updated_at = NOW()
                        WHERE id = :id AND tenant_slug = :tenant_slug
                        RETURNING *
                        """
                    ),
                    {
                        "content": content,
                        "variables": json.dumps(variables),
                        "active": active,
                        "id": str(template_id),
                        "tenant_slug": ctx.tenant_id,
                    },
                )
            ).mappings().first()
        return CareTemplateRecord(**dict(row)) if row else None

    async def get_template_by_code(
        self,
        ctx: TenantContext,
        template_code: str,
        channel: str = "rocketchat",
    ) -> CareTemplateRecord | None:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        SELECT *
                        FROM care_templates
                        WHERE template_code = :template_code
                          AND channel = :channel
                          AND active = TRUE
                        ORDER BY updated_at DESC
                        LIMIT 1
                        """
                    ),
                    {"template_code": template_code, "channel": channel},
                )
            ).mappings().first()
        return CareTemplateRecord(**dict(row)) if row else None

    async def create_video_session(
        self,
        ctx: TenantContext,
        payload: CareVideoSessionCreate,
    ) -> CareVideoSessionRecord:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        INSERT INTO care_video_sessions (
                            correlation_id, room_name, clinico_jwt, patient_jwt,
                            expires_at, clinico_ref, patient_ref, tenant_slug
                        )
                        VALUES (
                            :correlation_id, :room_name, :clinico_jwt, :patient_jwt,
                            :expires_at, :clinico_ref, :patient_ref, :tenant_slug
                        )
                        RETURNING *
                        """
                    ),
                    {
                        "correlation_id": str(payload.correlation_id),
                        "room_name": payload.room_name,
                        "clinico_jwt": payload.clinico_jwt,
                        "patient_jwt": payload.patient_jwt,
                        "expires_at": payload.expires_at,
                        "clinico_ref": payload.clinico_ref,
                        "patient_ref": payload.patient_ref,
                        "tenant_slug": ctx.tenant_id,
                    },
                )
            ).mappings().first()
        return CareVideoSessionRecord(**dict(row))

    async def get_video_session(
        self,
        ctx: TenantContext,
        correlation_id: UUID,
    ) -> CareVideoSessionRecord | None:
        async with tenant_session(ctx) as db:
            row = (
                await db.execute(
                    text(
                        """
                        SELECT *
                        FROM care_video_sessions
                        WHERE correlation_id = :correlation_id
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {"correlation_id": str(correlation_id)},
                )
            ).mappings().first()
        return CareVideoSessionRecord(**dict(row)) if row else None

    async def list_tasks(
        self,
        ctx: TenantContext,
        *,
        status_filter: TaskStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[CareTaskRecord]:
        offset = max(page - 1, 0) * page_size
        query = """
            SELECT *
            FROM care_tasks
        """
        params: dict[str, Any] = {"limit": page_size, "offset": offset}
        if status_filter:
            query += " WHERE status = :status"
            params["status"] = status_filter.value
        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"

        async with tenant_session(ctx) as db:
            rows = (await db.execute(text(query), params)).mappings().all()
        return [CareTaskRecord(**dict(row)) for row in rows]
