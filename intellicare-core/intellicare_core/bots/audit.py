"""Build FHIR AuditEvent dicts for bot executions."""

from __future__ import annotations

from .models import BotExecutionResult

_OUTCOME_SUCCESS = "0"
_OUTCOME_FAILURE = "8"


def build_bot_audit_event(result: BotExecutionResult, bot_name: str = "Unknown Bot") -> dict:
    """Return a FHIR R4 AuditEvent dict for one bot execution attempt."""
    outcome = _OUTCOME_SUCCESS if result.success else _OUTCOME_FAILURE
    return {
        "resourceType": "AuditEvent",
        "id": result.id,
        "type": {
            "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
            "code": "rest",
            "display": "RESTful Operation",
        },
        "subtype": [
            {
                "system": "urn:intellicare:event-type",
                "code": "bot-execution",
                "display": "Bot Execution",
            }
        ],
        "action": "E",
        "recorded": result.created_at.isoformat() + "Z",
        "outcome": outcome,
        "outcomeDesc": result.error_message or "success",
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
                "who": {
                    "display": f"Bot/{result.bot_id}",
                    "identifier": {
                        "system": "urn:intellicare:bot",
                        "value": result.bot_id,
                    },
                },
                "name": bot_name,
                "requestor": True,
            }
        ],
        "source": {
            "observer": {"display": "intellicare-bots-engine"},
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
                    "reference": f"{result.input_resource_type}/{result.input_resource_id}"
                    if result.input_resource_type
                    else None,
                },
                "type": {
                    "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                    "code": "2",
                    "display": "System Object",
                },
                "detail": [
                    {"type": "duration_ms", "valueString": str(round(result.duration_ms, 2))},
                    {"type": "interaction", "valueString": result.interaction},
                    {"type": "log", "valueString": result.log_output[:2000]},
                ],
            }
        ],
        "extension": [
            {"url": "urn:intellicare:extension:tenant", "valueString": result.tenant_id},
            {"url": "urn:intellicare:extension:bot-id", "valueString": result.bot_id},
        ],
    }
