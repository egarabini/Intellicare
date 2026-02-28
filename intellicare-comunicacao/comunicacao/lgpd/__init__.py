"""Módulo de conformidade LGPD e auditoria."""

from comunicacao.lgpd.config import LGPDConfig
from comunicacao.lgpd.models import (
    CommunicationPreference,
    ConsentLogEntry,
    LGPDDecision,
    LegalBasis,
)

__all__ = [
    "LGPDConfig",
    "CommunicationPreference",
    "ConsentLogEntry",
    "LGPDDecision",
    "LegalBasis",
]

