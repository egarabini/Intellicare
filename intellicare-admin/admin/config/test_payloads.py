from typing import Any

DEFAULT_TEST_PAYLOADS: dict[str, dict[str, Any]] = {
    "florence": {
        "query": "protocolo hipertensão arterial",
        "tenant_id": "test",
    },
    "oswaldo": {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "name": [{"given": ["João"], "family": "Silva"}],
                    "gender": "male",
                    "birthDate": "1959-01-01",
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10", "display": "Hipertensão"}]}
                }
            }
        ]
    },
    "donabedian": {
        "tenant_id": "test",
        "period": "2026-01"
    },
    "wanda": {
        "query": "resumo paciente",
        "patient_id": "test-001"
    },
    "comunicacao": {
        "channel": "test",
        "dry_run": True,
        "to": "test@test.com"
    },
    "geralda": {
        "action": "get_support_options",
        "tenant_id": "test"
    },
    "zilda": {
        "query": "CNES 0000001"
    },
    "minerva": {
        "document_url": "https://example.com/test.pdf",
        "dry_run": True
    },
    "pierre": {
        "query": "hypertension treatment 2025",
        "max_results": 1
    },
    "grahame": {
        "resource_type": "Patient",
        "action": "validate",
        "resource": {"resourceType": "Patient"}
    },
    "nise": {
        "message": "olá",
        "session_id": "test-session"
    }
}
