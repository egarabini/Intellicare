"""Rotas SMART-on-FHIR no Grahame.

Expõe no FHIR server:
    GET  /api/v1/metadata                         → CapabilityStatement com extensões SMART
    GET  /api/v1/.well-known/smart-configuration  → SmartConfiguration (proxy para intellicare_auth)

Referência:
    https://hl7.org/fhir/smart-app-launch/app-launch.html
    https://hl7.org/fhir/R4/capabilitystatement.html
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter

from grahame.config import config

router = APIRouter(tags=["SMART-on-FHIR"])

# ── Helpers ───────────────────────────────────────────────────────────────────

def _smart_urls() -> dict[str, str]:
    keycloak_base = os.getenv("KEYCLOAK_BASE_URL", "https://keycloak.example.com")
    realm = os.getenv("KEYCLOAK_REALM", "intellicare")
    base = f"{keycloak_base}/realms/{realm}"
    return {
        "authorize": f"{base}/protocol/openid-connect/auth",
        "token":     f"{base}/protocol/openid-connect/token",
        "jwks":      f"{base}/protocol/openid-connect/certs",
        "introspect": f"{base}/protocol/openid-connect/token/introspect",
    }


def _fhir_base_url() -> str:
    return os.getenv("FHIR_BASE_URL", "https://grahame.example.com")


# ── /.well-known/smart-configuration ─────────────────────────────────────────


@router.get(
    "/.well-known/smart-configuration",
    tags=["SMART-on-FHIR"],
    summary="SMART App Launch — configuração pública",
)
async def smart_configuration() -> dict[str, Any]:
    """Retorna configuração SMART-on-FHIR conforme HL7 STU2.

    Este endpoint é exigido pelo SMART App Launch Framework para que
    aplicações de terceiros descubram os endpoints de autorização.
    """
    urls = _smart_urls()
    fhir_base = _fhir_base_url()

    return {
        "issuer": fhir_base,
        "jwks_uri": urls["jwks"],
        "authorization_endpoint": urls["authorize"],
        "token_endpoint": urls["token"],
        "introspection_endpoint": urls["introspect"],
        "token_endpoint_auth_methods_supported": [
            "private_key_jwt",
            "client_secret_basic",
        ],
        "grant_types_supported": [
            "authorization_code",
            "client_credentials",
        ],
        "scopes_supported": [
            "openid", "fhirUser",
            "launch", "launch/patient", "launch/encounter",
            "patient/*.read", "patient/*.write", "patient/*.*",
            "user/*.read", "user/*.write", "user/*.*",
            "system/*.read", "system/*.write", "system/*.*",
            "offline_access",
        ],
        "response_types_supported": ["code"],
        "capabilities": [
            "launch-ehr",
            "launch-standalone",
            "client-public",
            "client-confidential-symmetric",
            "sso-openid-connect",
            "context-passthrough-banner",
            "context-ehr-patient",
            "context-ehr-encounter",
            "context-standalone-patient",
            "permission-offline",
            "permission-patient",
            "permission-user",
            "permission-v2",
        ],
        "code_challenge_methods_supported": ["S256"],
    }


# ── /metadata (CapabilityStatement) ──────────────────────────────────────────

_SUPPORTED_RESOURCES = [
    ("Patient",            ["search-type", "read", "create", "update", "delete", "history-instance"]),
    ("Observation",        ["search-type", "read", "create", "update", "delete"]),
    ("Condition",          ["search-type", "read", "create", "update", "delete"]),
    ("Encounter",          ["search-type", "read", "create", "update", "delete"]),
    ("MedicationRequest",  ["search-type", "read", "create", "update", "delete"]),
    ("DiagnosticReport",   ["search-type", "read", "create", "update"]),
    ("AllergyIntolerance", ["search-type", "read", "create", "update"]),
    ("Procedure",          ["search-type", "read", "create"]),
    ("Immunization",       ["search-type", "read", "create"]),
    ("CarePlan",           ["search-type", "read", "create", "update"]),
    ("Organization",       ["search-type", "read", "create", "update"]),
    ("Practitioner",       ["search-type", "read", "create", "update"]),
]


@router.get(
    "/metadata",
    tags=["SMART-on-FHIR"],
    summary="CapabilityStatement FHIR R4 com extensões SMART",
)
async def capability_statement() -> dict[str, Any]:
    """Retorna CapabilityStatement FHIR R4 com extensões SMART security.

    Conforme HL7 FHIR R4 spec + SMART App Launch 2.0.
    Apps de terceiros consultam este endpoint via `iss` discovery.
    """
    urls = _smart_urls()
    fhir_base = _fhir_base_url()

    resource_entries = [
        {
            "type": rtype,
            "interaction": [{"code": i} for i in interactions],
            "versioning": "versioned",
            "readHistory": True,
        }
        for rtype, interactions in _SUPPORTED_RESOURCES
    ]

    return {
        "resourceType": "CapabilityStatement",
        "id": "grahame-capability",
        "url": f"{fhir_base}/metadata",
        "version": config.module_version,
        "name": "IntelliCareGrahameCapabilityStatement",
        "title": "IntelliCare Grahame — CapabilityStatement FHIR R4",
        "status": "active",
        "experimental": False,
        "description": "FHIR R4 CDR com suporte SMART-on-FHIR App Launch v2.0",
        "kind": "instance",
        "software": {
            "name": "IntelliCare Grahame",
            "version": config.module_version,
        },
        "implementation": {
            "description": "IntelliCare FHIR R4 CDR — Grahame",
            "url": fhir_base,
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "security": {
                    "cors": True,
                    "service": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/restful-security-service",
                                    "code": "SMART-on-FHIR",
                                    "display": "SMART-on-FHIR",
                                }
                            ],
                            "text": "OAuth2 with SMART-on-FHIR",
                        }
                    ],
                    # SMART security extensions (required by SMART app launch)
                    "extension": [
                        {
                            "url": "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris",
                            "extension": [
                                {"url": "authorize", "valueUri": urls["authorize"]},
                                {"url": "token",     "valueUri": urls["token"]},
                                {"url": "introspect","valueUri": urls["introspect"]},
                                {"url": "jwks",      "valueUri": urls["jwks"]},
                            ],
                        }
                    ],
                },
                "resource": resource_entries,
                "interaction": [
                    {"code": "transaction"},
                    {"code": "batch"},
                ],
                "operation": [
                    {"name": "everything", "definition": "http://hl7.org/fhir/OperationDefinition/Patient-everything"},
                    {"name": "summary",    "definition": "http://hl7.org/fhir/OperationDefinition/Patient-summary"},
                    {"name": "validate",   "definition": "http://hl7.org/fhir/OperationDefinition/Resource-validate"},
                ],
            }
        ],
    }
