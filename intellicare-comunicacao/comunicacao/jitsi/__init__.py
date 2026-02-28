"""Módulo de integração com Jitsi Meet para teleconsultas."""

from comunicacao.jitsi.client import JitsiClient
from comunicacao.jitsi.config import JitsiConfig
from comunicacao.jitsi.dispatcher import JitsiDispatcher
from comunicacao.jitsi.models import (
    JitsiParticipant,
    JitsiParticipantCreate,
    JitsiRoom,
    JitsiRoomCreate,
    JitsiRoomResponse,
    ParticipantRole,
    RoomStatus,
    RoomType,
)
from comunicacao.jitsi.room_service import RoomService

__all__ = [
    "JitsiConfig",
    "JitsiClient",
    "JitsiRoom",
    "JitsiRoomCreate",
    "JitsiRoomResponse",
    "JitsiParticipant",
    "JitsiParticipantCreate",
    "RoomType",
    "RoomStatus",
    "ParticipantRole",
    "RoomService",
    "JitsiDispatcher",
]

