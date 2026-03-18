"""Servicos de orquestracao do CarePlanner."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import text

from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error
from intellicare_core.db.session import get_engine, tenant_session

from .adapters.jitsi import JitsiAdapter
from .adapters.kestra import KestraAdapter
from .adapters.rocketchat import RocketChatAdapter
from .config import CareplannerSettings, get_careplanner_settings
from .contracts import (
    CareConversationUpsert,
    CareEventCreate,
    CareTaskCreate,
    CareVideoSessionCreate,
    Channel,
    EventType,
    ParticipantRole,
    TaskStatus,
    cast_channel_conversation_id,
)
from .integrations import notify_clinico_replied, trigger_cuidado_encounter
from .metrics import (
    careplanner_dispatch_to_sent_seconds,
    careplanner_dispatch_total,
    careplanner_event_total,
    careplanner_inbound_to_close_seconds,
    careplanner_orphan_inbound_total,
    careplanner_video_session_total,
)
from .repository import CareplannerRepository
from .security import mask_content, mask_phone
from .workers.dispatcher import enqueue_dispatch

logger = logging.getLogger(__name__)


class CareplannerService:
    def __init__(
        self,
        repo: CareplannerRepository,
        rc: RocketChatAdapter,
        jitsi: JitsiAdapter,
        kestra: KestraAdapter,
        settings: CareplannerSettings | None = None,
    ) -> None:
        self._repo = repo
        self._rc = rc
        self._jitsi = jitsi
        self._kestra = kestra
        self._settings = settings or get_careplanner_settings()

    async def open_task(
        self,
        ctx: TenantContext,
        kestra_execution_id: str,
        patient_ref: str,
        task_type: str,
        template_code: str,
        template_variables: dict,
        contact_phone: str | None = None,
        contact_role: str = "PACIENTE",
    ) -> dict:
        correlation_id = uuid4()
        logger.debug(
            "open_task: tenant=%s patient=%s phone=%s",
            ctx.tenant_id,
            patient_ref,
            mask_phone(contact_phone),
        )
        task = await self._repo.create_task(
            ctx,
            CareTaskCreate(
                correlation_id=correlation_id,
                kestra_execution_id=kestra_execution_id,
                patient_ref=patient_ref,
                task_type=task_type,
                metadata={
                    "template_code": template_code,
                    "template_variables": template_variables,
                    "contact_phone": contact_phone,
                    "contact_role": contact_role,
                },
            ),
        )
        await enqueue_dispatch(str(task.correlation_id), ctx.tenant_id)
        return {"ok": True, "correlation_id": str(task.correlation_id), "status": TaskStatus.CREATED.value}

    async def process_message_sent(
        self,
        ctx: TenantContext,
        event_id: str,
        correlation_id: UUID,
        rc_room_id: str,
        channel_conversation_id: str | int,
    ) -> dict:
        conversation_id = cast_channel_conversation_id(channel_conversation_id)
        record, created = await self._repo.record_event_if_new(
            ctx,
            CareEventCreate(
                event_id=event_id,
                correlation_id=correlation_id,
                event_type=EventType.MESSAGE_SENT,
                status=TaskStatus.SENT,
                payload={
                    "rc_room_id": rc_room_id,
                    "channel_conversation_id": conversation_id,
                },
            ),
        )
        if not created:
            return {"ok": True, "duplicate": True, "event_id": record.event_id}

        current_conversation = await self._repo.get_conversation(ctx, correlation_id)
        await self._repo.upsert_conversation(
            ctx,
            CareConversationUpsert(
                correlation_id=correlation_id,
                channel=Channel.ROCKETCHAT,
                channel_conversation_id=conversation_id,
                rc_room_id=rc_room_id,
                phone_e164=current_conversation.phone_e164 if current_conversation else None,
                participant_role=ParticipantRole(current_conversation.participant_role)
                if current_conversation and current_conversation.participant_role
                else None,
                last_interaction_at=current_conversation.last_interaction_at if current_conversation else None,
            ),
        )
        task = await self._repo.get_task(ctx, correlation_id)
        await self._repo.transition_task_status(ctx, correlation_id, TaskStatus.SENT)
        careplanner_event_total.labels(tenant_slug=ctx.tenant_id, event_type="MESSAGE_SENT").inc()
        if task:
            delta = max((datetime.now(tz=timezone.utc) - task.updated_at).total_seconds(), 0)
            careplanner_dispatch_to_sent_seconds.labels(tenant_slug=ctx.tenant_id).observe(delta)
        return {"ok": True, "status": TaskStatus.SENT.value}

    async def process_inbound(
        self,
        ctx: TenantContext,
        event_id: str,
        rc_room_id: str,
        channel_conversation_id: str | int,
        content: str,
        occurred_at: str | None = None,
    ) -> dict:
        conversation_id = cast_channel_conversation_id(channel_conversation_id)
        logger.info(
            "inbound: tenant=%s room=%s content=%s",
            ctx.tenant_id,
            rc_room_id,
            mask_content(content),
        )
        conversation = await self._repo.find_conversation(
            ctx,
            rc_room_id=rc_room_id,
            channel_conversation_id=conversation_id,
        )
        if not conversation:
            await self._repo.record_event_if_new(
                ctx,
                CareEventCreate(
                    event_id=event_id,
                    correlation_id=None,
                    event_type=EventType.ORPHAN_INBOUND,
                    payload={
                        "rc_room_id": rc_room_id,
                        "channel_conversation_id": conversation_id,
                    },
                ),
            )
            careplanner_orphan_inbound_total.labels(tenant_slug=ctx.tenant_id).inc()
            return {"ok": True, "orphan": True}

        record, created = await self._repo.record_event_if_new(
            ctx,
            CareEventCreate(
                event_id=event_id,
                correlation_id=conversation.correlation_id,
                event_type=EventType.INBOUND_RECEIVED,
                status=TaskStatus.REPLIED,
                payload={
                    "rc_room_id": rc_room_id,
                    "channel_conversation_id": conversation_id,
                    "content": content,
                    "occurred_at": occurred_at,
                },
            ),
        )
        if not created:
            return {
                "ok": True,
                "duplicate": True,
                "correlation_id": str(record.correlation_id) if record.correlation_id else None,
            }

        task = await self._repo.get_task(ctx, conversation.correlation_id)
        if not task:
            raise api_error(404, "task_not_found", "Jornada nao encontrada")

        current_status = TaskStatus(task.status)
        if current_status in {TaskStatus.SENT, TaskStatus.DISPATCHED}:
            await self._repo.transition_task_status(ctx, conversation.correlation_id, TaskStatus.REPLIED)
            careplanner_event_total.labels(tenant_slug=ctx.tenant_id, event_type="INBOUND_RECEIVED").inc()

        interaction_at = (
            datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
            if occurred_at
            else datetime.now(tz=timezone.utc)
        )
        await self._repo.upsert_conversation(
            ctx,
            CareConversationUpsert(
                correlation_id=conversation.correlation_id,
                channel=conversation.channel,
                channel_conversation_id=conversation_id,
                rc_room_id=conversation.rc_room_id,
                phone_e164=conversation.phone_e164,
                participant_role=ParticipantRole(conversation.participant_role)
                if conversation.participant_role
                else None,
                last_interaction_at=interaction_at,
            ),
        )
        if task.kestra_execution_id:
            await self._kestra.resume_execution(task.kestra_execution_id, {"content": content})
        clinico_ref = task.metadata.get("clinico_ref") if task.metadata else None
        await notify_clinico_replied(
            ctx,
            correlation_id=conversation.correlation_id,
            task_type=task.task_type,
            patient_ref=task.patient_ref,
            clinico_ref=clinico_ref,
            content=content,
        )
        await trigger_cuidado_encounter(
            ctx,
            correlation_id=conversation.correlation_id,
            task_type=task.task_type,
            patient_ref=task.patient_ref,
        )
        return {
            "ok": True,
            "status": TaskStatus.REPLIED.value,
            "correlation_id": str(conversation.correlation_id),
        }

    async def process_inbound_from_webhook(
        self,
        event_id: str,
        rc_room_id: str,
        channel_conversation_id: str | int,
        content: str,
        occurred_at: str | None = None,
    ) -> dict:
        async with get_engine().begin() as conn:
            tenants = (await conn.execute(text("SELECT slug FROM public.tenants"))).scalars().all()
        for slug in tenants:
            ctx = TenantContext.from_slug(slug=slug, user_id="rocketchat-webhook")
            conversation = await self._repo.find_conversation(
                ctx,
                rc_room_id=rc_room_id,
                channel_conversation_id=channel_conversation_id,
            )
            if conversation:
                return await self.process_inbound(
                    ctx,
                    event_id=event_id,
                    rc_room_id=rc_room_id,
                    channel_conversation_id=channel_conversation_id,
                    content=content,
                    occurred_at=occurred_at,
                )
        logger.warning("Inbound Rocket.Chat sem correlacao: room=%s", rc_room_id)
        return {"ok": True, "orphan": True}

    async def open_video_session(
        self,
        ctx: TenantContext,
        correlation_id: UUID,
        clinico_ref: str,
    ) -> dict:
        task = await self._repo.get_task(ctx, correlation_id)
        if not task:
            raise api_error(404, "task_not_found", "Jornada nao encontrada")
        room_name = self._jitsi.build_room_name(ctx.tenant_id, str(correlation_id))
        clinico_jwt = self._jitsi.generate_room_jwt(room_name, clinico_ref, clinico_ref, is_moderator=True)
        patient_jwt = self._jitsi.generate_room_jwt(
            room_name,
            task.patient_ref,
            task.patient_ref,
            is_moderator=False,
        )
        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            minutes=self._settings.jitsi_default_room_duration
        )
        if self._jitsi.is_expired(expires_at):
            raise api_error(400, "jwt_expired", "JWT Jitsi expirado imediatamente — checar JITSI_DEFAULT_ROOM_DURATION")
        await self._repo.create_video_session(
            ctx,
            CareVideoSessionCreate(
                correlation_id=correlation_id,
                room_name=room_name,
                clinico_jwt=clinico_jwt,
                patient_jwt=patient_jwt,
                expires_at=expires_at,
                clinico_ref=clinico_ref,
                patient_ref=task.patient_ref,
            ),
        )
        clinico_url = self._jitsi.get_room_url(room_name, clinico_jwt)
        patient_url = self._jitsi.get_room_url(room_name, patient_jwt)
        conversation = await self._repo.get_conversation(ctx, correlation_id)
        if conversation and conversation.rc_room_id:
            await self._rc.post_message(conversation.rc_room_id, f"Sua videoconsulta: {patient_url}")
        await self._repo.record_event_if_new(
            ctx,
            CareEventCreate(
                event_id=f"video-{correlation_id}",
                correlation_id=correlation_id,
                event_type=EventType.VIDEO_SESSION_OPENED,
                payload={"room_name": room_name},
            ),
        )
        careplanner_video_session_total.labels(tenant_slug=ctx.tenant_id).inc()
        careplanner_event_total.labels(tenant_slug=ctx.tenant_id, event_type="VIDEO_SESSION_OPENED").inc()
        return {
            "room_name": room_name,
            "clinico_url": clinico_url,
            "patient_url": patient_url,
            "expires_at": expires_at.isoformat(),
        }

    async def close_task(self, ctx: TenantContext, correlation_id: UUID) -> dict:
        task = await self._repo.get_task(ctx, correlation_id)
        if not task:
            raise api_error(404, "task_not_found", "Jornada nao encontrada")
        replied_at = task.updated_at if task.status == TaskStatus.REPLIED else None
        await self._repo.transition_task_status(ctx, correlation_id, TaskStatus.CLOSED)
        conversation = await self._repo.get_conversation(ctx, correlation_id)
        if conversation and conversation.rc_room_id:
            await self._rc.archive_room(conversation.rc_room_id)
        await self._repo.record_event_if_new(
            ctx,
            CareEventCreate(
                event_id=f"close-{correlation_id}",
                correlation_id=correlation_id,
                event_type=EventType.TASK_CLOSED,
                status=TaskStatus.CLOSED,
                payload={},
            ),
        )
        careplanner_event_total.labels(tenant_slug=ctx.tenant_id, event_type="TASK_CLOSED").inc()
        if replied_at:
            delta = max((datetime.now(tz=timezone.utc) - replied_at).total_seconds(), 0)
            careplanner_inbound_to_close_seconds.labels(tenant_slug=ctx.tenant_id).observe(delta)
        return {"ok": True, "status": TaskStatus.CLOSED.value}

    async def get_task_details(self, ctx: TenantContext, correlation_id: UUID) -> dict:
        task = await self._repo.get_task(ctx, correlation_id)
        if not task:
            raise api_error(404, "task_not_found", "Jornada nao encontrada")
        conversation = await self._repo.get_conversation(ctx, correlation_id)
        events = await self._repo.list_events(ctx, correlation_id, limit=10)
        return {
            "task": task.model_dump(mode="json"),
            "conversation": conversation.model_dump(mode="json") if conversation else None,
            "events": [event.model_dump(mode="json") for event in events],
        }

    async def list_tasks(self, ctx: TenantContext, status_filter: str | None = None, page: int = 1) -> dict:
        normalized = TaskStatus(status_filter) if status_filter else None
        tasks = await self._repo.list_tasks(ctx, status_filter=normalized, page=page)
        return {"items": [task.model_dump(mode="json") for task in tasks], "page": page}

    async def get_dashboard_stats(self, ctx: TenantContext) -> dict:
        async with tenant_session(ctx) as db:
            rows = (
                await db.execute(
                    text(
                        """
                        SELECT status, COUNT(*) as cnt
                        FROM care_tasks
                        GROUP BY status
                        """
                    )
                )
            ).mappings().all()
            recent = (
                await db.execute(
                    text(
                        """
                        SELECT correlation_id, patient_ref, task_type, status, updated_at
                        FROM care_tasks
                        ORDER BY updated_at DESC
                        LIMIT 5
                        """
                    )
                )
            ).mappings().all()

        by_status = {status.value: 0 for status in TaskStatus}
        total = 0
        for row in rows:
            by_status[row["status"]] = row["cnt"]
            total += row["cnt"]

        return {
            "total": total,
            "by_status": by_status,
            "recent_tasks": [
                {
                    "correlation_id": str(row["correlation_id"]),
                    "patient_ref": row["patient_ref"],
                    "task_type": row["task_type"],
                    "status": row["status"],
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                }
                for row in recent
            ],
        }

    async def get_video_session_info(self, ctx: TenantContext, correlation_id: UUID) -> dict:
        session = await self._repo.get_video_session(ctx, correlation_id)
        if not session:
            raise api_error(404, "video_session_not_found", "Sessao de video nao encontrada")
        return {
            "room_name": session.room_name,
            "clinico_url": self._jitsi.get_room_url(session.room_name, session.clinico_jwt),
            "patient_url": self._jitsi.get_room_url(session.room_name, session.patient_jwt),
            "expires_at": session.expires_at.isoformat(),
            "expired": self._jitsi.is_expired(session.expires_at),
        }


def build_careplanner_service() -> CareplannerService:
    settings = get_careplanner_settings()
    repo = CareplannerRepository()
    rc = RocketChatAdapter(settings)
    jitsi = JitsiAdapter(settings)
    kestra = KestraAdapter(settings)
    return CareplannerService(repo=repo, rc=rc, jitsi=jitsi, kestra=kestra, settings=settings)
