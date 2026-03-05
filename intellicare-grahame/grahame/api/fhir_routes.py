"""Rotas FHIR R4 do Grahame."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.schemas.fhir_schemas import FHIRBundle, FHIRBundleEntry, FHIRResourceIn, FHIRResourceOut
from grahame.services.fhir_service import FHIRService

from .deps import get_db, get_policy_context, PolicyContext, FHIRForbiddenError

router = APIRouter(tags=["FHIR R4"])


def _to_bundle(resources: list) -> FHIRBundle:
    entries = [
        FHIRBundleEntry(
            fullUrl=f"{r.resource_type}/{r.fhir_id}",
            resource=r.resource,
        )
        for r in resources
    ]
    return FHIRBundle(total=len(entries), entry=entries)


# ── Patient ───────────────────────────────────────────────────────────────


@router.get("/Patient", response_model=FHIRBundle)
async def search_patients(
    name: str | None = Query(None, description="Busca por nome (parcial)"),
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    result = ctx.evaluator.can_read(ctx.policy, "Patient")
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    svc = FHIRService(session)
    if name:
        resources = await svc.search_patient_by_name(name)
    else:
        resources = await svc.search("Patient")
        
    filtered_resources = [
        ctx.evaluator.apply_field_restrictions(ctx.policy, "Patient", r.resource) 
        for r in resources
    ]
    # Re-wrap in the data models
    for i, r in enumerate(resources):
        r.resource = filtered_resources[i]

    return _to_bundle(resources)


@router.post("/Patient", response_model=FHIRResourceOut, status_code=201)
async def create_patient(
    body: FHIRResourceIn,
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    result = ctx.evaluator.can_write(ctx.policy, "Patient", "create", body.resource)
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    body.resource["resourceType"] = "Patient"
    svc = FHIRService(session)
    return await svc.upsert(body.resource)


@router.get("/Patient/{patient_id}", response_model=dict[str, Any])
async def get_patient(
    patient_id: str, 
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    result = ctx.evaluator.can_read(ctx.policy, "Patient")
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    svc = FHIRService(session)
    row = await svc.get("Patient", patient_id)
    return ctx.evaluator.apply_field_restrictions(ctx.policy, "Patient", row.resource)


# ── Observation ───────────────────────────────────────────────────────────


@router.get("/Observation", response_model=FHIRBundle)
async def search_observations(
    patient: str | None = Query(None, description="ID ou referência Patient/ID"),
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    result = ctx.evaluator.can_read(ctx.policy, "Observation")
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    svc = FHIRService(session)
    if patient:
        resources = await svc.search_observation_by_patient(patient)
    else:
        resources = await svc.search("Observation")

    filtered_resources = [
        ctx.evaluator.apply_field_restrictions(ctx.policy, "Observation", r.resource) 
        for r in resources
    ]
    for i, r in enumerate(resources):
        r.resource = filtered_resources[i]

    return _to_bundle(resources)


@router.post("/Observation", response_model=FHIRResourceOut, status_code=201)
async def create_observation(
    body: FHIRResourceIn,
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    result = ctx.evaluator.can_write(ctx.policy, "Observation", "create", body.resource)
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    body.resource["resourceType"] = "Observation"
    svc = FHIRService(session)
    return await svc.upsert(body.resource)


@router.get("/Observation/{obs_id}", response_model=dict[str, Any])
async def get_observation(
    obs_id: str, 
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    result = ctx.evaluator.can_read(ctx.policy, "Observation")
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    svc = FHIRService(session)
    row = await svc.get("Observation", obs_id)
    return ctx.evaluator.apply_field_restrictions(ctx.policy, "Observation", row.resource)


# ── Generic resource routes ───────────────────────────────────────────────


@router.get("/{resource_type}", response_model=FHIRBundle)
async def search_resources(
    resource_type: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    result = ctx.evaluator.can_read(ctx.policy, resource_type)
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    svc = FHIRService(session)
    resources = await svc.search(resource_type, limit=limit, offset=offset)
    
    filtered_resources = [
        ctx.evaluator.apply_field_restrictions(ctx.policy, resource_type, r.resource) 
        for r in resources
    ]
    for i, r in enumerate(resources):
        r.resource = filtered_resources[i]

    return _to_bundle(resources)


@router.post("/{resource_type}", response_model=FHIRResourceOut, status_code=201)
async def upsert_resource(
    resource_type: str,
    body: FHIRResourceIn,
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    result = ctx.evaluator.can_write(ctx.policy, resource_type, "create", body.resource)
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    body.resource["resourceType"] = resource_type
    svc = FHIRService(session)
    return await svc.upsert(body.resource)


@router.get("/{resource_type}/{fhir_id}", response_model=dict[str, Any])
async def get_resource(
    resource_type: str,
    fhir_id: str,
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    result = ctx.evaluator.can_read(ctx.policy, resource_type)
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    svc = FHIRService(session)
    row = await svc.get(resource_type, fhir_id)
    return ctx.evaluator.apply_field_restrictions(ctx.policy, resource_type, row.resource)


@router.delete("/{resource_type}/{fhir_id}", status_code=204)
async def delete_resource(
    resource_type: str,
    fhir_id: str,
    session: AsyncSession = Depends(get_db),
    ctx: PolicyContext = Depends(get_policy_context),
):
    # Fetch resource first to evaluate criteria appropriately (if policy requires resource context)
    svc = FHIRService(session)
    row = await svc.get(resource_type, fhir_id)
    resource = row.resource if row else None

    result = ctx.evaluator.can_write(ctx.policy, resource_type, "delete", resource)
    if not result.allowed:
        raise FHIRForbiddenError(result.reason)

    await svc.delete(resource_type, fhir_id)
