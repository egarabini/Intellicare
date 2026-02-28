"""Serviço FHIR R4 — operações CRUD sobre recursos clínicos."""

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.fhir_resource import FHIRResource


class FHIRService:
    """Operações sobre recursos FHIR armazenados em banco."""

    def __init__(self, session: AsyncSession, tenant_id: str | None = None) -> None:
        self.session = session
        self.tenant_id = tenant_id

    # ── Helpers ────────────────────────────────────────────────────────────

    def _base_query(self, resource_type: str):
        q = select(FHIRResource).where(
            FHIRResource.resource_type == resource_type,
            FHIRResource.active == True,  # noqa: E712
        )
        if self.tenant_id:
            q = q.where(FHIRResource.tenant_id == self.tenant_id)
        return q

    # ── Read ───────────────────────────────────────────────────────────────

    async def get(self, resource_type: str, fhir_id: str) -> FHIRResource:
        q = self._base_query(resource_type).where(FHIRResource.fhir_id == fhir_id)
        result = await self.session.execute(q)
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"{resource_type}/{fhir_id} not found",
            )
        return row

    async def search(
        self,
        resource_type: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FHIRResource]:
        q = self._base_query(resource_type).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())

    async def search_patient_by_name(self, name: str) -> list[FHIRResource]:
        """Filtra pacientes pelo nome (busca simples em JSON resource)."""
        resources = await self.search("Patient")
        term = name.lower()
        filtered = []
        for r in resources:
            res = r.resource
            for name_obj in res.get("name", []):
                family = name_obj.get("family", "").lower()
                given_parts = [g.lower() for g in name_obj.get("given", [])]
                if term in family or any(term in g for g in given_parts):
                    filtered.append(r)
                    break
        return filtered

    async def search_observation_by_patient(self, patient_ref: str) -> list[FHIRResource]:
        """Filtra observações pelo subject (Patient reference)."""
        resources = await self.search("Observation")
        ref = patient_ref if "Patient/" in patient_ref else f"Patient/{patient_ref}"
        return [
            r for r in resources
            if r.resource.get("subject", {}).get("reference") == ref
        ]

    # ── Write ──────────────────────────────────────────────────────────────

    async def upsert(self, resource: dict) -> FHIRResource:
        """Cria ou atualiza um recurso FHIR (idempotente por resourceType/id)."""
        resource_type = resource.get("resourceType")
        fhir_id = resource.get("id")

        if not resource_type:
            raise HTTPException(status_code=422, detail="resourceType is required")
        if not fhir_id:
            raise HTTPException(status_code=422, detail="id is required in FHIR resource")

        q = select(FHIRResource).where(
            FHIRResource.resource_type == resource_type,
            FHIRResource.fhir_id == fhir_id,
        )
        if self.tenant_id:
            q = q.where(FHIRResource.tenant_id == self.tenant_id)

        result = await self.session.execute(q)
        row = result.scalar_one_or_none()

        if row:
            row.resource = resource
            row.active = True
        else:
            row = FHIRResource(
                resource_type=resource_type,
                fhir_id=fhir_id,
                resource=resource,
                tenant_id=self.tenant_id,
            )
            self.session.add(row)

        await self.session.flush()
        await self.session.refresh(row)
        return row

    async def delete(self, resource_type: str, fhir_id: str) -> None:
        """Soft-delete: marca active=False."""
        row = await self.get(resource_type, fhir_id)
        row.active = False
        await self.session.flush()

    # ── Subscription hook ─────────────────────────────────────────────────

    async def trigger_subscriptions(
        self, resource: dict, event_type: str = "create"
    ) -> None:
        """Evaluate and dispatch FHIR Subscriptions matching this resource mutation.

        Silently no-ops if intellicare_core is not installed or if no
        subscriptions match. Should be called *after* session.commit().
        """
        try:
            from intellicare_core.subscriptions import (  # noqa: PLC0415
                dispatch,
                evaluate_subscriptions,
            )
        except ImportError:
            return

        tenant_id = self.tenant_id or "default"

        from grahame.services.subscription_service import SubscriptionService  # noqa: PLC0415

        svc = SubscriptionService(self.session, tenant_id)
        matches = await evaluate_subscriptions(
            resource, tenant_id, svc.fetch_active, event_type=event_type
        )
        for sub_record, _match_audit in matches:
            result, dispatch_audit = await dispatch(sub_record, resource, tenant_id)
            await svc.record_delivery_result(
                sub_record.id,
                success=result.success,
                status_code=result.status_code,
                error=result.error,
                resource_type=resource.get("resourceType"),
                resource_id=resource.get("id"),
                channel_type=sub_record.channel_type,
            )
