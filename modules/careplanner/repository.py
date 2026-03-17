"""Repositorio da fundacao tecnica do CarePlanner."""
from __future__ import annotations

import json
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
    CareVideoSessionCreate,
    CareVideoSessionRecord,
    TaskStatus,
    cast_channel_conversation_id,
)


class CareplannerRepository:
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

    async def list_templates(self, ctx: TenantContext) -> list[CareTemplateRecord]:
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text("SELECT * FROM care_templates ORDER BY created_at DESC")
                )
            ).mappings().all()
        return [CareTemplateRecord(**dict(row)) for row in rows]

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
