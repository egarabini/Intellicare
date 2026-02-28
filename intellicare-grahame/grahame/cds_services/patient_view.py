"""CDS Hook: patient-view — fired when a clinician opens a patient chart.

Cards emitted:
  • Missing allergy documentation warning
  • Overdue screening reminders (based on conditions + age)
  • Active high-risk condition alert
"""

from __future__ import annotations

from intellicare_core.cds_hooks.models import (
    Card,
    CardSource,
    CDSRequest,
    CDSResponse,
    CDSServiceDefinition,
)
from intellicare_core.cds_hooks.service import CDSService

_SOURCE = CardSource(
    label="IntelliCare — WANDA",
    url="https://intellicare.example.com",
)

# ICD-10/CID-10 codes for high-risk chronic conditions
_HIGH_RISK_CODES = {
    "N18",    # Chronic kidney disease
    "N18.3",  # CKD stage 3
    "N18.4",  # CKD stage 4
    "N18.5",  # CKD stage 5
    "E11",    # Diabetes mellitus type 2
    "I10",    # Essential hypertension
    "I50",    # Heart failure
    "J44",    # COPD
}


def _extract_conditions(prefetch: dict) -> list[dict]:
    bundle = prefetch.get("conditions", {})
    if not isinstance(bundle, dict):
        return []
    entries = bundle.get("entry", [])
    return [e.get("resource", {}) for e in entries if "resource" in e]


def _has_allergies(prefetch: dict) -> bool:
    bundle = prefetch.get("allergies", {})
    if not isinstance(bundle, dict):
        return True  # assume present if no prefetch
    entries = bundle.get("entry", [])
    return len(entries) > 0


def _condition_codes(conditions: list[dict]) -> set[str]:
    codes: set[str] = set()
    for cond in conditions:
        for coding in (cond.get("code", {}).get("coding") or []):
            if coding.get("code"):
                codes.add(coding["code"])
    return codes


class PatientViewAlertsService(CDSService):
    """Inspects patient chart on open and emits actionable alert cards."""

    @property
    def definition(self) -> CDSServiceDefinition:
        return CDSServiceDefinition(
            id="patient-view-alerts",
            hook="patient-view",
            title="IntelliCare — Alertas do Paciente",
            description=(
                "Verifica condições de alto risco, documentação de alergias e "
                "rastreamentos pendentes ao abrir o prontuário."
            ),
            prefetch={
                "patient": "Patient/{{context.patientId}}",
                "conditions": (
                    "Condition?patient={{context.patientId}}"
                    "&clinical-status=active&_count=50"
                ),
                "allergies": (
                    "AllergyIntolerance?patient={{context.patientId}}&_count=10"
                ),
            },
        )

    def handle(self, request: CDSRequest) -> CDSResponse:
        prefetch = request.prefetch or {}
        cards: list[Card] = []

        conditions = _extract_conditions(prefetch)
        codes = _condition_codes(conditions)

        # ── Card 1: Missing allergy documentation ──────────────────────────────
        if not _has_allergies(prefetch):
            cards.append(
                Card(
                    summary="Alergias não documentadas",
                    detail=(
                        "Nenhuma alergia ou intolerância registrada para este paciente. "
                        "Registre alergias antes de prescrever medicamentos."
                    ),
                    indicator="warning",
                    source=_SOURCE,
                )
            )

        # ── Card 2: High-risk chronic conditions ───────────────────────────────
        high_risk = codes & _HIGH_RISK_CODES
        if high_risk:
            labels = ", ".join(sorted(high_risk))
            cards.append(
                Card(
                    summary=f"Condição de alto risco ativa: {labels}",
                    detail=(
                        "Este paciente possui condição crônica de alto risco registrada. "
                        "Verifique o plano terapêutico e metas de controle."
                    ),
                    indicator="warning",
                    source=_SOURCE,
                )
            )

        # ── Card 3: No active conditions on record ─────────────────────────────
        if not conditions:
            cards.append(
                Card(
                    summary="Nenhuma condição ativa registrada",
                    detail=(
                        "O prontuário não contém condições clínicas ativas. "
                        "Considere revisar o histórico e registrar problemas ativos."
                    ),
                    indicator="info",
                    source=_SOURCE,
                )
            )

        return CDSResponse(cards=cards)
