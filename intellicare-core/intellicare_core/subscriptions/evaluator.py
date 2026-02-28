"""SubscriptionEvaluator — async engine with injectable DB fetcher.

The fetcher callable keeps the core engine decoupled from any ORM or DB layer.
Grahame (or any module) supplies a fetcher that queries its own DB.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Awaitable, Callable, List

from .matcher import FHIRCriteriaMatcher
from .models import AuditRecord, SubscriptionRecord

# Signature: (tenant_id: str, resource_type: str) → List[SubscriptionRecord]
SubscriptionFetcher = Callable[[str, str], Awaitable[List[SubscriptionRecord]]]


@lru_cache(maxsize=4096)
def _get_matcher(criteria: str) -> FHIRCriteriaMatcher:
    """Cache parsed matchers to avoid reparsing criteria for every event."""
    return FHIRCriteriaMatcher(criteria)


def _criteria_resource_type(criteria: str) -> str:
    if "?" in criteria:
        return criteria.split("?", 1)[0].strip()
    return criteria.strip()


async def evaluate_subscriptions(
    resource: dict,
    tenant_id: str,
    fetcher: SubscriptionFetcher,
    *,
    event_type: str = "create",
) -> list[tuple[SubscriptionRecord, AuditRecord]]:
    """Evaluate active subscriptions against a mutated FHIR resource.

    Args:
        resource:   The FHIR resource dict (after create/update/delete).
        tenant_id:  Tenant context for isolation.
        fetcher:    Async callable that returns active subscriptions for a
                    given (tenant_id, resource_type) pair.
        event_type: "create" | "update" | "delete"

    Returns:
        List of (subscription, audit_record) for every subscription that matches.
    """
    resource_type = resource.get("resourceType", "")
    resource_id = resource.get("id", "")

    subscriptions = await fetcher(tenant_id, resource_type)

    results: list[tuple[SubscriptionRecord, AuditRecord]] = []
    for sub in subscriptions:
        if sub.status != "active":
            continue

        # Fast pre-filter: skip obvious non-matching resource types without
        # running full matcher evaluation.
        criteria_rt = _criteria_resource_type(sub.criteria)
        if criteria_rt and criteria_rt != resource_type:
            continue

        matcher = _get_matcher(sub.criteria)
        if matcher.matches(resource):
            audit = AuditRecord(
                subscription_id=sub.id,
                tenant_id=tenant_id,
                event_type="matched",
                resource_type=resource_type,
                resource_id=resource_id,
                channel_type=sub.channel_type,
                details={"criteria": sub.criteria, "trigger": event_type},
            )
            results.append((sub, audit))

    return results
