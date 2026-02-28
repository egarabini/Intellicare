"""Tests for evaluate_subscriptions() — 12 scenarios."""

import datetime
import pytest

from intellicare_core.subscriptions.evaluator import evaluate_subscriptions
from intellicare_core.subscriptions.evaluator import _get_matcher
from intellicare_core.subscriptions.models import SubscriptionRecord


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_sub(
    criteria: str,
    channel_type: str = "rest-hook",
    status: str = "active",
    sub_id: str = "sub-001",
) -> SubscriptionRecord:
    return SubscriptionRecord(
        id=sub_id,
        tenant_id="tenant-A",
        status=status,
        criteria=criteria,
        channel_type=channel_type,
        channel_endpoint="https://example.com/hook",
    )


OBS_GLUCOSE = {
    "resourceType": "Observation",
    "id": "obs-001",
    "status": "final",
    "code": {"coding": [{"code": "glucose"}]},
    "subject": {"reference": "Patient/p1"},
    "valueQuantity": {"value": 250},
}

PATIENT = {
    "resourceType": "Patient",
    "id": "p1",
    "status": "active",
    "gender": "female",
}


# ── fetcher helper ─────────────────────────────────────────────────────────

def make_fetcher(*subs: SubscriptionRecord):
    """Return a fetcher that serves the given subscriptions."""
    async def fetcher(tenant_id: str, resource_type: str) -> list[SubscriptionRecord]:
        return [s for s in subs if s.tenant_id == tenant_id]
    return fetcher


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_no_subscriptions_returns_empty():
    results = await evaluate_subscriptions(
        OBS_GLUCOSE, "tenant-A", make_fetcher()
    )
    assert results == []


@pytest.mark.asyncio
async def test_matching_subscription_returned():
    sub = _make_sub("Observation?status=final")
    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", make_fetcher(sub))
    assert len(results) == 1
    assert results[0][0].id == "sub-001"


@pytest.mark.asyncio
async def test_non_matching_subscription_excluded():
    sub = _make_sub("Observation?status=preliminary")
    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", make_fetcher(sub))
    assert results == []


@pytest.mark.asyncio
async def test_inactive_subscription_excluded():
    sub = _make_sub("Observation?status=final", status="off")
    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", make_fetcher(sub))
    assert results == []


@pytest.mark.asyncio
async def test_error_status_subscription_excluded():
    sub = _make_sub("Observation?status=final", status="error")
    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", make_fetcher(sub))
    assert results == []


@pytest.mark.asyncio
async def test_multiple_subs_only_matching_returned():
    sub_match = _make_sub("Observation?status=final", sub_id="sub-match")
    sub_no_match = _make_sub("Observation?status=preliminary", sub_id="sub-no-match")
    results = await evaluate_subscriptions(
        OBS_GLUCOSE, "tenant-A", make_fetcher(sub_match, sub_no_match)
    )
    assert len(results) == 1
    assert results[0][0].id == "sub-match"


@pytest.mark.asyncio
async def test_value_quantity_gt_match():
    sub = _make_sub("Observation?value-quantity=gt200")
    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", make_fetcher(sub))
    assert len(results) == 1


@pytest.mark.asyncio
async def test_value_quantity_gt_no_match():
    sub = _make_sub("Observation?value-quantity=gt300")
    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", make_fetcher(sub))
    assert results == []


@pytest.mark.asyncio
async def test_tenant_isolation():
    sub_a = _make_sub("Observation", sub_id="sub-A")
    sub_b = SubscriptionRecord(
        id="sub-B",
        tenant_id="tenant-B",
        status="active",
        criteria="Observation",
        channel_type="rest-hook",
    )

    async def fetcher(tenant_id: str, resource_type: str) -> list[SubscriptionRecord]:
        return [s for s in [sub_a, sub_b] if s.tenant_id == tenant_id]

    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", fetcher)
    assert len(results) == 1
    assert results[0][0].id == "sub-A"


@pytest.mark.asyncio
async def test_audit_record_has_correct_fields():
    sub = _make_sub("Observation?status=final")
    results = await evaluate_subscriptions(
        OBS_GLUCOSE, "tenant-A", make_fetcher(sub), event_type="update"
    )
    assert len(results) == 1
    _sub_rec, audit = results[0]
    assert audit.event_type == "matched"
    assert audit.resource_type == "Observation"
    assert audit.resource_id == "obs-001"
    assert audit.channel_type == "rest-hook"
    assert audit.details["trigger"] == "update"


@pytest.mark.asyncio
async def test_resource_type_only_criteria_matches_all():
    sub = _make_sub("Observation")
    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", make_fetcher(sub))
    assert len(results) == 1


@pytest.mark.asyncio
async def test_wrong_resource_type_criteria_no_match():
    sub = _make_sub("Patient")
    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", make_fetcher(sub))
    assert results == []


@pytest.mark.asyncio
async def test_fast_prefilter_skips_non_matching_resource_type_without_matcher(monkeypatch):
    calls = {"count": 0}

    class _FailingMatcher:
        def __init__(self, _criteria):
            calls["count"] += 1

        def matches(self, _resource):
            return True

    # Patch matcher factory internals by replacing cached function body behavior.
    # If prefilter works, matcher must never be instantiated for Patient criteria.
    monkeypatch.setattr(
        "intellicare_core.subscriptions.evaluator._get_matcher",
        lambda criteria: _FailingMatcher(criteria),
    )

    sub = _make_sub("Patient?gender=female")
    results = await evaluate_subscriptions(OBS_GLUCOSE, "tenant-A", make_fetcher(sub))
    assert results == []
    assert calls["count"] == 0


def test_matcher_cache_reuses_instances():
    _get_matcher.cache_clear()
    m1 = _get_matcher("Observation?status=final")
    m2 = _get_matcher("Observation?status=final")
    assert m1 is m2
