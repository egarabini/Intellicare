"""Tests for CDS Hooks models — 15 scenarios."""

import pytest

from intellicare_core.cds_hooks.models import (
    Action,
    Card,
    CardSource,
    CDSRequest,
    CDSResponse,
    CDSServiceDefinition,
    FHIRAuthorization,
    Link,
    Suggestion,
)


_SOURCE = CardSource(label="Test Service", url="https://example.com")


# ── Card ───────────────────────────────────────────────────────────────────────


def test_card_defaults() -> None:
    card = Card(summary="Test summary", source=_SOURCE)
    assert card.indicator == "info"
    assert card.suggestions == []
    assert card.links == []
    assert card.uuid  # auto-generated


def test_card_uuid_unique() -> None:
    c1 = Card(summary="A", source=_SOURCE)
    c2 = Card(summary="B", source=_SOURCE)
    assert c1.uuid != c2.uuid


def test_card_warning_indicator() -> None:
    card = Card(summary="Warning", source=_SOURCE, indicator="warning")
    assert card.indicator == "warning"


def test_card_critical_indicator() -> None:
    card = Card(summary="Critical", source=_SOURCE, indicator="critical")
    assert card.indicator == "critical"


def test_card_with_suggestion() -> None:
    suggestion = Suggestion(label="Accept change", isRecommended=True)
    card = Card(
        summary="Suggestion test",
        source=_SOURCE,
        suggestions=[suggestion],
        selectionBehavior="at-most-one",
    )
    assert len(card.suggestions) == 1
    assert card.suggestions[0].isRecommended is True
    assert card.selectionBehavior == "at-most-one"


def test_card_with_link() -> None:
    link = Link(label="Open reference", url="https://drugs.example.com", type="absolute")
    card = Card(summary="Link test", source=_SOURCE, links=[link])
    assert len(card.links) == 1
    assert card.links[0].type == "absolute"


# ── CDSRequest ─────────────────────────────────────────────────────────────────


def test_cds_request_minimal() -> None:
    req = CDSRequest(hook="patient-view", context={"patientId": "p-001"})
    assert req.hook == "patient-view"
    assert req.context["patientId"] == "p-001"
    assert req.hookInstance  # auto-generated UUID


def test_cds_request_with_prefetch() -> None:
    req = CDSRequest(
        hook="order-sign",
        context={"patientId": "p-001"},
        prefetch={"patient": {"resourceType": "Patient", "id": "p-001"}},
    )
    assert req.prefetch is not None
    assert req.prefetch["patient"]["id"] == "p-001"


def test_cds_request_fhir_authorization() -> None:
    req = CDSRequest(
        hook="patient-view",
        context={},
        fhirServer="https://grahame.example.com",
        fhirAuthorization=FHIRAuthorization(
            access_token="tok123",
            expires_in=3600,
            scope="patient/*.read",
            subject="user-001",
        ),
    )
    assert req.fhirAuthorization is not None
    assert req.fhirAuthorization.scope == "patient/*.read"


# ── CDSResponse ────────────────────────────────────────────────────────────────


def test_cds_response_empty() -> None:
    resp = CDSResponse()
    assert resp.cards == []
    assert resp.systemActions == []


def test_cds_response_with_cards() -> None:
    cards = [
        Card(summary="Info card", source=_SOURCE, indicator="info"),
        Card(summary="Warning card", source=_SOURCE, indicator="warning"),
    ]
    resp = CDSResponse(cards=cards)
    assert len(resp.cards) == 2


# ── CDSServiceDefinition ───────────────────────────────────────────────────────


def test_service_definition_fields() -> None:
    defn = CDSServiceDefinition(
        id="patient-view-alerts",
        hook="patient-view",
        title="Patient Alerts",
        description="Detects high-risk conditions",
        prefetch={
            "patient": "Patient/{{context.patientId}}",
            "conditions": "Condition?patient={{context.patientId}}",
        },
    )
    assert defn.id == "patient-view-alerts"
    assert defn.hook == "patient-view"
    assert "patient" in defn.prefetch


def test_suggestion_auto_uuid() -> None:
    s1 = Suggestion(label="A")
    s2 = Suggestion(label="B")
    assert s1.uuid != s2.uuid


def test_action_create() -> None:
    action = Action(
        type="create",
        description="Add allergy",
        resource={"resourceType": "AllergyIntolerance"},
    )
    assert action.type == "create"
    assert action.resource["resourceType"] == "AllergyIntolerance"
