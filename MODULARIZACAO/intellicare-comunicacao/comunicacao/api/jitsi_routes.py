"""Endpoints REST para Jitsi Meet."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.jitsi import (
    JitsiConfig,
    JitsiParticipantCreate,
    JitsiRoomCreate,
    JitsiRoomResponse,
    ParticipantRole,
    RoomService,
    RoomStatus,
)
from comunicacao.storage.repository import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jitsi", tags=["jitsi"])


# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════════

def get_jitsi_config() -> JitsiConfig:
    """Dependency para obter configuração Jitsi."""
    return JitsiConfig.from_env()


async def get_room_service(
    db: AsyncSession = Depends(get_db_session),
    config: JitsiConfig = Depends(get_jitsi_config),
) -> RoomService:
    """Dependency para obter RoomService."""
    return RoomService(db, config)


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class RoomListResponse(BaseModel):
    """Response de listagem de salas."""
    
    rooms: list[JitsiRoomResponse]
    total: int
    limit: int
    offset: int


class ParticipantResponse(BaseModel):
    """Response de participante."""
    
    id: UUID
    room_id: UUID
    user_id: str
    user_name: str
    user_email: str | None
    role: ParticipantRole
    invited_at: str
    joined_at: str | None
    left_at: str | None
    room_url: str
    
    class Config:
        from_attributes = True


class AddParticipantRequest(BaseModel):
    """Request para adicionar participante."""
    
    user_id: str
    user_name: str
    user_email: str | None = None
    role: ParticipantRole = ParticipantRole.PARTICIPANT
    expires_in_minutes: int = Field(default=60, ge=5, le=480)


class WebhookEvent(BaseModel):
    """Evento de webhook do Jitsi."""
    
    event_type: str = Field(..., description="Tipo de evento (room.created, participant.joined, etc.)")
    room_name: str
    participant_id: str | None = None
    timestamp: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS - ROOMS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/rooms", response_model=JitsiRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: JitsiRoomCreate,
    room_service: RoomService = Depends(get_room_service),
) -> JitsiRoomResponse:
    """
    Cria nova sala Jitsi.
    
    **Permissões**: `comunicacao_write`
    """
    try:
        room = await room_service.create_room(room_data)
        return room_service.build_room_response(room)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Erro ao criar sala Jitsi")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao criar sala")


@router.get("/rooms/{room_id}", response_model=JitsiRoomResponse)
async def get_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
) -> JitsiRoomResponse:
    """
    Busca sala por ID.
    
    **Permissões**: `comunicacao_read`
    """
    room = await room_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sala {room_id} não encontrada")
    
    return room_service.build_room_response(room)


@router.get("/rooms", response_model=RoomListResponse)
async def list_rooms(
    status_filter: RoomStatus | None = Query(None, alias="status"),
    patient_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    room_service: RoomService = Depends(get_room_service),
) -> RoomListResponse:
    """
    Lista salas com filtros.
    
    **Permissões**: `comunicacao_read`
    """
    rooms = await room_service.list_rooms(
        status=status_filter,
        patient_id=patient_id,
        limit=limit,
        offset=offset,
    )
    
    return RoomListResponse(
        rooms=[room_service.build_room_response(room) for room in rooms],
        total=len(rooms),
        limit=limit,
        offset=offset,
    )


@router.post("/rooms/{room_id}/start", response_model=JitsiRoomResponse)
async def start_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
) -> JitsiRoomResponse:
    """
    Inicia sala (marca como ACTIVE).

    **Permissões**: `comunicacao_write`
    """
    try:
        room = await room_service.start_room(room_id)
        return room_service.build_room_response(room)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Erro ao iniciar sala")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao iniciar sala")


@router.post("/rooms/{room_id}/end", response_model=JitsiRoomResponse)
async def end_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
) -> JitsiRoomResponse:
    """
    Finaliza sala (marca como COMPLETED).

    **Permissões**: `comunicacao_write`
    """
    try:
        room = await room_service.end_room(room_id)
        return room_service.build_room_response(room)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Erro ao finalizar sala")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao finalizar sala")


@router.post("/rooms/{room_id}/cancel", response_model=JitsiRoomResponse)
async def cancel_room(
    room_id: UUID,
    room_service: RoomService = Depends(get_room_service),
) -> JitsiRoomResponse:
    """
    Cancela sala (marca como CANCELLED).

    **Permissões**: `comunicacao_write`
    """
    try:
        room = await room_service.cancel_room(room_id)
        return room_service.build_room_response(room)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Erro ao cancelar sala")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao cancelar sala")


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS - PARTICIPANTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/rooms/{room_id}/participants", response_model=ParticipantResponse, status_code=status.HTTP_201_CREATED)
async def add_participant(
    room_id: UUID,
    request: AddParticipantRequest,
    room_service: RoomService = Depends(get_room_service),
    config: JitsiConfig = Depends(get_jitsi_config),
) -> ParticipantResponse:
    """
    Adiciona participante à sala.

    Retorna URL da sala com token JWT para o participante.

    **Permissões**: `comunicacao_write`
    """
    try:
        participant_data = JitsiParticipantCreate(
            user_id=request.user_id,
            user_name=request.user_name,
            user_email=request.user_email,
            role=request.role,
        )

        participant = await room_service.add_participant(
            room_id=room_id,
            participant_data=participant_data,
            expires_in_minutes=request.expires_in_minutes,
        )

        # Buscar sala para gerar URL
        room = await room_service.get_room(room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sala {room_id} não encontrada")

        from comunicacao.jitsi.client import JitsiClient
        client = JitsiClient(config)
        room_url = client.get_room_url(room.room_name, participant.jwt_token)

        return ParticipantResponse(
            id=participant.id,
            room_id=participant.room_id,
            user_id=participant.user_id,
            user_name=participant.user_name,
            user_email=participant.user_email,
            role=participant.role,
            invited_at=participant.invited_at.isoformat(),
            joined_at=participant.joined_at.isoformat() if participant.joined_at else None,
            left_at=participant.left_at.isoformat() if participant.left_at else None,
            room_url=room_url,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Erro ao adicionar participante")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Erro ao adicionar participante")


@router.delete("/participants/{participant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_participant(
    participant_id: UUID,
    room_service: RoomService = Depends(get_room_service),
) -> None:
    """
    Remove participante da sala.

    **Permissões**: `comunicacao_write`
    """
    success = await room_service.remove_participant(participant_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Participante {participant_id} não encontrado")


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS - WEBHOOKS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def jitsi_webhook(
    event: WebhookEvent,
    room_service: RoomService = Depends(get_room_service),
) -> dict[str, str]:
    """
    Recebe eventos do Jitsi Meet.

    Eventos suportados:
    - room.created: Sala criada
    - room.destroyed: Sala destruída
    - participant.joined: Participante entrou
    - participant.left: Participante saiu

    **Nota**: Este endpoint deve ser configurado no Jitsi Meet para enviar webhooks.
    """
    logger.info("Jitsi webhook recebido: event_type=%s, room_name=%s", event.event_type, event.room_name)

    try:
        # Buscar sala por nome
        room = await room_service.get_room_by_name(event.room_name)
        if not room:
            logger.warning("Sala não encontrada: room_name=%s", event.room_name)
            return {"status": "ignored", "reason": "room_not_found"}

        # Processar evento
        if event.event_type == "participant.joined":
            if event.participant_id:
                updated = await room_service.mark_participant_joined(room.id, event.participant_id)
                logger.info(
                    "Participante entrou: room=%s, participant=%s, updated=%s",
                    event.room_name,
                    event.participant_id,
                    updated,
                )
            else:
                logger.warning("participant.joined sem participant_id: room=%s", event.room_name)

        elif event.event_type == "participant.left":
            if event.participant_id:
                updated = await room_service.mark_participant_left(room.id, event.participant_id)
                logger.info(
                    "Participante saiu: room=%s, participant=%s, updated=%s",
                    event.room_name,
                    event.participant_id,
                    updated,
                )
            else:
                logger.warning("participant.left sem participant_id: room=%s", event.room_name)

        elif event.event_type == "room.destroyed":
            # Finalizar sala automaticamente
            if room.status == RoomStatus.ACTIVE:
                await room_service.end_room(room.id)
                logger.info("Sala finalizada automaticamente: room=%s", event.room_name)

        return {"status": "processed"}

    except Exception as e:
        logger.exception("Erro ao processar webhook Jitsi")
        return {"status": "error", "message": str(e)}
