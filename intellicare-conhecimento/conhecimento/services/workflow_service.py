from __future__ import annotations

from conhecimento.models import Protocol, ProtocolStatus
from conhecimento.services.protocol_service import ProtocolService


class WorkflowService:
    """Simple approval/publishing workflow for protocols."""

    _allowed: dict[ProtocolStatus, set[ProtocolStatus]] = {
        ProtocolStatus.DRAFT: {ProtocolStatus.REVIEW},
        ProtocolStatus.REVIEW: {ProtocolStatus.APPROVAL, ProtocolStatus.DRAFT},
        ProtocolStatus.APPROVAL: {ProtocolStatus.PUBLISHED, ProtocolStatus.REVIEW},
        ProtocolStatus.PUBLISHED: {ProtocolStatus.DEPRECATED},
        ProtocolStatus.DEPRECATED: set(),
    }

    def __init__(self, protocol_service: ProtocolService) -> None:
        self.protocol_service = protocol_service

    def transition(self, protocol_id: str, actor: str, target: ProtocolStatus, reason: str) -> Protocol:
        protocol = self.protocol_service.get_protocol(protocol_id)
        if protocol is None:
            raise KeyError(f"Protocolo nao encontrado: {protocol_id}")
        if target not in self._allowed.get(protocol.metadata.status, set()):
            raise ValueError(
                f"Transicao invalida: {protocol.metadata.status.value} -> {target.value}"
            )
        return self.protocol_service.set_status(
            protocol_id=protocol_id,
            target_status=target,
            actor=actor,
            changelog=reason,
        )

