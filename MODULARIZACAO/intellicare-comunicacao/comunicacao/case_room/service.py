"""Serviço de Sala de Caso Multidisciplinar (EF-COM-021)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from comunicacao.case_room.models import (
    CaseRoom,
    CaseRoomMember,
    CaseRoomStatus,
    LaunchTeleconsultResponse,
)
from comunicacao.case_room.store import CaseRoomStore
from comunicacao.rocketchat.channel_service import RocketChatChannelService
from comunicacao.rocketchat.client import RocketChatClient

logger = logging.getLogger(__name__)

_SEVERITY_EMOJI: dict[str, str] = {
    "critical": ":red_circle:",
    "high": ":orange_circle:",
    "medium": ":yellow_circle:",
    "low": ":white_circle:",
}


class CaseRoomService:
    """
    Serviço para Sala de Caso Clínico Multidisciplinar.

    Orquestra:
    - Criação de grupo privado no Rocket.Chat (#caso-{patient_id})
    - Adição de profissionais com base no plano de cuidado (EF-COM-021, critério 2)
    - Fixação de resumo clínico no canal (critério 3)
    - Roteamento de alertas do paciente para o canal (critério 4)
    - Início de teleconsulta multidisciplinar via Jitsi (critério 5)
    - Arquivamento do canal ao encerrar o caso
    """

    def __init__(
        self,
        channel_service: RocketChatChannelService,
        rc_client: RocketChatClient,
        store: CaseRoomStore,
        jitsi_url: str = "https://meet.gsi.srv.br",
    ) -> None:
        self.channel_service = channel_service
        self.rc_client = rc_client
        self.store = store
        self.jitsi_url = jitsi_url
        logger.info("CaseRoomService inicializado (jitsi_url=%s)", jitsi_url)

    async def create_or_get(
        self,
        patient_id: str,
        patient_name: str | None = None,
        members: list[CaseRoomMember] | None = None,
        initial_summary: str | None = None,
    ) -> CaseRoom:
        """
        Cria sala de caso ou retorna a existente se já ativa.

        Args:
            patient_id: ID do paciente
            patient_name: Nome do paciente (para tópico do canal)
            members: Profissionais iniciais a adicionar
            initial_summary: Resumo clínico para fixar na criação

        Returns:
            CaseRoom criada ou existente
        """
        existing = self.store.get(patient_id)
        if existing and existing.status == CaseRoomStatus.ACTIVE:
            logger.info("Sala de caso já existe: patient_id=%s", patient_id)
            return existing

        logger.info("Criando sala de caso: patient_id=%s", patient_id)

        usernames = [m.username for m in (members or [])]
        rc_channel = await self.channel_service.create_case_channel(
            patient_id=patient_id,
            patient_name=patient_name,
            members=usernames if usernames else None,
        )

        room = CaseRoom(
            patient_id=patient_id,
            patient_name=patient_name,
            rc_channel_id=rc_channel.id,
            rc_channel_name=rc_channel.name,
            rc_channel_type=rc_channel.type,
            members=list(members or []),
            status=CaseRoomStatus.ACTIVE,
        )
        self.store.save(room)

        if initial_summary:
            await self.post_summary(patient_id, initial_summary, source_module="sistema")

        logger.info(
            "Sala de caso criada: patient_id=%s, channel=%s (id=%s)",
            patient_id,
            rc_channel.name,
            rc_channel.id,
        )
        return room

    async def add_member(
        self,
        patient_id: str,
        professional_id: str,
        username: str,
        role: str = "professional",
    ) -> bool:
        """
        Adiciona profissional à sala de caso.

        Args:
            patient_id: ID do paciente
            professional_id: ID Keycloak do profissional
            username: Username RC
            role: Papel do profissional

        Returns:
            True se adicionado (ou já era membro)
        """
        room = self.store.get(patient_id)
        if not room:
            logger.warning("Sala de caso não encontrada: patient_id=%s", patient_id)
            return False

        already = any(m.professional_id == professional_id for m in room.members)
        if already:
            logger.info(
                "Membro já presente: professional_id=%s, patient_id=%s",
                professional_id,
                patient_id,
            )
            return True

        ok = await self.channel_service.add_member(
            channel_id=room.rc_channel_id,
            user_id=username,
            channel_type=room.rc_channel_type,
        )
        if ok:
            room.members.append(
                CaseRoomMember(
                    professional_id=professional_id,
                    username=username,
                    role=role,
                )
            )
            self.store.save(room)
            logger.info("Membro adicionado: %s → sala patient_id=%s", username, patient_id)
        return ok

    async def post_summary(
        self,
        patient_id: str,
        summary: str,
        source_module: str = "wanda",
    ) -> bool:
        """
        Posta resumo clínico no canal da sala (deve ser fixado manualmente pelo bot).

        Args:
            patient_id: ID do paciente
            summary: Texto do resumo clínico (Markdown)
            source_module: Módulo que gerou o resumo

        Returns:
            True se postado com sucesso
        """
        room = self.store.get(patient_id)
        if not room:
            logger.warning("Sala não encontrada para post_summary: patient_id=%s", patient_id)
            return False

        ts = datetime.now(UTC).strftime("%d/%m/%Y %H:%M")
        text = (
            f":clipboard: **Resumo Clínico** — _{source_module}_\n\n"
            f"{summary}\n\n"
            f"_Atualizado em: {ts} UTC_"
        )

        await self.rc_client.send_message(
            room_id=room.rc_channel_id,
            text=text,
            alias="IntelliCare — Resumo",
            emoji=":clipboard:",
        )

        room.last_summary_at = datetime.now(UTC)
        self.store.save(room)

        logger.info("Resumo postado: patient_id=%s, source=%s", patient_id, source_module)
        return True

    async def post_alert(
        self,
        patient_id: str,
        alert_text: str,
        severity: str = "medium",
        source_module: str = "unknown",
    ) -> bool:
        """
        Roteia alerta clínico para o canal da sala de caso.

        Args:
            patient_id: ID do paciente
            alert_text: Texto do alerta
            severity: Severidade (critical, high, medium, low)
            source_module: Módulo que gerou o alerta

        Returns:
            True se postado com sucesso
        """
        room = self.store.get(patient_id)
        if not room:
            logger.warning("Sala não encontrada para post_alert: patient_id=%s", patient_id)
            return False

        emoji = _SEVERITY_EMOJI.get(severity.lower(), ":warning:")
        ts = datetime.now(UTC).strftime("%d/%m/%Y %H:%M")
        text = (
            f"{emoji} **ALERTA CLÍNICO — {severity.upper()}** | _{source_module}_\n\n"
            f"{alert_text}\n\n"
            f"_Gerado em: {ts} UTC_"
        )

        await self.rc_client.send_message(
            room_id=room.rc_channel_id,
            text=text,
            alias="IntelliCare — Alerta",
            emoji=emoji,
        )

        room.last_alert_at = datetime.now(UTC)
        self.store.save(room)

        logger.info(
            "Alerta postado: patient_id=%s, severity=%s, source=%s",
            patient_id,
            severity,
            source_module,
        )
        return True

    async def launch_teleconsult(
        self,
        patient_id: str,
        initiator_id: str,
        initiator_username: str,
        duration_minutes: int = 30,
    ) -> LaunchTeleconsultResponse:
        """
        Inicia teleconsulta multidisciplinar: cria sala Jitsi e notifica o canal.

        Args:
            patient_id: ID do paciente
            initiator_id: ID Keycloak do profissional que inicia
            initiator_username: Username RC do iniciador
            duration_minutes: Duração prevista

        Returns:
            LaunchTeleconsultResponse com URL Jitsi

        Raises:
            ValueError: Se sala de caso não existir
        """
        room = self.store.get(patient_id)
        if not room:
            raise ValueError(f"Sala de caso não encontrada: patient_id={patient_id}")

        jitsi_room_name = f"intellicare-caso-{uuid4().hex[:12]}"
        jitsi_url = f"{self.jitsi_url}/{jitsi_room_name}"

        patient_label = room.patient_name or patient_id
        member_count = len(room.members)

        text = (
            f":video_camera: **Teleconsulta Multidisciplinar Iniciada**\n\n"
            f"**Paciente:** {patient_label}\n"
            f"**Iniciado por:** @{initiator_username}\n"
            f"**Duração prevista:** {duration_minutes} min\n\n"
            f":link: **Acesse:** {jitsi_url}\n\n"
            f"_Todos os {member_count} membro(s) desta sala foram notificados._"
        )

        await self.rc_client.send_message(
            room_id=room.rc_channel_id,
            text=text,
            alias="IntelliCare — Teleconsulta",
            emoji=":video_camera:",
        )

        logger.info(
            "Teleconsulta lançada: patient_id=%s, jitsi=%s, initiator=%s",
            patient_id,
            jitsi_room_name,
            initiator_username,
        )

        return LaunchTeleconsultResponse(
            patient_id=patient_id,
            jitsi_room_name=jitsi_room_name,
            jitsi_url=jitsi_url,
            notified_members=member_count,
            initiated_by=initiator_username,
            duration_minutes=duration_minutes,
        )

    async def archive(self, patient_id: str) -> bool:
        """
        Arquiva sala de caso (fecha canal RC).

        Args:
            patient_id: ID do paciente

        Returns:
            True se arquivada com sucesso
        """
        room = self.store.get(patient_id)
        if not room:
            logger.warning("Sala não encontrada para archive: patient_id=%s", patient_id)
            return False

        await self.channel_service.archive_channel(
            channel_id=room.rc_channel_id,
            channel_type=room.rc_channel_type,
        )

        room.status = CaseRoomStatus.ARCHIVED
        self.store.save(room)

        logger.info(
            "Sala arquivada: patient_id=%s, channel=%s",
            patient_id,
            room.rc_channel_name,
        )
        return True

    def get_room(self, patient_id: str) -> CaseRoom | None:
        """Retorna sala de caso do store (sem IO)."""
        return self.store.get(patient_id)
