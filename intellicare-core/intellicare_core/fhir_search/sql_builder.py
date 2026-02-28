"""FHIRSQLBuilder — translates SearchRequest to SQLAlchemy SELECT expressions.

Strategy:
    - Uses SQLAlchemy JSON column's [] path traversal (compatible with SQLite + PostgreSQL)
    - For array paths ([*]), falls back to case-insensitive LIKE on the JSON text
      (less precise but cross-DB; PostgreSQL GIN indexes handle this efficiently in prod)
    - Simple single-path queries use precise column["key"].as_string() comparison

Operators supported:
    eq, ne, gt, lt, ge, le  — comparison (strings cast as-needed)
    co                       — contains (LIKE '%val%')
    sw                       — starts-with (LIKE 'val%')
    missing                  — IS NULL check (always False for JSON — skipped)
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import JSON, Text, and_, cast, func, or_, select, text
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from ..fhir_storage.models import FHIRNativeResource
from .models import SearchFilter, SearchRequest, SearchResult
from .search_params import SearchParamDef, get_search_param

logger = logging.getLogger(__name__)

_WRITE_OPS = frozenset({"create", "update", "delete"})


class FHIRSQLBuilder:
    """Build and execute FHIR search queries against fhir_native_resources.

    Usage::

        builder = FHIRSQLBuilder(session)
        result = await builder.execute(tenant_id, search_request)
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Public interface ──────────────────────────────────────────────────

    async def execute(
        self,
        tenant_id: str,
        search: SearchRequest,
    ) -> SearchResult:
        """Execute a FHIR search and return a SearchResult."""
        q = self._base_query(tenant_id, search.resource_type)

        for f in search.filters:
            expr = self._build_filter(f, search.resource_type)
            if expr is not None:
                q = q.where(expr)

        # Sort
        for sort_field in search.sort:
            desc = sort_field.startswith("-")
            code = sort_field.lstrip("-")
            col_expr = self._sort_expr(code, search.resource_type)
            if col_expr is not None:
                q = q.order_by(col_expr.desc() if desc else col_expr.asc())

        # Pagination
        q = q.limit(search.count).offset(search.offset)

        result = await self.session.execute(q)
        rows = list(result.scalars().all())
        resources = [row.resource for row in rows]

        # Count (optional — expensive)
        total: Optional[int] = None
        if search.total == "accurate":
            from sqlalchemy import func as sqlfunc, select as sqselect  # noqa: PLC0415
            count_q = (
                sqselect(sqlfunc.count())
                .select_from(FHIRNativeResource)
                .where(
                    FHIRNativeResource.tenant_id == tenant_id,
                    FHIRNativeResource.resource_type == search.resource_type,
                    FHIRNativeResource.is_deleted == False,  # noqa: E712
                )
            )
            count_result = await self.session.execute(count_q)
            total = count_result.scalar_one()

        return SearchResult(
            resources=resources,
            total=total,
            next_offset=search.offset + len(resources) if len(resources) == search.count else None,
        )

    # ── Query helpers ─────────────────────────────────────────────────────

    def _base_query(self, tenant_id: str, resource_type: str):
        return (
            select(FHIRNativeResource)
            .where(
                FHIRNativeResource.tenant_id == tenant_id,
                FHIRNativeResource.resource_type == resource_type,
                FHIRNativeResource.is_deleted == False,  # noqa: E712
            )
        )

    def _build_filter(
        self, f: SearchFilter, resource_type: str
    ) -> Any:
        """Build a SQLAlchemy WHERE expression for a single SearchFilter."""
        param = get_search_param(resource_type, f.code)
        if param is None:
            logger.debug("fhir_search.unknown_param %s for %s", f.code, resource_type)
            return None

        # Handle special _id efficiently
        if f.code == "_id":
            return FHIRNativeResource.fhir_id == f.value

        # Choose strategy based on presence of array paths
        has_array = any("[*]" in p for p in param.paths)

        if has_array:
            return self._array_filter(f, param)
        else:
            return self._simple_filter(f, param)

    def _simple_filter(self, f: SearchFilter, param: SearchParamDef) -> Any:
        """Precise filter for non-array JSON paths using column[key].as_string()."""
        clauses = []
        for path in param.paths:
            expr = self._json_path_expr(path)
            if expr is None:
                continue
            clause = self._apply_op(expr, f.op, f.value, param.type)
            if clause is not None:
                clauses.append(clause)

        if not clauses:
            return None
        return or_(*clauses) if len(clauses) > 1 else clauses[0]

    def _array_filter(self, f: SearchFilter, param: SearchParamDef) -> Any:
        """Approximate filter for array paths via LIKE on full JSON text.

        E.g. name[*].family → check if JSON string contains the value.
        This works for basic use cases; production PostgreSQL uses GIN indexes.
        """
        op = f.op
        val = f.value

        # Cast the full JSON column to text for LIKE approximation
        json_text = func.lower(cast(FHIRNativeResource.resource, Text))

        if op in ("eq", "sw"):
            # Case-insensitive contains (approximation for array member match)
            pattern = f"%{val.lower()}%"
            return json_text.like(pattern)
        elif op == "co":
            pattern = f"%{val.lower()}%"
            return json_text.like(pattern)
        elif op == "ne":
            pattern = f"%{val.lower()}%"
            return json_text.notlike(pattern)
        else:
            # For other ops on array paths, skip (too complex without proper JSON_TABLE support)
            return None

    def _apply_op(
        self, expr: Any, op: str, value: str, param_type: str
    ) -> Any:
        """Apply comparison operator to a SQLAlchemy expression."""
        if param_type == "date":
            return self._date_op(expr, op, value)
        if param_type in ("number", "quantity"):
            return self._number_op(expr, op, value)

        # String / token / reference / uri
        if op == "eq":
            return func.lower(expr) == value.lower()
        elif op == "ne":
            return func.lower(expr) != value.lower()
        elif op == "co":
            return func.lower(expr).like(f"%{value.lower()}%")
        elif op == "sw":
            return func.lower(expr).like(f"{value.lower()}%")
        else:
            # Default: equality
            return func.lower(expr) == value.lower()

    def _date_op(self, expr: Any, op: str, value: str) -> Any:
        """Date comparison — casts expr to text and compares as date string."""
        # Simple lexicographic comparison works for ISO date strings
        if op == "eq":
            return func.substr(expr, 1, 10) == value[:10]
        elif op == "ne":
            return func.substr(expr, 1, 10) != value[:10]
        elif op == "gt":
            return func.substr(expr, 1, 10) > value[:10]
        elif op == "lt":
            return func.substr(expr, 1, 10) < value[:10]
        elif op == "ge":
            return func.substr(expr, 1, 10) >= value[:10]
        elif op == "le":
            return func.substr(expr, 1, 10) <= value[:10]
        elif op == "sa":  # starts-after (same as gt for date)
            return func.substr(expr, 1, 10) > value[:10]
        elif op == "eb":  # ends-before (same as lt for date)
            return func.substr(expr, 1, 10) < value[:10]
        return None

    def _number_op(self, expr: Any, op: str, value: str) -> Any:
        """Numeric comparison."""
        try:
            num = float(value)
        except ValueError:
            return None

        cast_expr = cast(expr, type_=JSON)

        if op == "eq":
            return cast(expr, type_=JSON) == num
        elif op == "ne":
            return cast(expr, type_=JSON) != num
        elif op == "gt":
            return cast(expr, type_=JSON) > num
        elif op == "lt":
            return cast(expr, type_=JSON) < num
        elif op == "ge":
            return cast(expr, type_=JSON) >= num
        elif op == "le":
            return cast(expr, type_=JSON) <= num
        return None

    def _json_path_expr(self, path: str) -> Any:
        """Build a SQLAlchemy expression for a simple JSON dot-path (no arrays).

        Returns None for paths with [*] (use _array_filter instead).
        """
        if "[*]" in path:
            return None

        parts = path.split(".")
        col = FHIRNativeResource.resource
        for part in parts:
            col = col[part]

        # .as_string() returns the JSON value as text for comparison
        try:
            return col.as_string()
        except Exception:
            return None

    def _sort_expr(self, code: str, resource_type: str) -> Any:
        """Build sort expression for *code*."""
        if code == "_lastUpdated":
            return FHIRNativeResource.last_updated

        param = get_search_param(resource_type, code)
        if param is None or not param.paths:
            return None

        # Use first non-array path for sorting
        for path in param.paths:
            if "[*]" not in path:
                return self._json_path_expr(path)

        return None
