"""
============================================================================
NISE TRAINING MODULE - OPENAPI CONFIGURATION
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: OpenAPI/Swagger Configuration
Versão: 1.0
Data: 24/03/2026
Responsável: DEV1
============================================================================
"""

from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

# ============================================================================
# OPENAPI METADATA
# ============================================================================

OPENAPI_TAGS = [
    {
        "name": "Metadata",
        "description": "FHIR server metadata and capability statement",
    },
    {
        "name": "Patients",
        "description": "Patient resource operations (FHIR R4)",
        "externalDocs": {
            "description": "FHIR Patient Resource",
            "url": "http://hl7.org/fhir/R4/patient.html",
        },
    },
    {
        "name": "Observations",
        "description": "Observation resource operations (FHIR R4)",
        "externalDocs": {
            "description": "FHIR Observation Resource",
            "url": "http://hl7.org/fhir/R4/observation.html",
        },
    },
    {
        "name": "Practitioners",
        "description": "Practitioner resource operations (FHIR R4)",
        "externalDocs": {
            "description": "FHIR Practitioner Resource",
            "url": "http://hl7.org/fhir/R4/practitioner.html",
        },
    },
    {
        "name": "Encounters",
        "description": "Encounter resource operations (FHIR R4)",
        "externalDocs": {
            "description": "FHIR Encounter Resource",
            "url": "http://hl7.org/fhir/R4/encounter.html",
        },
    },
    {
        "name": "Florence",
        "description": "Florence AI Assistant (Dr. Nise chatbot)",
    },
]

# ============================================================================
# OPENAPI EXAMPLES
# ============================================================================

PATIENT_EXAMPLE = {
    "resourceType": "Patient",
    "id": "example-patient-001",
    "identifier": [
        {
            "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
            "value": "12345678901"
        },
        {
            "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns",
            "value": "123456789012345"
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Silva",
            "given": ["João", "Pedro"]
        }
    ],
    "gender": "male",
    "birthDate": "1980-01-15",
    "address": [
        {
            "use": "home",
            "city": "São Paulo",
            "state": "SP",
            "postalCode": "01310-100",
            "country": "BR"
        }
    ]
}

OBSERVATION_EXAMPLE = {
    "resourceType": "Observation",
    "id": "example-obs-001",
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory",
                    "display": "Laboratory"
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "2339-0",
                "display": "Glucose [Mass/volume] in Blood"
            }
        ]
    },
    "subject": {
        "reference": "Patient/example-patient-001"
    },
    "effectiveDateTime": "2026-03-24T10:00:00Z",
    "valueQuantity": {
        "value": 95,
        "unit": "mg/dL",
        "system": "http://unitsofmeasure.org",
        "code": "mg/dL"
    }
}

PRACTITIONER_EXAMPLE = {
    "resourceType": "Practitioner",
    "id": "example-pract-001",
    "identifier": [
        {
            "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
            "value": "CRM-SP-123456"
        }
    ],
    "name": [
        {
            "use": "official",
            "family": "Santos",
            "given": ["Maria", "Clara"],
            "prefix": ["Dra."]
        }
    ],
    "qualification": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                        "code": "MD",
                        "display": "Cardiologia"
                    }
                ]
            }
        }
    ]
}

ENCOUNTER_EXAMPLE = {
    "resourceType": "Encounter",
    "id": "example-enc-001",
    "status": "finished",
    "class": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory"
    },
    "subject": {
        "reference": "Patient/example-patient-001"
    },
    "period": {
        "start": "2026-03-24T09:00:00Z",
        "end": "2026-03-24T10:00:00Z"
    }
}

# ============================================================================
# CUSTOM OPENAPI SCHEMA
# ============================================================================

def custom_openapi(app) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with FHIR examples.
    
    Args:
        app: FastAPI application instance
    
    Returns:
        dict: Custom OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="NISE Training Module API",
        version="1.0.0",
        description="""
# NISE - Treinamento Assistido com FHIR R4

API RESTful para treinamento de profissionais de saúde com recursos FHIR R4.

## Recursos Implementados

- **Patient**: Gerenciamento de pacientes
- **Observation**: Resultados de exames e sinais vitais
- **Practitioner**: Profissionais de saúde
- **Encounter**: Atendimentos e consultas

## Conformidade FHIR R4

Esta API segue o padrão FHIR R4 (Fast Healthcare Interoperability Resources).
Todos os recursos são validados usando a biblioteca `fhir.resources`.

## Autenticação

Atualmente em desenvolvimento. Autenticação será implementada na Fase 2.

## Performance

- Target: P99 < 100ms
- Queries assíncronas
- Paginação eficiente

## Suporte

- Documentação: http://localhost:8000/docs
- Repositório: https://github.com/intellicare/nise
        """,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

