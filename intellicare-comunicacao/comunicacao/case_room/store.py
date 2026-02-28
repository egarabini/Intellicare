"""Store in-memory para Salas de Caso (EF-COM-021)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from comunicacao.case_room.models import CaseRoom, CaseRoomStatus

logger = logging.getLogger(__name__)


class CaseRoomStore:
    """
    Store in-memory para rastrear salas de caso ativas.

    Keyed por patient_id. Pode ser substituído por repositório PostgreSQL.
    """

    def __init__(self) -> None:
        self._rooms: dict[str, CaseRoom] = {}
        logger.info("CaseRoomStore inicializado (in-memory)")

    def get(self, patient_id: str) -> CaseRoom | None:
        """Retorna sala de caso do paciente, ou None se não existir."""
        return self._rooms.get(patient_id)

    def save(self, room: CaseRoom) -> None:
        """Persiste (cria ou atualiza) sala de caso."""
        room.updated_at = datetime.now(UTC)
        self._rooms[room.patient_id] = room
        logger.debug(
            "CaseRoom salva: patient_id=%s, channel=%s",
            room.patient_id,
            room.rc_channel_name,
        )

    def list_active(self) -> list[CaseRoom]:
        """Lista todas as salas com status ACTIVE."""
        return [r for r in self._rooms.values() if r.status == CaseRoomStatus.ACTIVE]

    def delete(self, patient_id: str) -> bool:
        """Remove sala do store. Retorna True se existia."""
        if patient_id in self._rooms:
            del self._rooms[patient_id]
            logger.debug("CaseRoom removida: patient_id=%s", patient_id)
            return True
        return False

    def count(self) -> int:
        """Total de salas no store."""
        return len(self._rooms)
