"""FHIRCriteriaMatcher — parse and evaluate FHIR Search criteria strings.

Supports criteria like:
  Observation?code=glucose
  Observation?value-quantity=gt200
  Observation?status=final&subject=Patient/123
  Patient?gender=female&birthdate=lt2000-01-01
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# FHIR comparator prefixes (ordered longest-first to avoid false matches)
_COMPARATORS = ("ne", "gt", "lt", "ge", "le", "eq", "sa", "eb", "ap")

# Map FHIR search parameter name → dot-paths to check inside the resource JSON.
# '*' wildcard expands lists.
_PARAM_PATHS: dict[str, list[str]] = {
    "status": ["status"],
    "subject": ["subject.reference"],
    "patient": ["subject.reference", "patient.reference"],
    "encounter": ["encounter.reference"],
    "code": ["code.coding.*.code", "code.coding.*.display", "code.text"],
    "category": ["category.*.coding.*.code", "category.*.text"],
    "value-quantity": ["valueQuantity.value"],
    "value-string": ["valueString"],
    "value-integer": ["valueInteger"],
    "value-boolean": ["valueBoolean"],
    "identifier": ["identifier.*.value"],
    "name": ["name.*.family", "name.*.given.*", "name.*.text"],
    "family": ["name.*.family"],
    "given": ["name.*.given.*"],
    "birthdate": ["birthDate"],
    "birth-date": ["birthDate"],
    "gender": ["gender"],
    "active": ["active"],
    "type": ["type"],
    "class": ["class.code"],
    "period-start": ["period.start"],
    "period-end": ["period.end"],
    "recorded-date": ["recordedDate"],
    "onset-date": ["onsetDateTime"],
    "effective-date": ["effectiveDateTime"],
}


@dataclass
class _ParsedParam:
    key: str
    comparator: str  # eq, gt, lt, ge, le, ne, …
    value: str
    modifier: Optional[str] = None  # :exact :contains :text :not :missing


def _split_comparator(raw: str) -> tuple[str, str]:
    """Extract leading FHIR comparator from a value string."""
    for comp in _COMPARATORS:
        if raw.startswith(comp) and len(raw) > len(comp):
            return comp, raw[len(comp):]
    return "eq", raw


def _get_nested(obj: Any, path: str) -> list[Any]:
    """Walk a FHIR JSON object along a dot-separated path with * wildcard."""
    if obj is None:
        return []
    parts = path.split(".", 1)
    key = parts[0]
    rest = parts[1] if len(parts) > 1 else None

    if key == "*":
        if isinstance(obj, list):
            results: list[Any] = []
            for item in obj:
                results.extend(_get_nested(item, rest) if rest else [item])
            return results
        # Scalar with wildcard — treat as self
        return _get_nested(obj, rest) if rest else [obj]

    if isinstance(obj, dict):
        val = obj.get(key)
        if val is None:
            return []
        if rest:
            return _get_nested(val, rest)
        return [val] if not isinstance(val, list) else val

    if isinstance(obj, list):
        results = []
        for item in obj:
            results.extend(_get_nested(item, path))
        return results

    return []


def _compare(actual: Any, comparator: str, expected: str) -> bool:
    """Compare actual resource value against expected string with comparator."""
    if actual is None:
        return False

    # Boolean shortcut
    if isinstance(actual, bool):
        expected_lower = expected.lower()
        actual_bool = "true" if actual else "false"
        return actual_bool == expected_lower if comparator in ("eq", "ne") else False

    # Try numeric comparison
    try:
        a = float(actual)
        e = float(expected)
        if comparator == "eq":
            return a == e
        if comparator == "ne":
            return a != e
        if comparator == "gt":
            return a > e
        if comparator == "lt":
            return a < e
        if comparator == "ge":
            return a >= e
        if comparator == "le":
            return a <= e
    except (ValueError, TypeError):
        pass

    # String comparison
    actual_s = str(actual).lower()
    expected_s = expected.lower()
    if comparator == "eq":
        return actual_s == expected_s
    if comparator == "ne":
        return actual_s != expected_s

    return False


class FHIRCriteriaMatcher:
    """Parse and evaluate FHIR Search criteria for Subscriptions.

    Usage::

        matcher = FHIRCriteriaMatcher("Observation?code=glucose&value-quantity=gt200")
        matcher.matches(resource_dict)  # → True / False
    """

    def __init__(self, criteria: str) -> None:
        self.criteria = criteria
        self.resource_type: str = ""
        self.params: list[_ParsedParam] = []
        self._parse(criteria)

    def _parse(self, criteria: str) -> None:
        if "?" not in criteria:
            self.resource_type = criteria.strip()
            return

        resource, query = criteria.split("?", 1)
        self.resource_type = resource.strip()

        for pair in query.split("&"):
            if "=" not in pair:
                continue
            raw_key, raw_value = pair.split("=", 1)
            modifier: Optional[str] = None
            if ":" in raw_key:
                raw_key, modifier = raw_key.split(":", 1)
            comparator, value = _split_comparator(raw_value)
            self.params.append(
                _ParsedParam(key=raw_key, comparator=comparator, value=value, modifier=modifier)
            )

    # ── Public API ─────────────────────────────────────────────────────────

    def matches(self, resource: dict[str, Any]) -> bool:
        """Return True if *resource* satisfies all criteria parameters."""
        if self.resource_type and resource.get("resourceType") != self.resource_type:
            return False
        for param in self.params:
            if not self._match_param(resource, param):
                return False
        return True

    def _match_param(self, resource: dict[str, Any], param: _ParsedParam) -> bool:
        paths = _PARAM_PATHS.get(param.key, [param.key])
        for path in paths:
            values = _get_nested(resource, path)
            for v in values:
                if _compare(v, param.comparator, param.value):
                    return True
        return False
