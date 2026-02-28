"""Patient Compartment FHIR R4 — define quais recursos pertencem ao compartimento de um paciente."""

from typing import Final

# Recursos que pertencem ao Patient Compartment com seus campos de referência
PATIENT_COMPARTMENT: Final[dict[str, list[str]]] = {
    "AllergyIntolerance": ["patient"],
    "CarePlan": ["patient", "subject"],
    "CareTeam": ["patient", "subject"],
    "Condition": ["patient", "subject"],
    "DiagnosticReport": ["subject", "patient"],
    "DocumentReference": ["subject", "patient"],
    "Encounter": ["patient", "subject"],
    "Goal": ["patient", "subject"],
    "Immunization": ["patient"],
    "MedicationAdministration": ["patient", "subject"],
    "MedicationRequest": ["patient", "subject"],
    "Observation": ["patient", "subject"],
    "Procedure": ["patient", "subject"],
    "ServiceRequest": ["patient", "subject"],
    "RiskAssessment": ["patient", "subject"],
    "NutritionOrder": ["patient"],
    "Coverage": ["beneficiary"],
    "Appointment": ["participant"],
    "Communication": ["patient", "subject"],
    "Flag": ["patient", "subject"],
}

# Tipos de referências a resolver recursivamente (enriquecimento do Bundle)
RESOLVE_REFERENCE_TYPES: Final[list[str]] = [
    "Organization",
    "Location",
    "Practitioner",
    "PractitionerRole",
    "Medication",
    "Device",
    "RelatedPerson",
    "Specimen",
]


def get_patient_ref(patient_id: str) -> str:
    """Normaliza o ID para referência FHIR padrão `Patient/{id}`."""
    if patient_id.startswith("Patient/"):
        return patient_id
    return f"Patient/{patient_id}"


def extract_references(resource: dict) -> list[str]:
    """Extrai todas as referências de um recurso FHIR (recursivo em dicts/lists)."""
    refs: list[str] = []

    def _walk(obj):
        if isinstance(obj, dict):
            if "reference" in obj and isinstance(obj["reference"], str):
                refs.append(obj["reference"])
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(resource)
    return refs


def resource_belongs_to_patient(resource: dict, patient_ref: str) -> bool:
    """Verifica se um recurso pertence ao compartimento do paciente."""
    resource_type = resource.get("resourceType", "")
    ref_fields = PATIENT_COMPARTMENT.get(resource_type, [])

    for field in ref_fields:
        field_val = resource.get(field)
        if isinstance(field_val, dict):
            if field_val.get("reference") == patient_ref:
                return True
        elif isinstance(field_val, list):
            for item in field_val:
                if isinstance(item, dict) and item.get("reference") == patient_ref:
                    return True

    return False
