"""Pagination helpers for FHIR search results."""

from __future__ import annotations

from typing import Any, Optional

from .models import SearchResult


def build_bundle_links(
    base_url: str,
    search_result: SearchResult,
    count: int,
    offset: int,
) -> list[dict[str, str]]:
    """Build FHIR Bundle link entries (self, next, previous).

    Args:
        base_url:      Base URL of the search, e.g. 'https://api.example.com/fhir/Patient'
        search_result: Result with resources and next_offset.
        count:         Requested page size (_count).
        offset:        Current offset.

    Returns:
        List of {relation, url} dicts for Bundle.link.
    """
    links: list[dict[str, str]] = []

    def _url(off: int) -> str:
        return f"{base_url}?_count={count}&_offset={off}"

    links.append({"relation": "self", "url": _url(offset)})

    if search_result.next_offset is not None:
        links.append({"relation": "next", "url": _url(search_result.next_offset)})

    if offset > 0:
        prev_offset = max(0, offset - count)
        links.append({"relation": "previous", "url": _url(prev_offset)})

    return links


def to_fhir_bundle(
    search_result: SearchResult,
    base_url: str = "",
    count: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Convert SearchResult to a full FHIR Bundle with links."""
    bundle: dict[str, Any] = {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "fullUrl": f"{r.get('resourceType')}/{r.get('id', '')}",
                "resource": r,
                "search": {"mode": "match"},
            }
            for r in search_result.resources
        ],
    }

    if search_result.total is not None:
        bundle["total"] = search_result.total

    if base_url:
        bundle["link"] = build_bundle_links(base_url, search_result, count, offset)

    return bundle
