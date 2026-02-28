"""FHIR search query string parser — converts URL query params to SearchRequest.

Handles:
    - Prefixed values: gt2023-01-01, lt100, ge18
    - Modifiers: name:exact=Silva, name:contains=ilv
    - Token system|value: identifier=http://cpf.gov.br|12345678901
    - Special params: _count, _offset, _sort, _include, _revinclude, _summary, _total
"""

from __future__ import annotations

import re
from typing import Any

from .models import SearchFilter, SearchRequest

# Numeric/date prefix operators
_PREFIX_RE = re.compile(r"^(eq|ne|gt|lt|ge|le|sa|eb|ap)")
_MODIFIER_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_-]*)(?::([a-zA-Z]+))?$")


def _parse_value(raw: str) -> tuple[str, str]:
    """Split a FHIR search value into (op, value).

    Examples:
        "gt2023-01-01" → ("gt", "2023-01-01")
        "le100"        → ("le", "100")
        "active"       → ("eq", "active")
    """
    m = _PREFIX_RE.match(raw)
    if m:
        return m.group(1), raw[len(m.group(1)):]
    return "eq", raw


def _parse_code_modifier(key: str) -> tuple[str, str | None]:
    """Split 'code:modifier' into (code, modifier_or_None)."""
    if ":" in key:
        code, modifier = key.split(":", 1)
        return code, modifier
    return key, None


def parse_search_params(
    resource_type: str,
    params: dict[str, Any],
) -> SearchRequest:
    """Parse a FHIR search query param dict into a SearchRequest.

    Args:
        resource_type: FHIR resource type (e.g. 'Patient').
        params:        Dict of query parameters (from request.query_params or similar).
                       Values may be str or list[str].

    Returns:
        SearchRequest ready for FHIRSQLBuilder.
    """
    filters: list[SearchFilter] = []
    sort: list[str] = []
    count = 100
    offset = 0
    include: list[str] = []
    revinclude: list[str] = []
    summary = None
    total = "none"

    for raw_key, raw_val in params.items():
        values = raw_val if isinstance(raw_val, list) else [raw_val]

        # ── Special / control params ──────────────────────────────────────
        if raw_key == "_count":
            try:
                count = max(1, min(1000, int(values[0])))
            except (ValueError, IndexError):
                pass
            continue

        if raw_key == "_offset":
            try:
                offset = max(0, int(values[0]))
            except (ValueError, IndexError):
                pass
            continue

        if raw_key == "_sort":
            for v in values:
                sort.extend(v.split(","))
            continue

        if raw_key == "_include":
            include.extend(v for v in values if v)
            continue

        if raw_key == "_revinclude":
            revinclude.extend(v for v in values if v)
            continue

        if raw_key == "_summary":
            summary = values[0] if values else None
            continue

        if raw_key == "_total":
            total = values[0] if values else "none"
            continue

        # _id is a valid FHIR search param — treated as a filter
        if raw_key == "_id":
            for val in values:
                filters.append(SearchFilter(code="_id", op="eq", value=val))
            continue

        # Skip other leading-underscore params not handled above
        if raw_key.startswith("_"):
            continue

        # ── Filter params ─────────────────────────────────────────────────
        code, modifier = _parse_code_modifier(raw_key)

        for val in values:
            # Token system|value split
            system = None
            if "|" in val:
                system, val = val.split("|", 1)

            op, parsed_val = _parse_value(val)

            # :contains / :missing modifiers map to pseudo-operators
            if modifier == "missing":
                op = "missing"
            elif modifier == "exact":
                op = "eq"  # exact matching handled by builder
            elif modifier == "contains":
                op = "co"

            filters.append(
                SearchFilter(
                    code=code,
                    op=op,  # type: ignore[arg-type]
                    value=parsed_val,
                    modifier=modifier,
                    system=system,
                )
            )

    return SearchRequest(
        resource_type=resource_type,
        filters=filters,
        sort=sort,
        count=count,
        offset=offset,
        include=include,
        revinclude=revinclude,
        summary=summary,
        total=total,  # type: ignore[arg-type]
    )
