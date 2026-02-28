"""IPS (International Patient Summary) — classificação de recursos em seções LOINC."""

from typing import Final

# Mapeamento de seções IPS com código LOINC
IPS_SECTIONS: Final[dict[str, dict]] = {
    "allergies":           {"code": "48765-2", "display": "Allergies and intolerances"},
    "immunizations":       {"code": "11369-6", "display": "Immunizations"},
    "medications":         {"code": "10160-0", "display": "History of medication use"},
    "problem_list":        {"code": "11450-4", "display": "Problem List"},
    "results":             {"code": "30954-2", "display": "Relevant Diagnostic Tests/Laboratory Data"},
    "vital_signs":         {"code": "8716-3",  "display": "Vital Signs"},
    "social_history":      {"code": "29762-2", "display": "Social History"},
    "procedures":          {"code": "47519-4", "display": "History of Procedures"},
    "encounters":          {"code": "46240-8", "display": "History of encounters"},
    "plan_of_treatment":   {"code": "18776-5", "display": "Plan of Treatment"},
    "goals":               {"code": "61146-7", "display": "Goals"},
    "health_concerns":     {"code": "75310-3", "display": "Health Concerns"},
    "functional_status":   {"code": "47420-5", "display": "Functional Status"},
    "notes":               {"code": "11488-4", "display": "Consult Note"},
    "assessments":         {"code": "51848-0", "display": "Assessment Note"},
    "reason_for_referral": {"code": "42349-1", "display": "Reason for Referral"},
    "insurance":           {"code": "48768-6", "display": "Payer"},
    "devices":             {"code": "46264-8", "display": "Medical Devices"},
}

# Mapeamento direto por resourceType → seção IPS
RESOURCE_TYPE_TO_SECTION: Final[dict[str, str]] = {
    "AllergyIntolerance": "allergies",
    "Immunization":       "immunizations",
    "MedicationRequest":  "medications",
    "Procedure":          "procedures",
    "Encounter":          "encounters",
    "CarePlan":           "plan_of_treatment",
    "Goal":               "goals",
    "Coverage":           "insurance",
    "Device":             "devices",
    "DocumentReference":  "notes",
    "DiagnosticReport":   "results",
    "RiskAssessment":     "assessments",
}

# Category codes de Observation LOINC
OBSERVATION_VITAL_SIGNS = "vital-signs"
OBSERVATION_SOCIAL_HISTORY = "social-history"
OBSERVATION_LAB = "laboratory"
LOINC_DISABILITY_CODE = "89572-3"  # Disability status LOINC


def _get_category_codes(obs: dict) -> list[str]:
    codes: list[str] = []
    for cat in obs.get("category", []):
        for coding in cat.get("coding", []):
            if coding.get("code"):
                codes.append(coding["code"])
    return codes


def classify_observation(obs: dict) -> str:
    """Classifica Observation por category code → seção IPS."""
    categories = _get_category_codes(obs)
    if OBSERVATION_VITAL_SIGNS in categories:
        return "vital_signs"
    if OBSERVATION_SOCIAL_HISTORY in categories:
        return "social_history"
    # Verificar se é functional status pelo código LOINC
    for coding in obs.get("code", {}).get("coding", []):
        if coding.get("code") == LOINC_DISABILITY_CODE:
            return "functional_status"
    return "results"


def classify_condition(cond: dict) -> str:
    """Classifica Condition: health-concern vs problem-list."""
    for cat in cond.get("category", []):
        for coding in cat.get("coding", []):
            if coding.get("code") == "health-concern":
                return "health_concerns"
    return "problem_list"


def classify_resource(resource: dict) -> str | None:
    """Classifica um recurso FHIR na seção IPS correspondente.

    Returns:
        Nome da seção IPS, ou None se o recurso não pertence ao IPS.
    """
    resource_type = resource.get("resourceType", "")

    if resource_type == "Observation":
        return classify_observation(resource)

    if resource_type == "Condition":
        return classify_condition(resource)

    return RESOURCE_TYPE_TO_SECTION.get(resource_type)


def build_ips_composition(
    patient: dict,
    sections_map: dict[str, list[dict]],
    author_ref: str | None = None,
    authored_on: str | None = None,
) -> dict:
    """Monta um recurso Composition FHIR para o IPS.

    Args:
        patient: Recurso Patient FHIR.
        sections_map: Dict de seção → lista de recursos.
        author_ref: Referência ao autor (ex: "Practitioner/123").
        authored_on: Data de criação (ISO 8601).

    Returns:
        Recurso Composition FHIR R4 (dict).
    """
    import uuid
    from datetime import datetime, timezone

    patient_id = patient.get("id", "unknown")
    patient_name = _extract_patient_name(patient)
    now_iso = authored_on or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    sections = []
    for section_key, resources in sections_map.items():
        if not resources:
            continue
        section_def = IPS_SECTIONS.get(section_key)
        if not section_def:
            continue

        entry_refs = [
            {"reference": f"{r['resourceType']}/{r['id']}"}
            for r in resources
            if r.get("id")
        ]

        sections.append({
            "title": section_def["display"],
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": section_def["code"],
                    "display": section_def["display"],
                }]
            },
            "text": {
                "status": "generated",
                "div": f"<div xmlns='http://www.w3.org/1999/xhtml'>{len(resources)} registro(s)</div>",
            },
            "entry": entry_refs,
        })

    composition = {
        "resourceType": "Composition",
        "id": str(uuid.uuid4()),
        "status": "final",
        "type": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "60591-5",
                "display": "Patient Summary Document",
            }]
        },
        "subject": {"reference": f"Patient/{patient_id}", "display": patient_name},
        "date": now_iso,
        "title": f"Patient Summary — {patient_name}",
        "confidentiality": "N",
        "section": sections,
    }

    if author_ref:
        composition["author"] = [{"reference": author_ref}]

    return composition


def _extract_patient_name(patient: dict) -> str:
    for name in patient.get("name", []):
        family = name.get("family", "")
        given = " ".join(name.get("given", []))
        if family or given:
            return f"{given} {family}".strip()
    return patient.get("id", "Unknown")
