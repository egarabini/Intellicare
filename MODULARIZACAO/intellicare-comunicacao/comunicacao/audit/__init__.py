"""Módulo de auditoria e trilha imutável."""

from comunicacao.audit.audit_service import AuditTrailService
from comunicacao.audit.fhir_communication import FHIRCommunicationBuilder
from comunicacao.audit.hash_chain import HashChainManager
from comunicacao.audit.models import AuditEntry

__all__ = [
    "AuditTrailService",
    "HashChainManager",
    "AuditEntry",
    "FHIRCommunicationBuilder",
]

