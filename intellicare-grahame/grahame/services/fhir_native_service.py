"""FHIRNativeService — bridge between Grahame routes and the FHIRRepository.

Wraps FHIRRepository (from intellicare-core) with:
    - Tenant isolation (from request headers)
    - FHIR Bundle construction for search results
    - Error mapping (ResourceNotFoundError → HTTPException 404)
    - Subscription triggering (calls FHIRService.trigger_subscriptions)
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FHIRNativeService:
    """Grahame service that delegates to intellicare_core FHIRRepository."""

    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self._repo = self._get_repo()

    def _get_repo(self):
        try:
            from intellicare_core.fhir_storage import FHIRRepository  # noqa: PLC0415
            return FHIRRepository(self.session, self.tenant_id)
        except ImportError as exc:
            raise RuntimeError(f"intellicare_core.fhir_storage not available: {exc}") from exc

    # ── CRUD ──────────────────────────────────────────────────────────────

    async def create(
        self, resource: dict[str, Any], *, author: Optional[str] = None
    ) -> dict[str, Any]:
        result = await self._repo.create(resource, author=author)
        await self._trigger(result, "create")
        return result

    async def read(self, resource_type: str, fhir_id: str) -> dict[str, Any]:
        try:
            from intellicare_core.fhir_storage.repository import ResourceNotFoundError  # noqa: PLC0415
        except ImportError:
            ResourceNotFoundError = Exception  # type: ignore[misc,assignment]
        try:
            return await self._repo.read(resource_type, fhir_id)
        except ResourceNotFoundError:
            raise HTTPException(status_code=404, detail=f"{resource_type}/{fhir_id} not found")

    async def update(
        self,
        resource_type: str,
        fhir_id: str,
        resource: dict[str, Any],
        *,
        author: Optional[str] = None,
    ) -> dict[str, Any]:
        try:
            from intellicare_core.fhir_storage.repository import ResourceNotFoundError  # noqa: PLC0415
        except ImportError:
            ResourceNotFoundError = Exception  # type: ignore[misc,assignment]
        try:
            result = await self._repo.update(resource_type, fhir_id, resource, author=author)
            await self._trigger(result, "update")
            return result
        except ResourceNotFoundError:
            raise HTTPException(status_code=404, detail=f"{resource_type}/{fhir_id} not found")

    async def delete(
        self, resource_type: str, fhir_id: str, *, author: Optional[str] = None
    ) -> None:
        try:
            from intellicare_core.fhir_storage.repository import ResourceNotFoundError  # noqa: PLC0415
        except ImportError:
            ResourceNotFoundError = Exception  # type: ignore[misc,assignment]
        try:
            await self._repo.delete(resource_type, fhir_id, author=author)
        except ResourceNotFoundError:
            raise HTTPException(status_code=404, detail=f"{resource_type}/{fhir_id} not found")

    async def history(
        self, resource_type: str, fhir_id: str, *, limit: int = 100
    ) -> dict[str, Any]:
        entries = await self._repo.history(resource_type, fhir_id, limit=limit)
        return {
            "resourceType": "Bundle",
            "type": "history",
            "total": len(entries),
            "entry": entries,
        }

    async def vread(
        self, resource_type: str, fhir_id: str, version_id: str
    ) -> dict[str, Any]:
        try:
            from intellicare_core.fhir_storage.repository import ResourceNotFoundError  # noqa: PLC0415
        except ImportError:
            ResourceNotFoundError = Exception  # type: ignore[misc,assignment]
        try:
            return await self._repo.vread(resource_type, fhir_id, version_id)
        except ResourceNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"{resource_type}/{fhir_id}/_history/{version_id} not found",
            )

    async def search(
        self,
        resource_type: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """FHIR search using FHIRSQLBuilder when available, else basic search."""
        try:
            from intellicare_core.fhir_search import FHIRSQLBuilder, parse_search_params  # noqa: PLC0415
            search_req = parse_search_params(resource_type, params)
            builder = FHIRSQLBuilder(self.session)
            result = await builder.execute(self.tenant_id, search_req)
            return result.to_bundle()
        except ImportError:
            # Fallback: basic search without param filtering
            resources = await self._repo.search(resource_type)
            return {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": len(resources),
                "entry": [{"resource": r} for r in resources],
            }

    # ── Subscription trigger ──────────────────────────────────────────────

    async def _trigger(self, resource: dict[str, Any], event_type: str) -> None:
        """Silently trigger FHIR Subscriptions (non-fatal if unavailable)."""
        try:
            from grahame.services.fhir_service import FHIRService  # noqa: PLC0415
            svc = FHIRService(self.session, self.tenant_id)
            await svc.trigger_subscriptions(resource, event_type)
        except Exception as exc:
            logger.debug("fhir_native.trigger_subscriptions silently failed: %s", exc)
