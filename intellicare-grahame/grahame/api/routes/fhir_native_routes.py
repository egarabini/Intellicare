"""FHIR Native Storage routes — versioned FHIR R4 endpoints backed by FHIRRepository.

Endpoints (prefix: /api/v2/fhir):
    POST   /{resourceType}                  — create
    GET    /{resourceType}/{id}             — read
    PUT    /{resourceType}/{id}             — update
    DELETE /{resourceType}/{id}             — delete (soft)
    GET    /{resourceType}/{id}/_history    — history bundle
    GET    /{resourceType}/{id}/_history/{vid} — vread
    GET    /{resourceType}                  — search (FHIR params)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import Response

from grahame.services.fhir_native_service import FHIRNativeService

router = APIRouter(tags=["FHIR Native (v2)"])


def _svc(request: Request) -> FHIRNativeService:
    session = request.state.db
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    return FHIRNativeService(session, tenant_id)


def _author(request: Request) -> str | None:
    return request.headers.get("X-Author-Reference")


# ── Create ────────────────────────────────────────────────────────────────────


@router.post("/v2/fhir/{resource_type}", status_code=201)
async def create_resource(resource_type: str, body: dict, request: Request):
    """Create a new FHIR resource. Assigns id if not provided."""
    body["resourceType"] = resource_type
    return await _svc(request).create(body, author=_author(request))


# ── Read ──────────────────────────────────────────────────────────────────────


@router.get("/v2/fhir/{resource_type}/{fhir_id}")
async def read_resource(resource_type: str, fhir_id: str, request: Request):
    """Read current state of a FHIR resource."""
    return await _svc(request).read(resource_type, fhir_id)


# ── Update ────────────────────────────────────────────────────────────────────


@router.put("/v2/fhir/{resource_type}/{fhir_id}")
async def update_resource(resource_type: str, fhir_id: str, body: dict, request: Request):
    """Update a FHIR resource (creates new version)."""
    body["resourceType"] = resource_type
    body["id"] = fhir_id
    return await _svc(request).update(resource_type, fhir_id, body, author=_author(request))


# ── Delete ────────────────────────────────────────────────────────────────────


@router.delete("/v2/fhir/{resource_type}/{fhir_id}", status_code=204)
async def delete_resource(resource_type: str, fhir_id: str, request: Request):
    """Soft-delete a FHIR resource (keeps history)."""
    await _svc(request).delete(resource_type, fhir_id, author=_author(request))
    return Response(status_code=204)


# ── History ───────────────────────────────────────────────────────────────────


@router.get("/v2/fhir/{resource_type}/{fhir_id}/_history")
async def resource_history(
    resource_type: str, fhir_id: str, request: Request, _count: int = 100
):
    """Return all versions of a FHIR resource as a history Bundle."""
    return await _svc(request).history(resource_type, fhir_id, limit=_count)


# ── Vread ─────────────────────────────────────────────────────────────────────


@router.get("/v2/fhir/{resource_type}/{fhir_id}/_history/{version_id}")
async def vread_resource(
    resource_type: str, fhir_id: str, version_id: str, request: Request
):
    """Read a specific historical version."""
    return await _svc(request).vread(resource_type, fhir_id, version_id)


# ── Search ────────────────────────────────────────────────────────────────────


@router.get("/v2/fhir/{resource_type}")
async def search_resource(resource_type: str, request: Request):
    """FHIR search with standard search parameters.

    Supports: _id, status, name, birthdate, subject, date, code, _count, _offset, _sort.
    Returns a FHIR Bundle searchset.
    """
    params = dict(request.query_params)
    return await _svc(request).search(resource_type, params)
