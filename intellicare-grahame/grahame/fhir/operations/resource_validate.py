"""$validate — valida um recurso FHIR R4 contra seu StructureDefinition."""

from typing import Any, Optional

# Campos obrigatórios mínimos por ResourceType (subset para validação básica)
REQUIRED_FIELDS: dict[str, list[str]] = {
    "Patient":           ["resourceType"],
    "Observation":       ["resourceType", "status", "code"],
    "Condition":         ["resourceType", "code", "subject"],
    "Encounter":         ["resourceType", "status", "class", "subject"],
    "MedicationRequest": ["resourceType", "status", "intent", "medication", "subject"],
    "DiagnosticReport":  ["resourceType", "status", "code"],
    "Procedure":         ["resourceType", "status", "code", "subject"],
    "Immunization":      ["resourceType", "status", "vaccineCode", "patient"],
    "AllergyIntolerance":["resourceType", "patient"],
    "CarePlan":          ["resourceType", "status", "intent", "subject"],
    "Measure":           ["resourceType", "status", "scoring"],
    "ValueSet":          ["resourceType", "status"],
    "CodeSystem":        ["resourceType", "status", "content"],
}

# Valores válidos para campos de status comuns
VALID_STATUS: dict[str, list[str]] = {
    "Observation": ["registered", "preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error", "unknown"],
    "Condition": ["active", "recurrence", "relapse", "inactive", "remission", "resolved"],
    "Encounter": ["planned", "arrived", "triaged", "in-progress", "onleave", "finished", "cancelled", "entered-in-error", "unknown"],
    "MedicationRequest": ["active", "on-hold", "cancelled", "completed", "entered-in-error", "stopped", "draft", "unknown"],
    "DiagnosticReport": ["registered", "partial", "preliminary", "final", "amended", "corrected", "appended", "cancelled", "entered-in-error", "unknown"],
    "Procedure": ["preparation", "in-progress", "not-done", "on-hold", "stopped", "completed", "entered-in-error", "unknown"],
    "Immunization": ["completed", "entered-in-error", "not-done"],
    "Measure": ["draft", "active", "retired", "unknown"],
    "ValueSet": ["draft", "active", "retired", "unknown"],
    "CodeSystem": ["draft", "active", "retired", "unknown"],
}


def validate_resource(
    resource_type: str,
    resource_data: dict[str, Any],
    profile: Optional[str] = None,
    mode: str = "create",
) -> dict:
    """Valida um recurso FHIR R4 e retorna OperationOutcome.

    Validações:
    1. resourceType presente e corresponde ao endpoint
    2. Campos obrigatórios mínimos presentes
    3. Status válido (quando aplicável)
    4. id não obrigatório em create, obrigatório em update

    Returns:
        OperationOutcome dict (FHIR R4).
    """
    issues: list[dict] = []

    # 1. Verificar resourceType
    declared_type = resource_data.get("resourceType")
    if not declared_type:
        issues.append({
            "severity": "error",
            "code": "required",
            "diagnostics": "resourceType is required",
            "location": ["resourceType"],
        })
    elif declared_type != resource_type:
        issues.append({
            "severity": "error",
            "code": "invalid",
            "diagnostics": f"resourceType '{declared_type}' does not match endpoint '{resource_type}'",
            "location": ["resourceType"],
        })

    # 2. Campos obrigatórios
    required = REQUIRED_FIELDS.get(resource_type, ["resourceType"])
    for field in required:
        if field not in resource_data or resource_data[field] is None:
            issues.append({
                "severity": "error",
                "code": "required",
                "diagnostics": f"Field '{field}' is required for {resource_type}",
                "location": [field],
            })

    # 3. Validar status
    status_val = resource_data.get("status")
    valid_statuses = VALID_STATUS.get(resource_type)
    if status_val and valid_statuses and status_val not in valid_statuses:
        issues.append({
            "severity": "error",
            "code": "code-invalid",
            "diagnostics": f"Invalid status '{status_val}' for {resource_type}. Valid: {valid_statuses}",
            "location": ["status"],
        })

    # 4. id obrigatório em update
    if mode == "update" and not resource_data.get("id"):
        issues.append({
            "severity": "error",
            "code": "required",
            "diagnostics": "Field 'id' is required for update mode",
            "location": ["id"],
        })

    # 5. Sugestão de profile
    if profile:
        issues.append({
            "severity": "information",
            "code": "informational",
            "diagnostics": f"Profile validation against '{profile}' not yet implemented; structural validation only",
        })

    # Determinar resultado
    has_errors = any(i["severity"] == "error" for i in issues)

    if not issues:
        issues.append({
            "severity": "information",
            "code": "informational",
            "diagnostics": f"{resource_type} resource is valid",
        })

    return {
        "resourceType": "OperationOutcome",
        "issue": issues,
    }, not has_errors
