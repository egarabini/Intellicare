"""Build FHIR AuditEvent dicts for subscription notification attempts.

Pure Python — no SQLAlchemy in core. The caller persists the returned dict
as a FHIRResource or SubscriptionAudit ORM row.
"""

from __future__ import annotations

from .models import AuditRecord

_OUTCOME_SUCCESS = "0"
_OUTCOME_FAILURE = "8"


def build_audit_event(record: AuditRecord) -> dict:
    """Return a FHIR R4 AuditEvent dict for one subscription notification attempt."""
    outcome = (
        _OUTCOME_SUCCESS
        if record.event_type in ("matched", "dispatched")
        else _OUTCOME_FAILURE
    )
    return {
        "resourceType": "AuditEvent",
        "id": record.id,
        "type": {
            "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
            "code": "rest",
            "display": "RESTful Operation",
        },
        "subtype": [
            {
                "system": "http://hl7.org/fhir/restful-interaction",
                "code": "subscription-notification",
                "display": "Subscription Notification",
            }
        ],
        "action": "E",
        "recorded": record.timestamp.isoformat() + "Z",
        "outcome": outcome,
        "outcomeDesc": record.error or "success",
        "agent": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                            "code": "AUT",
                        }
                    ]
                },
                "who": {"display": "IntelliCare Subscription Engine"},
                "requestor": True,
            }
        ],
        "source": {
            "observer": {"display": "intellicare-grahame"},
            "type": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/security-source-type",
                    "code": "4",
                    "display": "Application Server",
                }
            ],
        },
        "entity": [
            {
                "what": {
                    "identifier": {
                        "system": "urn:intellicare:subscription",
                        "value": record.subscription_id,
                    }
                },
                "type": {
                    "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                    "code": "2",
                    "display": "System Object",
                },
                "role": {
                    "system": "http://terminology.hl7.org/CodeSystem/object-role",
                    "code": "20",
                    "display": "Job",
                },
                "name": f"{record.resource_type}/{record.resource_id}",
                "detail": [
                    {"type": "channel", "valueString": record.channel_type or "unknown"},
                    {"type": "event", "valueString": record.event_type},
                    *[
                        {"type": k, "valueString": str(v)}
                        for k, v in (record.details or {}).items()
                    ],
                ],
            }
        ],
        "extension": [
            {
                "url": "urn:intellicare:extension:tenant",
                "valueString": record.tenant_id,
            }
        ],
    }
