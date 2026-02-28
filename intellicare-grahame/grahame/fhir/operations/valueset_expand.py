"""$expand — expande um ValueSet FHIR, retornando os conceitos do conjunto."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.codesystem_concept import CodeSystemConcept
from grahame.models.fhir_resource import FHIRResource


async def expand_valueset(
    valueset_id: Optional[str],
    session: AsyncSession,
    tenant_id: str | None = None,
    url: Optional[str] = None,
    filter_text: Optional[str] = None,
    count: int = 100,
    offset: int = 0,
) -> dict:
    """Implementa ValueSet/$expand — FHIR R4.

    Fluxo:
    1. Carregar ValueSet por id ou url canônica
    2. Resolver includes (CodeSystem references)
    3. Filtrar conceitos por filter_text
    4. Aplicar paginação
    5. Retornar ValueSet com expansion
    """
    # 1. Carregar ValueSet
    valueset_resource = None

    if valueset_id and valueset_id not in ("-", ""):
        q = select(FHIRResource).where(
            FHIRResource.resource_type == "ValueSet",
            FHIRResource.fhir_id == valueset_id,
            FHIRResource.active == True,  # noqa: E712
        )
        if tenant_id:
            q = q.where(FHIRResource.tenant_id == tenant_id)
        result = await session.execute(q)
        row = result.scalar_one_or_none()
        if row:
            valueset_resource = row.resource

    elif url:
        q = select(FHIRResource).where(
            FHIRResource.resource_type == "ValueSet",
            FHIRResource.active == True,  # noqa: E712
        )
        if tenant_id:
            q = q.where(FHIRResource.tenant_id == tenant_id)
        result = await session.execute(q)
        for row in result.scalars().all():
            if row.resource.get("url") == url:
                valueset_resource = row.resource
                valueset_id = row.resource.get("id")
                break

    if not valueset_resource and not url:
        raise HTTPException(
            status_code=404,
            detail=f"ValueSet/{valueset_id} not found",
        )

    # 2. Determinar as URLs de CodeSystems a incluir
    codesystem_urls: list[str] = []
    if valueset_resource:
        for include in valueset_resource.get("compose", {}).get("include", []):
            cs_url = include.get("system")
            if cs_url:
                codesystem_urls.append(cs_url)

    # 3. Buscar conceitos
    concepts_query = select(CodeSystemConcept)
    if codesystem_urls:
        concepts_query = concepts_query.where(
            CodeSystemConcept.codesystem_url.in_(codesystem_urls)
        )
    if tenant_id:
        concepts_query = concepts_query.where(CodeSystemConcept.tenant_id == tenant_id)

    concepts_result = await session.execute(concepts_query)
    all_concepts = list(concepts_result.scalars().all())

    # 4. Filtrar por texto
    if filter_text:
        term = filter_text.lower()
        all_concepts = [
            c for c in all_concepts
            if term in (c.display or "").lower() or term in c.code.lower()
        ]

    # 5. Paginação
    total = len(all_concepts)
    paged = all_concepts[offset: offset + count]

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    contains = [
        {
            "system": c.codesystem_url,
            "code": c.code,
            "display": c.display or c.code,
        }
        for c in paged
    ]

    expansion_result = {
        "resourceType": "ValueSet",
        "id": valueset_id or str(uuid.uuid4()),
        "status": "active",
        "expansion": {
            "id": str(uuid.uuid4()),
            "timestamp": now_iso,
            "total": total,
            "offset": offset,
            "contains": contains,
        },
    }

    # Preservar metadata do ValueSet original
    if valueset_resource:
        for field in ("url", "name", "title", "description", "version"):
            if field in valueset_resource:
                expansion_result[field] = valueset_resource[field]

    return expansion_result
