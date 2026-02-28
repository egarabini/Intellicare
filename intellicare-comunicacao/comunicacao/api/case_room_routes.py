"""Rotas para Sala de Caso Multidisciplinar (EF-COM-021)."""

from __future__ import annotations

import logging
from typing import Any, Callable

from fastapi import APIRouter, HTTPException

from comunicacao.case_room.models import (
    AddMemberRequest,
    CreateCaseRoomRequest,
    LaunchTeleconsultRequest,
    LaunchTeleconsultResponse,
    PostAlertRequest,
    PostSummaryRequest,
)
from comunicacao.case_room.service import CaseRoomService

logger = logging.getLogger(__name__)


def create_case_room_router(state_fn: Callable[[], dict[str, Any]]) -> APIRouter:
    """
    Cria router para Sala de Caso Multidisciplinar.

    Endpoints (EF-COM-021):
        POST   /api/v1/case-room/{patient_id}             — Criar sala
        GET    /api/v1/case-room/{patient_id}             — Consultar sala
        POST   /api/v1/case-room/{patient_id}/members     — Adicionar membro
        POST   /api/v1/case-room/{patient_id}/summary     — Fixar resumo clínico
        POST   /api/v1/case-room/{patient_id}/alert       — Rotear alerta ao canal
        POST   /api/v1/case-room/{patient_id}/teleconsult — Iniciar teleconsulta
        DELETE /api/v1/case-room/{patient_id}/archive     — Arquivar sala

    Args:
        state_fn: Callable que retorna o dict de estado da aplicação
    """
    router = APIRouter(prefix="/api/v1/case-room", tags=["case-room"])

    def _get_service() -> CaseRoomService:
        service = state_fn().get("case_room_service")
        if service is None:
            raise HTTPException(
                status_code=503,
                detail="CaseRoomService não disponível (RC não configurado)",
            )
        return service

    @router.post("/{patient_id}", summary="Criar sala de caso multidisciplinar")
    async def create_case_room(patient_id: str, body: CreateCaseRoomRequest) -> dict[str, Any]:
        """
        Cria grupo privado no Rocket.Chat para discussão multidisciplinar do caso.

        Se já existir sala ativa para o paciente, retorna a existente.
        Profissionais da lista `professionals` são adicionados ao grupo.
        Se `initial_summary` for informado, é postado como resumo fixado no canal.
        """
        service = _get_service()
        room = await service.create_or_get(
            patient_id=patient_id,
            patient_name=body.patient_name,
            members=body.professionals or None,
            initial_summary=body.initial_summary,
        )
        return {
            "ok": True,
            "patient_id": room.patient_id,
            "patient_name": room.patient_name,
            "rc_channel_id": room.rc_channel_id,
            "rc_channel_name": room.rc_channel_name,
            "members_count": len(room.members),
            "status": room.status,
            "created_at": room.created_at.isoformat(),
        }

    @router.get("/{patient_id}", summary="Consultar sala de caso")
    def get_case_room(patient_id: str) -> dict[str, Any]:
        """Retorna informações da sala de caso do paciente, incluindo membros e timestamps."""
        service = _get_service()
        room = service.get_room(patient_id)
        if not room:
            raise HTTPException(
                status_code=404,
                detail=f"Sala de caso não encontrada: patient_id={patient_id}",
            )
        return {
            "ok": True,
            "patient_id": room.patient_id,
            "patient_name": room.patient_name,
            "rc_channel_id": room.rc_channel_id,
            "rc_channel_name": room.rc_channel_name,
            "members": [m.model_dump() for m in room.members],
            "status": room.status,
            "created_at": room.created_at.isoformat(),
            "updated_at": room.updated_at.isoformat(),
            "last_summary_at": room.last_summary_at.isoformat() if room.last_summary_at else None,
            "last_alert_at": room.last_alert_at.isoformat() if room.last_alert_at else None,
        }

    @router.post("/{patient_id}/members", summary="Adicionar membro à sala")
    async def add_member(patient_id: str, body: AddMemberRequest) -> dict[str, Any]:
        """
        Adiciona profissional ao grupo privado RC da sala de caso.

        Idempotente: se o profissional já for membro, retorna sucesso sem duplicar.
        """
        service = _get_service()
        ok = await service.add_member(
            patient_id=patient_id,
            professional_id=body.professional_id,
            username=body.username,
            role=body.role,
        )
        if not ok:
            room = service.get_room(patient_id)
            status_code = 404 if room is None else 502
            detail = (
                f"Sala de caso não encontrada: patient_id={patient_id}"
                if room is None
                else "Falha ao adicionar membro no Rocket.Chat"
            )
            raise HTTPException(status_code=status_code, detail=detail)
        return {"ok": True, "patient_id": patient_id, "username": body.username, "added": ok}

    @router.post("/{patient_id}/summary", summary="Fixar resumo clínico no canal")
    async def post_summary(patient_id: str, body: PostSummaryRequest) -> dict[str, Any]:
        """
        Posta resumo clínico (Wanda/Florence) no canal da sala de caso.

        O resumo é enviado com formatação Markdown e timestamp de atualização.
        """
        service = _get_service()
        ok = await service.post_summary(
            patient_id=patient_id,
            summary=body.summary,
            source_module=body.source_module,
        )
        if not ok:
            raise HTTPException(
                status_code=404,
                detail=f"Sala de caso não encontrada: patient_id={patient_id}",
            )
        return {"ok": True, "patient_id": patient_id, "posted": True}

    @router.post("/{patient_id}/alert", summary="Rotear alerta ao canal da sala")
    async def post_alert(patient_id: str, body: PostAlertRequest) -> dict[str, Any]:
        """
        Roteia alerta clínico (Oswaldo/Florence) para o canal da sala de caso.

        O alerta inclui emoji de severidade, fonte do módulo e timestamp.
        """
        service = _get_service()
        ok = await service.post_alert(
            patient_id=patient_id,
            alert_text=body.alert_text,
            severity=body.severity,
            source_module=body.source_module,
        )
        if not ok:
            raise HTTPException(
                status_code=404,
                detail=f"Sala de caso não encontrada: patient_id={patient_id}",
            )
        return {"ok": True, "patient_id": patient_id, "severity": body.severity, "posted": True}

    @router.post(
        "/{patient_id}/teleconsult",
        response_model=LaunchTeleconsultResponse,
        summary="Iniciar teleconsulta multidisciplinar",
    )
    async def launch_teleconsult(
        patient_id: str, body: LaunchTeleconsultRequest
    ) -> LaunchTeleconsultResponse:
        """
        Cria sala Jitsi para teleconsulta e notifica todos os membros via canal RC.

        O link Jitsi gerado (intellicare-caso-{uuid}) é postado no canal da sala.
        """
        service = _get_service()
        try:
            return await service.launch_teleconsult(
                patient_id=patient_id,
                initiator_id=body.initiator_id,
                initiator_username=body.initiator_username,
                duration_minutes=body.duration_minutes,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.delete("/{patient_id}/archive", summary="Arquivar sala de caso")
    async def archive_case_room(patient_id: str) -> dict[str, Any]:
        """Arquiva a sala de caso: marca como ARCHIVED e tenta fechar o canal RC."""
        service = _get_service()
        ok = await service.archive(patient_id)
        if not ok:
            raise HTTPException(
                status_code=404,
                detail=f"Sala de caso não encontrada: patient_id={patient_id}",
            )
        return {"ok": True, "patient_id": patient_id, "archived": True}

    return router
