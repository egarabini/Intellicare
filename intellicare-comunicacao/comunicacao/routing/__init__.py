"""Nucleo de roteamento de comunicacao."""

from comunicacao.routing.lgpd import DefaultLGPDGateway, LGPDComplianceGateway, LGPDDecision
from comunicacao.routing.lgpd_adapter import LGPDComplianceAdapter

__all__ = [
    "DefaultLGPDGateway",
    "LGPDComplianceGateway",
    "LGPDDecision",
    "LGPDComplianceAdapter",
]
