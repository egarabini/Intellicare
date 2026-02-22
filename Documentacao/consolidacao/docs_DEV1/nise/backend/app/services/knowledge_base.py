"""
============================================================================
NISE TRAINING MODULE - KNOWLEDGE BASE SERVICE
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: Knowledge Base Management for RAG
Versão: 1.0
Data: 25/03/2026
Responsável: DEV1
============================================================================
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import logging
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# FHIR R4 KNOWLEDGE BASE
# ============================================================================

FHIR_KNOWLEDGE_BASE = {
    "Patient": {
        "description": "Recurso FHIR R4 para representar informações demográficas e administrativas de pacientes.",
        "required_fields": ["resourceType", "name"],
        "optional_fields": ["identifier", "gender", "birthDate", "address", "telecom", "contact"],
        "identifiers": {
            "CPF": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
            "CNS": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cns"
        },
        "example": {
            "resourceType": "Patient",
            "id": "example-001",
            "identifier": [
                {
                    "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/cpf",
                    "value": "12345678901"
                }
            ],
            "name": [{"family": "Silva", "given": ["João"]}],
            "gender": "male",
            "birthDate": "1980-01-15"
        },
        "validation_rules": [
            "CPF deve ter 11 dígitos",
            "CNS deve ter 15 dígitos",
            "birthDate deve estar no formato YYYY-MM-DD",
            "gender deve ser: male, female, other, unknown"
        ]
    },
    "Observation": {
        "description": "Recurso FHIR R4 para representar medições, resultados de exames e sinais vitais.",
        "required_fields": ["resourceType", "status", "code", "subject"],
        "optional_fields": ["category", "effectiveDateTime", "valueQuantity", "interpretation"],
        "status_values": ["registered", "preliminary", "final", "amended", "corrected", "cancelled"],
        "common_loinc_codes": {
            "2339-0": "Glucose [Mass/volume] in Blood",
            "8480-6": "Systolic blood pressure",
            "8462-4": "Diastolic blood pressure",
            "8867-4": "Heart rate",
            "9279-1": "Respiratory rate",
            "8310-5": "Body temperature",
            "29463-7": "Body weight",
            "8302-2": "Body height",
            "39156-5": "Body mass index (BMI)"
        },
        "example": {
            "resourceType": "Observation",
            "id": "example-001",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "laboratory"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "2339-0",
                    "display": "Glucose [Mass/volume] in Blood"
                }]
            },
            "subject": {"reference": "Patient/example-001"},
            "effectiveDateTime": "2026-03-25T10:00:00Z",
            "valueQuantity": {
                "value": 95,
                "unit": "mg/dL",
                "system": "http://unitsofmeasure.org",
                "code": "mg/dL"
            }
        },
        "reference_ranges": {
            "2339-0": {"min": 70, "max": 100, "unit": "mg/dL", "description": "Glicemia em jejum normal"},
            "8480-6": {"min": 90, "max": 120, "unit": "mmHg", "description": "Pressão sistólica normal"},
            "8462-4": {"min": 60, "max": 80, "unit": "mmHg", "description": "Pressão diastólica normal"}
        }
    },
    "Practitioner": {
        "description": "Recurso FHIR R4 para representar profissionais de saúde.",
        "required_fields": ["resourceType", "name"],
        "optional_fields": ["identifier", "qualification", "telecom", "address"],
        "specialties": [
            "Cardiologia", "Endocrinologia", "Neurologia", "Pediatria",
            "Psiquiatria", "Ortopedia", "Dermatologia", "Oftalmologia",
            "Ginecologia", "Clínica Geral"
        ],
        "example": {
            "resourceType": "Practitioner",
            "id": "example-001",
            "identifier": [{
                "system": "http://rnds.saude.gov.br/fhir/r4/NamingSystem/crm",
                "value": "CRM-SP-123456"
            }],
            "name": [{"family": "Santos", "given": ["Maria"], "prefix": ["Dra."]}],
            "qualification": [{
                "code": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                        "code": "MD",
                        "display": "Cardiologia"
                    }]
                }
            }]
        }
    },
    "Encounter": {
        "description": "Recurso FHIR R4 para representar atendimentos e consultas.",
        "required_fields": ["resourceType", "status", "class", "subject"],
        "optional_fields": ["period", "participant", "reasonCode", "diagnosis"],
        "status_values": ["planned", "arrived", "triaged", "in-progress", "onleave", "finished", "cancelled"],
        "class_codes": {
            "AMB": "ambulatory - Atendimento ambulatorial",
            "EMER": "emergency - Emergência",
            "HH": "home health - Atendimento domiciliar",
            "IMP": "inpatient encounter - Internação",
            "ACUTE": "inpatient acute - Internação aguda"
        },
        "example": {
            "resourceType": "Encounter",
            "id": "example-001",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            },
            "subject": {"reference": "Patient/example-001"},
            "period": {
                "start": "2026-03-25T09:00:00Z",
                "end": "2026-03-25T10:00:00Z"
            }
        }
    }
}

# ============================================================================
# CLINICAL SCENARIOS
# ============================================================================

CLINICAL_SCENARIOS = {
    "diabetes_monitoring": {
        "title": "Monitoramento de Diabetes",
        "description": "Cenário de acompanhamento de paciente diabético",
        "resources_needed": ["Patient", "Observation", "Practitioner", "Encounter"],
        "observations": ["2339-0"],  # Glicemia
        "workflow": [
            "1. Criar Patient com dados demográficos",
            "2. Criar Practitioner (endocrinologista)",
            "3. Criar Encounter (consulta ambulatorial)",
            "4. Criar Observation (glicemia em jejum)",
            "5. Avaliar resultado e conduta"
        ]
    },
    "hypertension_control": {
        "title": "Controle de Hipertensão",
        "description": "Cenário de monitoramento de pressão arterial",
        "resources_needed": ["Patient", "Observation", "Practitioner", "Encounter"],
        "observations": ["8480-6", "8462-4"],  # PA sistólica e diastólica
        "workflow": [
            "1. Criar Patient",
            "2. Criar Practitioner (cardiologista)",
            "3. Criar Encounter",
            "4. Criar Observations (PA sistólica e diastólica)",
            "5. Avaliar controle pressórico"
        ]
    }
}

# ============================================================================
# SERVICE FUNCTIONS
# ============================================================================

async def get_resource_documentation(resource_type: str) -> Optional[Dict[str, Any]]:
    """Get documentation for a FHIR resource type."""
    return FHIR_KNOWLEDGE_BASE.get(resource_type)


async def get_loinc_code_info(loinc_code: str) -> Optional[Dict[str, Any]]:
    """Get information about a LOINC code."""
    obs_info = FHIR_KNOWLEDGE_BASE.get("Observation", {})
    loinc_codes = obs_info.get("common_loinc_codes", {})
    
    if loinc_code in loinc_codes:
        return {
            "code": loinc_code,
            "display": loinc_codes[loinc_code],
            "reference_range": obs_info.get("reference_ranges", {}).get(loinc_code)
        }
    return None


async def get_clinical_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    """Get a clinical scenario by ID."""
    return CLINICAL_SCENARIOS.get(scenario_id)


async def search_knowledge_base(query: str) -> List[Dict[str, Any]]:
    """Search knowledge base for relevant information."""
    results = []
    query_lower = query.lower()
    
    # Search in FHIR resources
    for resource_type, info in FHIR_KNOWLEDGE_BASE.items():
        if resource_type.lower() in query_lower or query_lower in info.get("description", "").lower():
            results.append({
                "type": "fhir_resource",
                "resource_type": resource_type,
                "info": info
            })
    
    # Search in clinical scenarios
    for scenario_id, scenario in CLINICAL_SCENARIOS.items():
        if query_lower in scenario.get("title", "").lower() or query_lower in scenario.get("description", "").lower():
            results.append({
                "type": "clinical_scenario",
                "scenario_id": scenario_id,
                "info": scenario
            })
    
    return results

