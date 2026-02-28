"""Pydantic models for FHIR Search — SearchRequest / SearchResult."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SearchFilter(BaseModel):
    """A single FHIR search filter extracted from a query string parameter."""

    code: str
    """FHIR search parameter code, e.g. 'name', 'birthdate', 'status'."""

    op: Literal["eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap", "co", "sw"] = "eq"
    """Comparison operator.
        eq=equal, ne=not-equal, gt/lt/ge/le=comparison,
        sa=starts-after, eb=ends-before, ap=approximately,
        co=contains (string), sw=starts-with (string).
    """

    value: str
    """Raw search value (un-parsed)."""

    modifier: Optional[str] = None
    """FHIR modifier: exact, contains, missing, not, text, above, below."""

    system: Optional[str] = None
    """Token system part: 'system|value' parsed into separate fields."""


class SearchRequest(BaseModel):
    """A parsed FHIR search request."""

    resource_type: str
    filters: list[SearchFilter] = Field(default_factory=list)
    sort: list[str] = Field(default_factory=list)
    """Sort fields. Prefix '-' for descending. E.g. ['-date', 'name']."""

    count: int = Field(default=100, ge=1, le=1000)
    """Max results per page."""

    offset: int = Field(default=0, ge=0)
    """Pagination offset."""

    include: list[str] = Field(default_factory=list)
    """_include params: ['Observation:subject', ...]."""

    revinclude: list[str] = Field(default_factory=list)
    """_revinclude params."""

    summary: Optional[Literal["true", "false", "text", "data", "count"]] = None
    """_summary modifier."""

    total: Optional[Literal["none", "estimate", "accurate"]] = "none"
    """_total modifier — cost of accurate count."""


class SearchResult(BaseModel):
    """Result of a FHIR search operation."""

    resource_type: str = "Bundle"
    type: str = "searchset"
    resources: list[dict[str, Any]] = Field(default_factory=list)
    total: Optional[int] = None
    next_offset: Optional[int] = None

    def to_bundle(self) -> dict[str, Any]:
        """Serialize as a FHIR Bundle."""
        bundle: dict[str, Any] = {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [
                {"resource": r, "fullUrl": f"{r.get('resourceType')}/{r.get('id', '')}"}
                for r in self.resources
            ],
        }
        if self.total is not None:
            bundle["total"] = self.total
        return bundle
