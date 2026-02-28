"""Rotas FHIR R4 do Grahame."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.schemas.fhir_schemas import FHIRBundle, FHIRBundleEntry, FHIRResourceIn, FHIRResourceOut
from grahame.services.fhir_service import FHIRService

from .deps import get_db

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
):
    svc = FHIRService(session)
    if name:
        resources = await svc.search_patient_by_name(name)
    else:
        resources = await svc.search("Patient")
    return _to_bundle(resources)


@router.post("/Patient", response_model=FHIRResourceOut, status_code=201)
async def create_patient(
    body: FHIRResourceIn,
    session: AsyncSession = Depends(get_db),
):
    body.resource["resourceType"] = "Patient"
    svc = FHIRService(session)
    return await svc.upsert(body.resource)


@router.get("/Patient/{patient_id}", response_model=dict[str, Any])
async def get_patient(patient_id: str, session: AsyncSession = Depends(get_db)):
    svc = FHIRService(session)
    row = await svc.get("Patient", patient_id)
    return row.resource


# ── Observation ───────────────────────────────────────────────────────────


@router.get("/Observation", response_model=FHIRBundle)
async def search_observations(
    patient: str | None = Query(None, description="ID ou referência Patient/ID"),
    session: AsyncSession = Depends(get_db),
):
    svc = FHIRService(session)
    if patient:
        resources = await svc.search_observation_by_patient(patient)
    else:
        resources = await svc.search("Observation")
    return _to_bundle(resources)


@router.post("/Observation", response_model=FHIRResourceOut, status_code=201)
async def create_observation(
    body: FHIRResourceIn,
    session: AsyncSession = Depends(get_db),
):
    body.resource["resourceType"] = "Observation"
    svc = FHIRService(session)
    return await svc.upsert(body.resource)


@router.get("/Observation/{obs_id}", response_model=dict[str, Any])
async def get_observation(obs_id: str, session: AsyncSession = Depends(get_db)):
    svc = FHIRService(session)
    row = await svc.get("Observation", obs_id)
    return row.resource


# ── Generic resource routes ───────────────────────────────────────────────


@router.get("/{resource_type}", response_model=FHIRBundle)
async def search_resources(
    resource_type: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    svc = FHIRService(session)
    resources = await svc.search(resource_type, limit=limit, offset=offset)
    return _to_bundle(resources)


@router.post("/{resource_type}", response_model=FHIRResourceOut, status_code=201)
async def upsert_resource(
    resource_type: str,
    body: FHIRResourceIn,
    session: AsyncSession = Depends(get_db),
):
    body.resource["resourceType"] = resource_type
    svc = FHIRService(session)
    return await svc.upsert(body.resource)


@router.get("/{resource_type}/{fhir_id}", response_model=dict[str, Any])
async def get_resource(
    resource_type: str,
    fhir_id: str,
    session: AsyncSession = Depends(get_db),
):
    svc = FHIRService(session)
    row = await svc.get(resource_type, fhir_id)
    return row.resource


@router.delete("/{resource_type}/{fhir_id}", status_code=204)
async def delete_resource(
    resource_type: str,
    fhir_id: str,
    session: AsyncSession = Depends(get_db),
):
    svc = FHIRService(session)
    await svc.delete(resource_type, fhir_id)
