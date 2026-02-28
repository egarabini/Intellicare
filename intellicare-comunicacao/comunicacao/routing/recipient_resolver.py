"""Resolução de destinatários com adaptadores plugáveis (R6)."""

from __future__ import annotations

import logging
from typing import Protocol

from comunicacao.dispatchers.base import ResolvedRecipient
from comunicacao.routing.models import RecipientType

logger = logging.getLogger(__name__)


class RecipientAdapter(Protocol):
    """
    Interface para adaptadores de resolução de destinatários.
    
    Cada tipo de destinatário (professional, patient, team, etc) pode ter
    seu próprio adaptador que sabe como resolver os dados específicos.
    """

    async def resolve(self, recipient_id: str) -> ResolvedRecipient:
        """Resolve destinatário para dados de contato."""
        ...


class DefaultRecipientAdapter:
    """Adaptador padrão que retorna dados básicos."""

    async def resolve(self, recipient_id: str) -> ResolvedRecipient:
        """Retorna destinatário com dados mínimos."""
        return ResolvedRecipient(
            recipient_id=recipient_id,
            recipient_type="unknown",
            channels={},
        )


class ProfessionalAdapter:
    """Adaptador para profissionais de saúde."""

    def __init__(self, professional_service=None) -> None:
        self.professional_service = professional_service

    async def resolve(self, recipient_id: str) -> ResolvedRecipient:
        """
        Resolve profissional para dados de contato.
        
        TODO: Integrar com módulo de profissionais quando disponível.
        """
        # Placeholder - será integrado com módulo de profissionais
        logger.info("ProfessionalAdapter: resolvendo profissional %s", recipient_id)
        
        return ResolvedRecipient(
            recipient_id=recipient_id,
            recipient_type="professional",
            channels={
                "email": f"{recipient_id}@hospital.com",
                "rocketchat": f"@{recipient_id}",
            },
        )


class PatientAdapter:
    """Adaptador para pacientes."""

    def __init__(self, patient_service=None, room_repository=None) -> None:
        self.patient_service = patient_service
        self.room_repository = room_repository

    async def resolve(self, recipient_id: str) -> ResolvedRecipient:
        """
        Resolve paciente para dados de contato.
        
        TODO: Integrar com módulo de pacientes quando disponível.
        """
        # Placeholder - será integrado com módulo de pacientes
        logger.info("PatientAdapter: resolvendo paciente %s", recipient_id)
        
        channels = {
            "sms": f"+55119{recipient_id[-8:]}",
            "whatsapp": f"+55119{recipient_id[-8:]}",
        }
        if self.room_repository is not None:
            room_id = self.room_repository.get_room_id(recipient_id)
            if room_id:
                channels["rocketchat"] = room_id
        else:
            channels["rocketchat"] = f"@{recipient_id}"

        return ResolvedRecipient(
            recipient_id=recipient_id,
            recipient_type="patient",
            channels=channels,
        )


class TeamAdapter:
    """Adaptador para equipes/grupos."""

    def __init__(self, team_service=None) -> None:
        self.team_service = team_service

    async def resolve(self, recipient_id: str) -> ResolvedRecipient:
        """
        Resolve equipe para lista de membros.
        
        TODO: Integrar com módulo de equipes quando disponível.
        """
        # Placeholder - será integrado com módulo de equipes
        logger.info("TeamAdapter: resolvendo equipe %s", recipient_id)
        
        return ResolvedRecipient(
            recipient_id=recipient_id,
            recipient_type="team",
            channels={
                "rocketchat": f"#team-{recipient_id}",
            },
        )


class RecipientResolver:
    """
    Resolvedor de destinatários com adaptadores plugáveis (R6).
    
    Permite registrar adaptadores customizados para cada tipo de destinatário.
    """

    def __init__(self, room_repository=None) -> None:
        self._adapters: dict[RecipientType, RecipientAdapter] = {}
        self._default_adapter = DefaultRecipientAdapter()
        
        # Registra adaptadores padrão
        self.register_adapter(RecipientType.PROFESSIONAL, ProfessionalAdapter())
        self.register_adapter(RecipientType.PATIENT, PatientAdapter(room_repository=room_repository))
        self.register_adapter(RecipientType.TEAM, TeamAdapter())

    def register_adapter(self, recipient_type: RecipientType, adapter: RecipientAdapter) -> None:
        """Registra adaptador para um tipo de destinatário."""
        self._adapters[recipient_type] = adapter
        logger.info("RecipientResolver: adaptador registrado para %s", recipient_type.value)

    async def resolve(self, recipient_type: RecipientType, recipient_id: str) -> ResolvedRecipient:
        """
        Resolve destinatário usando adaptador apropriado.
        
        Se não houver adaptador registrado, usa o adaptador padrão.
        """
        adapter = self._adapters.get(recipient_type, self._default_adapter)
        
        logger.info(
            "RecipientResolver: resolvendo %s (type=%s) com %s",
            recipient_id,
            recipient_type.value,
            adapter.__class__.__name__,
        )
        
        resolved = await adapter.resolve(recipient_id)
        
        logger.info(
            "RecipientResolver: %s resolvido com %d canais",
            recipient_id,
            len(resolved.channels),
        )
        
        return resolved
