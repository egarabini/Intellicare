"""$everything — retorna todos os recursos clínicos de um paciente (Patient Compartment)."""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.fhir.compartment import (
    PATIENT_COMPARTMENT,
    get_patient_ref,
    resource_belongs_to_patient,
)
from grahame.fhir.reference_resolver import resolve_references
from grahame.models.fhir_resource import FHIRResource


@dataclass
class EverythingParams:
    start: Optional[date] = None
    end: Optional[date] = None
    _since: Optional[datetime] = None
    _count: int = 100
    _offset: int = 0
    _type: Optional[list[str]] = field(default=None)


async def patient_everything(
    patient_id: str,
    params: EverythingParams,
    session: AsyncSession,
    tenant_id: str | None = None,
) -> dict:
    """Implementa Patient/$everything — FHIR R4.

    1. Carrega o Patient (verifica existência)
    2. Busca recursos do Patient Compartment
    3. Filtra por _type, _since, start/end
    4. Resolve referências recursivamente
    5. Deduplica
    6. Retorna Bundle searchset
    """
    patient_ref = get_patient_ref(patient_id)

    # 1. Carregar Patient
    patient_row = await _get_resource(session, "Patient", patient_id, tenant_id)
    if not patient_row:
        raise HTTPException(
            status_code=404,
            detail=f"Patient/{patient_id} not found",
        )

    # 2. Buscar todos os resource types do compartment (ou filtrar por _type)
    resource_types = list(PATIENT_COMPARTMENT.keys())
    if params._type:
        resource_types = [t for t in resource_types if t in params._type]

    collected: list[dict] = [patient_row.resource]
    seen: set[str] = {f"Patient/{patient_id}"}

    for rtype in resource_types:
        rows = await _fetch_compartment_resources(
            session, rtype, patient_ref, tenant_id, params
        )
        for row in rows:
            key = f"{row.resource_type}/{row.fhir_id}"
            if key not in seen:
                seen.add(key)
                collected.append(row.resource)

    # 3. Resolver referências
    additional = await resolve_references(collected, session, tenant_id)
    for res in additional:
        key = f"{res.get('resourceType')}/{res.get('id')}"
        if key not in seen:
            seen.add(key)
            collected.append(res)

    # 4. Paginação
    start = params._offset
    end = start + params._count
    page = collected[start:end]

    # 5. Montar Bundle
    entries = [
        {
            "fullUrl": f"{r['resourceType']}/{r['id']}",
            "resource": r,
        }
        for r in page
        if r.get("id")
    ]

    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "searchset",
        "total": len(collected),
        "entry": entries,
        "link": [
            {
                "relation": "self",
                "url": f"/fhir/Patient/{patient_id}/$everything?_count={params._count}&_offset={params._offset}",
            }
        ],
    }


async def _get_resource(
    session: AsyncSession,
    resource_type: str,
    fhir_id: str,
    tenant_id: str | None,
) -> FHIRResource | None:
    q = select(FHIRResource).where(
        FHIRResource.resource_type == resource_type,
        FHIRResource.fhir_id == fhir_id,
        FHIRResource.active == True,  # noqa: E712
    )
    if tenant_id:
        q = q.where(FHIRResource.tenant_id == tenant_id)
    result = await session.execute(q)
    return result.scalar_one_or_none()


async def _fetch_compartment_resources(
    session: AsyncSession,
    resource_type: str,
    patient_ref: str,
    tenant_id: str | None,
    params: EverythingParams,
) -> list[FHIRResource]:
    """Busca recursos de um tipo que pertencem ao compartimento do paciente."""
    q = select(FHIRResource).where(
        FHIRResource.resource_type == resource_type,
        FHIRResource.active == True,  # noqa: E712
    )
    if tenant_id:
        q = q.where(FHIRResource.tenant_id == tenant_id)
    if params._since:
        q = q.where(FHIRResource.updated_at >= params._since)

    result = await session.execute(q)
    rows = list(result.scalars().all())

    # Filtro Python-side para compatibilidade SQLite/PostgreSQL
    filtered: list[FHIRResource] = []
    for row in rows:
        if not resource_belongs_to_patient(row.resource, patient_ref):
            continue

        # Filtro por start/end (usa effectiveDateTime ou recordedDate)
        if params.start or params.end:
            if not _in_date_range(row.resource, params.start, params.end):
                continue

        filtered.append(row)

    return filtered


def _in_date_range(resource: dict, start: Optional[date], end: Optional[date]) -> bool:
    """Verifica se o recurso está no intervalo de datas (usa vários campos FHIR)."""
    date_fields = [
        "effectiveDateTime", "effectivePeriod", "recordedDate",
        "onsetDateTime", "authoredOn", "date", "period",
    ]

    for field in date_fields:
        val = resource.get(field)
        if not val:
            continue
        try:
            if isinstance(val, dict):
                # Period: start/end
                raw = val.get("start") or val.get("end")
            else:
                raw = val

            if raw:
                dt = datetime.fromisoformat(raw[:10]).date()
                if start and dt < start:
                    return False
                if end and dt > end:
                    return False
                return True
        except (ValueError, TypeError):
            continue

    return True  # sem data → inclui
