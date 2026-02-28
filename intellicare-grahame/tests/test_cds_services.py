"""Tests for built-in CDS Hook services (patient-view + order-sign) — 11 scenarios."""

import pytest

from intellicare_core.cds_hooks.models import CDSRequest, CDSResponse
from grahame.cds_services.patient_view import PatientViewAlertsService
from grahame.cds_services.order_sign import OrderSignCheckerService


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def patient_view_svc() -> PatientViewAlertsService:
    return PatientViewAlertsService()


@pytest.fixture
def order_sign_svc() -> OrderSignCheckerService:
    return OrderSignCheckerService()


# ── PatientViewAlertsService ───────────────────────────────────────────────────


def test_patient_view_definition(patient_view_svc: PatientViewAlertsService) -> None:
    defn = patient_view_svc.definition
    assert defn.hook == "patient-view"
    assert defn.id == "patient-view-alerts"
    assert "patient" in defn.prefetch
    assert "conditions" in defn.prefetch
    assert "allergies" in defn.prefetch


def test_patient_view_no_allergies_emits_warning(patient_view_svc: PatientViewAlertsService) -> None:
    req = CDSRequest(
        hook="patient-view",
        context={"patientId": "p-001"},
        prefetch={
            "conditions": {"resourceType": "Bundle", "entry": []},
            "allergies": {"resourceType": "Bundle", "entry": []},
        },
    )
    resp = patient_view_svc.handle(req)
    summaries = [c.summary for c in resp.cards]
    assert any("alergi" in s.lower() for s in summaries)


def test_patient_view_high_risk_ckd_emits_card(patient_view_svc: PatientViewAlertsService) -> None:
    req = CDSRequest(
        hook="patient-view",
        context={"patientId": "p-001"},
        prefetch={
            "conditions": {
                "resourceType": "Bundle",
                "entry": [{
                    "resource": {
                        "resourceType": "Condition",
                        "code": {"coding": [{"code": "N18.5", "display": "CKD stage 5"}]},
                    }
                }],
            },
            "allergies": {"resourceType": "Bundle", "entry": [{"resource": {}}]},
        },
    )
    resp = patient_view_svc.handle(req)
    assert any("N18.5" in c.summary for c in resp.cards)


def test_patient_view_no_conditions_emits_info(patient_view_svc: PatientViewAlertsService) -> None:
    req = CDSRequest(
        hook="patient-view",
        context={"patientId": "p-001"},
        prefetch={
            "conditions": {"resourceType": "Bundle", "entry": []},
            "allergies": {"resourceType": "Bundle", "entry": [{"resource": {}}]},
        },
    )
    resp = patient_view_svc.handle(req)
    assert any("condição" in c.summary.lower() or "nenhuma" in c.summary.lower() for c in resp.cards)


def test_patient_view_empty_prefetch_does_not_raise(patient_view_svc: PatientViewAlertsService) -> None:
    req = CDSRequest(hook="patient-view", context={"patientId": "p-001"})
    resp = patient_view_svc.handle(req)
    assert isinstance(resp, CDSResponse)


# ── OrderSignCheckerService ────────────────────────────────────────────────────


def test_order_sign_definition(order_sign_svc: OrderSignCheckerService) -> None:
    defn = order_sign_svc.definition
    assert defn.hook == "order-sign"
    assert defn.id == "order-sign-checker"
    assert "conditions" in defn.prefetch


def test_order_sign_nsaid_ckd_critical(order_sign_svc: OrderSignCheckerService) -> None:
    req = CDSRequest(
        hook="order-sign",
        context={
            "patientId": "p-001",
            "draftOrders": {
                "resourceType": "Bundle",
                "entry": [{
                    "resource": {
                        "medicationCodeableConcept": {
                            "text": "Ibuprofeno 400mg",
                            "coding": [{"display": "ibuprofeno"}],
                        },
                    }
                }],
            },
        },
        prefetch={
            "conditions": {
                "resourceType": "Bundle",
                "entry": [{"resource": {"code": {"coding": [{"code": "N18.5"}]}}}],
            }
        },
    )
    resp = order_sign_svc.handle(req)
    assert any(c.indicator == "critical" for c in resp.cards)


def test_order_sign_metformin_severe_ckd_critical(order_sign_svc: OrderSignCheckerService) -> None:
    req = CDSRequest(
        hook="order-sign",
        context={
            "patientId": "p-001",
            "draftOrders": {
                "resourceType": "Bundle",
                "entry": [{"resource": {"medicationCodeableConcept": {"text": "metformina 500mg"}}}],
            },
        },
        prefetch={
            "conditions": {
                "resourceType": "Bundle",
                "entry": [{"resource": {"code": {"coding": [{"code": "N18.4"}]}}}],
            }
        },
    )
    resp = order_sign_svc.handle(req)
    assert any("etformin" in c.summary for c in resp.cards)
    assert any(c.indicator == "critical" for c in resp.cards)


def test_order_sign_high_alert_warfarin(order_sign_svc: OrderSignCheckerService) -> None:
    req = CDSRequest(
        hook="order-sign",
        context={
            "patientId": "p-001",
            "draftOrders": {
                "resourceType": "Bundle",
                "entry": [{"resource": {"medicationCodeableConcept": {"text": "warfarina 5mg"}}}],
            },
        },
        prefetch={"conditions": {"resourceType": "Bundle", "entry": []}},
    )
    resp = order_sign_svc.handle(req)
    assert any("vigilância" in c.summary.lower() for c in resp.cards)
    assert all(c.indicator in ("info", "warning", "critical") for c in resp.cards)


def test_order_sign_safe_medication_no_cards(order_sign_svc: OrderSignCheckerService) -> None:
    req = CDSRequest(
        hook="order-sign",
        context={
            "patientId": "p-001",
            "draftOrders": {
                "resourceType": "Bundle",
                "entry": [{"resource": {"medicationCodeableConcept": {"text": "paracetamol 500mg"}}}],
            },
        },
        prefetch={"conditions": {"resourceType": "Bundle", "entry": []}},
    )
    resp = order_sign_svc.handle(req)
    assert resp.cards == []


def test_order_sign_empty_draft_orders_no_cards(order_sign_svc: OrderSignCheckerService) -> None:
    req = CDSRequest(
        hook="order-sign",
        context={"patientId": "p-001", "draftOrders": {"resourceType": "Bundle", "entry": []}},
        prefetch={"conditions": {"resourceType": "Bundle", "entry": []}},
    )
    resp = order_sign_svc.handle(req)
    assert resp.cards == []
