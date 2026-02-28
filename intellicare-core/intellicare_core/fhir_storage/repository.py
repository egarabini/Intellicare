"""FHIRRepository — versioned FHIR resource CRUD + history + vread.

Design:
    - Every write creates a new version_id (UUID) and inserts into fhir_native_history
    - fhir_native_resources holds only the CURRENT state (upsert on update)
    - Deletes are soft: is_deleted=True + history entry with interaction="delete"
    - History queries return all snapshots newest-first
    - vread returns a specific snapshot from history
"""

from __future__ import annotations

import datetime
import logging
import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .compartments import extract_compartments
from .models import FHIRNativeResource, FHIRResourceHistory

logger = logging.getLogger(__name__)

_NOT_FOUND = "not_found"


class ResourceNotFoundError(Exception):
    pass


class FHIRRepository:
    """Async FHIR resource repository backed by fhir_native_resources + fhir_native_history."""

    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id

    # ── Internal helpers ──────────────────────────────────────────────────

    async def _get_row(
        self, resource_type: str, fhir_id: str
    ) -> Optional[FHIRNativeResource]:
        result = await self.session.execute(
            select(FHIRNativeResource).where(
                FHIRNativeResource.tenant_id == self.tenant_id,
                FHIRNativeResource.resource_type == resource_type,
                FHIRNativeResource.fhir_id == fhir_id,
            )
        )
        return result.scalar_one_or_none()

    def _inject_meta(
        self, resource: dict[str, Any], version_id: str, last_updated: datetime.datetime
    ) -> dict[str, Any]:
        """Inject FHIR meta (versionId, lastUpdated) into resource dict."""
        r = dict(resource)
        meta = dict(r.get("meta", {}))
        meta["versionId"] = version_id
        meta["lastUpdated"] = last_updated.isoformat() + "Z"
        r["meta"] = meta
        return r

    def _history_entry(
        self,
        row: FHIRNativeResource,
        interaction: str,
    ) -> dict[str, Any]:
        return {
            "fullUrl": f"{row.resource_type}/{row.fhir_id}/_history/{row.version_id}",
            "resource": self._inject_meta(row.resource, row.version_id, row.last_updated),
            "request": {"method": interaction.upper(), "url": f"{row.resource_type}/{row.fhir_id}"},
        }

    # ── Create ─────────────────────────────────────────────────────────────

    async def create(
        self,
        resource: dict[str, Any],
        *,
        author: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a new FHIR resource.

        Assigns a random id if not present in *resource*.
        Returns the stored resource with meta.versionId and meta.lastUpdated.
        """
        resource = dict(resource)
        resource_type = resource.get("resourceType")
        if not resource_type:
            raise ValueError("resource.resourceType is required")

        if not resource.get("id"):
            resource["id"] = str(uuid.uuid4())

        fhir_id = resource["id"]
        version_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        compartments = extract_compartments(resource)

        resource = self._inject_meta(resource, version_id, now)

        row = FHIRNativeResource(
            fhir_id=fhir_id,
            tenant_id=self.tenant_id,
            resource_type=resource_type,
            version_id=version_id,
            resource=resource,
            last_updated=now,
            author=author,
            compartments=compartments,
            is_deleted=False,
        )
        self.session.add(row)

        history_row = FHIRResourceHistory(
            version_id=version_id,
            fhir_id=fhir_id,
            tenant_id=self.tenant_id,
            resource_type=resource_type,
            resource=resource,
            last_updated=now,
            author=author,
            interaction="create",
        )
        self.session.add(history_row)

        await self.session.commit()
        await self.session.refresh(row)
        logger.info("fhir.create %s/%s v%s", resource_type, fhir_id, version_id)
        return row.resource

    # ── Read ───────────────────────────────────────────────────────────────

    async def read(
        self,
        resource_type: str,
        fhir_id: str,
    ) -> dict[str, Any]:
        """Read the current state of a resource.

        Raises ResourceNotFoundError if not found or deleted.
        """
        row = await self._get_row(resource_type, fhir_id)
        if row is None or row.is_deleted:
            raise ResourceNotFoundError(f"{resource_type}/{fhir_id} not found")
        return row.resource

    # ── Update ─────────────────────────────────────────────────────────────

    async def update(
        self,
        resource_type: str,
        fhir_id: str,
        resource: dict[str, Any],
        *,
        author: Optional[str] = None,
    ) -> dict[str, Any]:
        """Update an existing resource (creates a new version).

        Raises ResourceNotFoundError if not found or deleted.
        """
        row = await self._get_row(resource_type, fhir_id)
        if row is None or row.is_deleted:
            raise ResourceNotFoundError(f"{resource_type}/{fhir_id} not found")

        resource = dict(resource)
        resource["id"] = fhir_id
        resource["resourceType"] = resource_type

        version_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        compartments = extract_compartments(resource)
        resource = self._inject_meta(resource, version_id, now)

        row.version_id = version_id
        row.resource = resource
        row.last_updated = now
        row.author = author
        row.compartments = compartments

        history_row = FHIRResourceHistory(
            version_id=version_id,
            fhir_id=fhir_id,
            tenant_id=self.tenant_id,
            resource_type=resource_type,
            resource=resource,
            last_updated=now,
            author=author,
            interaction="update",
        )
        self.session.add(history_row)

        await self.session.commit()
        await self.session.refresh(row)
        logger.info("fhir.update %s/%s v%s", resource_type, fhir_id, version_id)
        return row.resource

    # ── Delete ─────────────────────────────────────────────────────────────

    async def delete(
        self,
        resource_type: str,
        fhir_id: str,
        *,
        author: Optional[str] = None,
    ) -> None:
        """Soft-delete a resource (marks is_deleted=True, keeps history).

        Raises ResourceNotFoundError if not found.
        """
        row = await self._get_row(resource_type, fhir_id)
        if row is None:
            raise ResourceNotFoundError(f"{resource_type}/{fhir_id} not found")
        if row.is_deleted:
            return  # idempotent

        version_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()

        row.is_deleted = True
        row.version_id = version_id
        row.last_updated = now
        row.author = author

        history_row = FHIRResourceHistory(
            version_id=version_id,
            fhir_id=fhir_id,
            tenant_id=self.tenant_id,
            resource_type=resource_type,
            resource=row.resource,
            last_updated=now,
            author=author,
            interaction="delete",
        )
        self.session.add(history_row)

        await self.session.commit()
        logger.info("fhir.delete %s/%s", resource_type, fhir_id)

    # ── History ────────────────────────────────────────────────────────────

    async def history(
        self,
        resource_type: str,
        fhir_id: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return all versions of a resource, newest first.

        Each entry has: fullUrl, resource (with meta), request.
        Returns empty list if resource never existed.
        """
        result = await self.session.execute(
            select(FHIRResourceHistory)
            .where(
                FHIRResourceHistory.tenant_id == self.tenant_id,
                FHIRResourceHistory.resource_type == resource_type,
                FHIRResourceHistory.fhir_id == fhir_id,
            )
            .order_by(FHIRResourceHistory.last_updated.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        return [
            {
                "fullUrl": f"{row.resource_type}/{row.fhir_id}/_history/{row.version_id}",
                "resource": self._inject_meta(row.resource, row.version_id, row.last_updated),
                "request": {
                    "method": row.interaction.upper(),
                    "url": f"{row.resource_type}/{row.fhir_id}",
                },
            }
            for row in rows
        ]

    # ── Vread ──────────────────────────────────────────────────────────────

    async def vread(
        self,
        resource_type: str,
        fhir_id: str,
        version_id: str,
    ) -> dict[str, Any]:
        """Read a specific historical version.

        Raises ResourceNotFoundError if version not found.
        """
        result = await self.session.execute(
            select(FHIRResourceHistory).where(
                FHIRResourceHistory.tenant_id == self.tenant_id,
                FHIRResourceHistory.resource_type == resource_type,
                FHIRResourceHistory.fhir_id == fhir_id,
                FHIRResourceHistory.version_id == version_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ResourceNotFoundError(
                f"{resource_type}/{fhir_id}/_history/{version_id} not found"
            )
        return self._inject_meta(row.resource, row.version_id, row.last_updated)

    # ── Search (basic) ─────────────────────────────────────────────────────

    async def search(
        self,
        resource_type: str,
        *,
        limit: int = 100,
        offset: int = 0,
        compartment: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Basic search — return all (non-deleted) resources of *resource_type*.

        Use FHIRSQLBuilder for parameterized FHIR search.

        Args:
            compartment: Filter to resources with this compartment reference,
                         e.g. 'Patient/123'. Filters via JSON containment check.
        """
        q = (
            select(FHIRNativeResource)
            .where(
                FHIRNativeResource.tenant_id == self.tenant_id,
                FHIRNativeResource.resource_type == resource_type,
                FHIRNativeResource.is_deleted == False,  # noqa: E712
            )
            .order_by(FHIRNativeResource.last_updated.desc())
            .limit(limit)
            .offset(offset)
        )

        if compartment:
            # Python-side filtering (cross-DB compat; replace with DB-side for prod)
            result = await self.session.execute(q)
            rows = list(result.scalars().all())
            return [
                row.resource for row in rows if compartment in (row.compartments or [])
            ]

        result = await self.session.execute(q)
        rows = list(result.scalars().all())
        return [row.resource for row in rows]

    # ── Upsert (convenience) ───────────────────────────────────────────────

    async def upsert(
        self,
        resource: dict[str, Any],
        *,
        author: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create or update a resource based on presence of id."""
        resource_type = resource.get("resourceType")
        fhir_id = resource.get("id")

        if not fhir_id:
            return await self.create(resource, author=author)

        existing = await self._get_row(resource_type or "", fhir_id)
        if existing is None or existing.is_deleted:
            return await self.create(resource, author=author)

        return await self.update(resource_type or "", fhir_id, resource, author=author)
