"""Gateway de conformidade LGPD para o engine de roteamento."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from comunicacao.dispatchers.base import ResolvedRecipient
    from comunicacao.routing.models import CommunicationIntentRecord


@dataclass(slots=True)
class LGPDDecision:
    """Decisao de permissao para envio por canal."""

    allowed: bool
    legal_basis: str | None
    reason: str
    override_applied: bool = False
    defer_until: datetime | None = None


class LGPDComplianceGateway(Protocol):
    """Contrato para consulta de elegibilidade LGPD por envio."""

    async def can_send(
        self,
        patient_id: str,
        channel: str,
        intent_type: str,
        severity: str,
    ) -> LGPDDecision: ...

    async def check_compliance(
        self,
        intent: CommunicationIntentRecord,
        resolved_recipient: ResolvedRecipient,
    ) -> bool:
        """
        Verifica conformidade LGPD para a intent.

        Retorna True se permitido, False caso contrário.
        """
        ...


class DefaultLGPDGateway:
    """Implementacao provisoria de D1 ate D6 fornecer a regra completa."""

    async def can_send(
        self,
        patient_id: str,
        channel: str,
        intent_type: str,
        severity: str,
    ) -> LGPDDecision:
        _ = patient_id
        normalized_severity = severity.strip().lower()
        normalized_type = intent_type.strip().lower()

        if normalized_severity == "critical":
            return LGPDDecision(
                allowed=True,
                legal_basis="lgpd_art_7_vii",
                reason=f"critico permitido no canal {channel}",
                override_applied=True,
            )

        if normalized_severity == "high" and normalized_type in {"clinical_alert", "escalation"}:
            return LGPDDecision(
                allowed=True,
                legal_basis="lgpd_art_7_vii",
                reason=f"urgente clinico permitido no canal {channel}",
                override_applied=True,
            )

        return LGPDDecision(
            allowed=True,
            legal_basis=None,
            reason="gateway padrao d1 permite envio",
            override_applied=False,
        )

    async def check_compliance(
        self,
        intent: CommunicationIntentRecord,
        resolved_recipient: ResolvedRecipient,
    ) -> bool:
        """
        Verifica conformidade LGPD para a intent.

        Implementação padrão: permite CRITICAL e HIGH, demais requerem consentimento.
        """
        _ = resolved_recipient  # Não usado na implementação padrão

        normalized_severity = intent.severity.strip().lower()
        normalized_category = intent.category.strip().lower()

        # CRITICAL sempre permitido (interesse vital)
        if normalized_severity == "critical":
            return True

        # HIGH permitido para alertas clínicos e escalonamentos
        if normalized_severity == "high" and normalized_category in {"clinical_alert", "escalation"}:
            return True

        # Demais casos: permitido por padrão (D6 implementará regras completas)
        return True

