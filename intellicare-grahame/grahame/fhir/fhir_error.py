"""Helper para respostas de erro FHIR R4 (OperationOutcome)."""

from fastapi.responses import JSONResponse


def fhir_error(
    status: int,
    code: str,
    diagnostics: str,
    severity: str = "error",
) -> JSONResponse:
    """Retorna uma JSONResponse com OperationOutcome FHIR R4 padronizado.

    Args:
        status: HTTP status code.
        code: Código FHIR (not-found, invalid, processing, etc.).
        diagnostics: Mensagem descritiva do erro.
        severity: fatal | error | warning | information.
    """
    return JSONResponse(
        status_code=status,
        content={
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": severity,
                    "code": code,
                    "diagnostics": diagnostics,
                }
            ],
        },
        media_type="application/fhir+json",
    )


def operation_outcome_from_errors(errors: list[dict]) -> dict:
    """Monta um dict OperationOutcome com múltiplos issues.

    Args:
        errors: Lista de dicts com chaves severity, code, diagnostics, location (opcional).
    """
    return {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": e.get("severity", "error"),
                "code": e.get("code", "invalid"),
                "diagnostics": e.get("diagnostics", ""),
                **({"location": e["location"]} if "location" in e else {}),
            }
            for e in errors
        ],
    }
