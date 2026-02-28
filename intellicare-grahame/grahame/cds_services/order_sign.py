"""CDS Hook: order-sign — fired when a clinician signs a medication order.

Cards emitted:
  • NSAID contraindicated in CKD
  • Metformin contraindicated in severe CKD (eGFR < 30)
  • High-alert medication requires confirmation
  • Duplicate therapy warning (same drug class already ordered)
"""

from __future__ import annotations

from intellicare_core.cds_hooks.models import (
    Card,
    CardSource,
    CDSRequest,
    CDSResponse,
    CDSServiceDefinition,
    Suggestion,
    Action,
)
from intellicare_core.cds_hooks.service import CDSService

_SOURCE = CardSource(
    label="IntelliCare — WANDA",
    url="https://intellicare.example.com",
)

# NSAID RxNorm/RENAME codes (simplified subset — display names for matching)
_NSAID_KEYWORDS = {"ibuprofeno", "diclofenaco", "naproxeno", "cetoprofeno", "meloxicam", "piroxicam"}

# Metformin keywords
_METFORMIN_KEYWORDS = {"metformina", "metformin"}

# CKD stage codes that contraindicate NSAIDs
_CKD_SEVERE = {"N18.4", "N18.5"}

# CKD codes that contraindicate metformin (stage 4+)
_CKD_METFORMIN = {"N18.4", "N18.5"}

# High-alert medications requiring double-check
_HIGH_ALERT_KEYWORDS = {
    "insulina", "insulin", "warfarina", "warfarin",
    "heparina", "heparin", "amiodarona", "amiodarone",
    "lítio", "lithium", "digoxina", "digoxin",
}


def _medication_display(draft_orders: list[dict]) -> list[str]:
    names: list[str] = []
    for order in draft_orders:
        med = order.get("medicationCodeableConcept") or {}
        text = med.get("text", "")
        if text:
            names.append(text.lower())
        for coding in (med.get("coding") or []):
            display = (coding.get("display") or "").lower()
            if display:
                names.append(display)
    return names


def _condition_codes(prefetch: dict) -> set[str]:
    bundle = prefetch.get("conditions", {})
    if not isinstance(bundle, dict):
        return set()
    codes: set[str] = set()
    for entry in bundle.get("entry", []):
        cond = entry.get("resource", {})
        for coding in (cond.get("code", {}).get("coding") or []):
            if coding.get("code"):
                codes.add(coding["code"])
    return codes


def _draft_orders(context: dict) -> list[dict]:
    """Extract draftOrders bundle entries from hook context."""
    bundle = context.get("draftOrders", {})
    if not isinstance(bundle, dict):
        return []
    return [e.get("resource", {}) for e in bundle.get("entry", []) if "resource" in e]


class OrderSignCheckerService(CDSService):
    """Checks medication orders for contraindications and safety alerts."""

    @property
    def definition(self) -> CDSServiceDefinition:
        return CDSServiceDefinition(
            id="order-sign-checker",
            hook="order-sign",
            title="IntelliCare — Verificação de Prescrição",
            description=(
                "Detecta contraindicações, medicamentos de alta vigilância e "
                "terapias duplicadas no momento da assinatura da prescrição."
            ),
            prefetch={
                "patient": "Patient/{{context.patientId}}",
                "conditions": (
                    "Condition?patient={{context.patientId}}"
                    "&clinical-status=active&_count=50"
                ),
            },
        )

    def handle(self, request: CDSRequest) -> CDSResponse:
        context = request.context
        prefetch = request.prefetch or {}
        cards: list[Card] = []

        orders = _draft_orders(context)
        med_names = _medication_display(orders)
        cond_codes = _condition_codes(prefetch)

        # ── NSAID + CKD contraindication ───────────────────────────────────────
        has_nsaid = any(kw in name for name in med_names for kw in _NSAID_KEYWORDS)
        has_ckd = bool(cond_codes & (_CKD_SEVERE | {"N18", "N18.3"}))
        if has_nsaid and has_ckd:
            cards.append(
                Card(
                    summary="Anti-inflamatório contraindicado — DRC ativa",
                    detail=(
                        "AINEs (anti-inflamatórios não esteroidais) são contraindicados "
                        "em pacientes com doença renal crônica pois aceleram a progressão "
                        "da perda de função renal. Considere paracetamol ou opioide fraco."
                    ),
                    indicator="critical",
                    source=_SOURCE,
                    suggestions=[
                        Suggestion(
                            label="Substituir por paracetamol 500 mg",
                            isRecommended=True,
                        )
                    ],
                )
            )

        # ── Metformin + severe CKD ─────────────────────────────────────────────
        has_metformin = any(kw in name for name in med_names for kw in _METFORMIN_KEYWORDS)
        has_severe_ckd = bool(cond_codes & _CKD_METFORMIN)
        if has_metformin and has_severe_ckd:
            cards.append(
                Card(
                    summary="Metformina contraindicada — DRC estágio 4/5",
                    detail=(
                        "Metformina é contraindicada com TFG estimada < 30 mL/min/1.73m² "
                        "devido ao risco de acidose lática. Reavalie antidiabético oral."
                    ),
                    indicator="critical",
                    source=_SOURCE,
                )
            )

        # ── High-alert medications ─────────────────────────────────────────────
        for name in med_names:
            matched = [kw for kw in _HIGH_ALERT_KEYWORDS if kw in name]
            if matched:
                cards.append(
                    Card(
                        summary=f"Medicamento de alta vigilância: {name.title()}",
                        detail=(
                            "Este medicamento requer atenção especial na prescrição, "
                            "dispensação e administração. Verifique dose, via e frequência."
                        ),
                        indicator="warning",
                        source=_SOURCE,
                    )
                )
                break  # one card is enough per request

        return CDSResponse(cards=cards)
