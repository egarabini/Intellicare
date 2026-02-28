"""Builder de FHIR Communication para exportação."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from comunicacao.audit.models import AuditEntry


class FHIRCommunicationBuilder:
    """
    Builder de FHIR Communication R4.
    
    Converte AuditEntry para FHIR Communication para interoperabilidade.
    """
    
    @staticmethod
    def build_from_audit(entry: AuditEntry) -> Dict[str, Any]:
        """
        Constrói FHIR Communication a partir de AuditEntry.
        
        Args:
            entry: AuditEntry
        
        Returns:
            Dict com FHIR Communication R4
        """
        # Status mapping
        status_map = {
            "sent": "completed",
            "failed": "not-done",
            "queued": "preparation",
            "skipped": "stopped",
            "blocked_lgpd": "stopped",
            "deferred": "on-hold",
        }
        
        fhir_status = status_map.get(entry.status, "unknown")
        
        # Priority mapping
        priority_map = {
            "critical": "urgent",
            "high": "urgent",
            "medium": "routine",
            "low": "routine",
        }
        
        fhir_priority = priority_map.get(entry.severity.lower(), "routine")
        
        # Build FHIR Communication
        communication = {
            "resourceType": "Communication",
            "id": str(entry.id),
            "meta": {
                "versionId": "1",
                "lastUpdated": entry.created_at.isoformat(),
                "source": "intellicare-comunicacao",
                "profile": [
                    "http://hl7.org/fhir/StructureDefinition/Communication"
                ],
            },
            "identifier": [
                {
                    "system": "http://intellicare.gsi.srv.br/fhir/communication",
                    "value": str(entry.id),
                }
            ],
            "status": fhir_status,
            "priority": fhir_priority,
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/communication-category",
                            "code": "notification",
                            "display": "Notification",
                        }
                    ],
                    "text": entry.intent_type,
                }
            ],
            "medium": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
                            "code": FHIRCommunicationBuilder._map_channel_to_fhir(entry.channel),
                            "display": entry.channel,
                        }
                    ],
                    "text": entry.channel,
                }
            ],
            "sent": entry.created_at.isoformat(),
            "received": entry.created_at.isoformat(),
            "recipient": [
                {
                    "type": "Patient" if entry.recipient_type == "patient" else "Practitioner",
                    "identifier": {
                        "system": "http://intellicare.gsi.srv.br/fhir/patient-hash",
                        "value": entry.recipient_hash or "unknown",
                    },
                }
            ],
            "sender": {
                "type": "Organization",
                "identifier": {
                    "system": "http://intellicare.gsi.srv.br/fhir/module",
                    "value": entry.source_module or "unknown",
                },
            },
            "reasonCode": [
                {
                    "coding": [
                        {
                            "system": "http://intellicare.gsi.srv.br/fhir/severity",
                            "code": entry.severity,
                            "display": entry.severity.upper(),
                        }
                    ],
                    "text": entry.lgpd_reason or "Comunicação clínica",
                }
            ],
            "note": [],
        }
        
        # Adicionar nota com informações LGPD
        if entry.legal_basis:
            communication["note"].append({
                "text": f"Base legal: {entry.legal_basis}. {entry.lgpd_reason or ''}",
                "time": entry.created_at.isoformat(),
            })
        
        # Adicionar nota com erro (se houver)
        if entry.error_message:
            communication["note"].append({
                "text": f"Erro: {entry.error_message}",
                "time": entry.created_at.isoformat(),
            })
        
        return communication
    
    @staticmethod
    def _map_channel_to_fhir(channel: str) -> str:
        """Mapeia canal IntelliCare para código FHIR."""
        channel_map = {
            "email": "WRITTEN",
            "sms": "SMSWRIT",
            "whatsapp": "SMSWRIT",
            "rocketchat": "WRITTEN",
            "push": "ELECTRONIC",
            "jitsi": "VIDEOCONF",
        }
        return channel_map.get(channel, "ELECTRONIC")

