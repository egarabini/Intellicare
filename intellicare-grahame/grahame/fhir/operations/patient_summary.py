"""$summary — gera International Patient Summary (IPS) para um paciente."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.fhir.compartment import PATIENT_COMPARTMENT, get_patient_ref, resource_belongs_to_patient
from grahame.fhir.ips_sections import build_ips_composition, classify_resource
from grahame.models.fhir_resource import FHIRResource


async def patient_summary(
    patient_id: str,
    session: AsyncSession,
    tenant_id: str | None = None,
    author_ref: Optional[str] = None,
    authored_on: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> dict:
    """Implementa Patient/$summary — gera IPS Bundle FHIR R4.

    1. Carrega o Patient
    2. Busca todos os recursos do compartimento
    3. Classifica em seções IPS
    4. Monta Composition
    5. Retorna Bundle document
    """
    patient_ref = get_patient_ref(patient_id)

    # 1. Carregar Patient
    q = select(FHIRResource).where(
        FHIRResource.resource_type == "Patient",
        FHIRResource.fhir_id == patient_id,
        FHIRResource.active == True,  # noqa: E712
    )
    if tenant_id:
        q = q.where(FHIRResource.tenant_id == tenant_id)
    result = await session.execute(q)
    patient_row = result.scalar_one_or_none()

    if not patient_row:
        raise HTTPException(status_code=404, detail=f"Patient/{patient_id} not found")

    # 2. Buscar todos os recursos do compartimento
    resource_types = list(PATIENT_COMPARTMENT.keys())
    all_resources: list[dict] = []

    for rtype in resource_types:
        rq = select(FHIRResource).where(
            FHIRResource.resource_type == rtype,
            FHIRResource.active == True,  # noqa: E712
        )
        if tenant_id:
            rq = rq.where(FHIRResource.tenant_id == tenant_id)
        rresult = await session.execute(rq)
        for row in rresult.scalars().all():
            if resource_belongs_to_patient(row.resource, patient_ref):
                all_resources.append(row.resource)

    # 3. Classificar em seções IPS
    sections_map: dict[str, list[dict]] = {}
    for resource in all_resources:
        section = classify_resource(resource)
        if section:
            sections_map.setdefault(section, []).append(resource)

    # 4. Montar Composition
    composition = build_ips_composition(
        patient=patient_row.resource,
        sections_map=sections_map,
        author_ref=author_ref,
        authored_on=authored_on,
    )

    # 5. Montar Bundle document
    now_iso = authored_on or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Todas as entradas do Bundle (Composition primeiro, depois os recursos)
    all_bundle_resources = [patient_row.resource, composition] + all_resources

    # Deduplicar por resourceType/id
    seen: set[str] = set()
    entries = []
    for res in all_bundle_resources:
        rtype = res.get("resourceType", "")
        rid = res.get("id", "")
        key = f"{rtype}/{rid}"
        if key not in seen and rid:
            seen.add(key)
            entries.append({
                "fullUrl": key,
                "resource": res,
            })

    return {
        "resourceType": "Bundle",
        "id": str(uuid.uuid4()),
        "type": "document",
        "timestamp": now_iso,
        "total": len(entries),
        "entry": entries,
    }
