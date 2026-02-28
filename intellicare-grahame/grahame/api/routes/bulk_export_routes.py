"""FastAPI router para FHIR Bulk Data $export (HL7 Bulk Data Access 2.0).

Kick-off endpoints:
    GET  /$export               → exportação de sistema (202 + Content-Location)
    GET  /Patient/$export       → exportação centrada no paciente (202 + Content-Location)

Status / dados:
    GET    /bulk-status/{job_id}           → 202 in-progress | 200 manifest JSON
    DELETE /bulk-status/{job_id}           → 202 (cancelado)
    GET    /bulk-data/{job_id}/{rtype}     → download NDJSON

Referência: https://hl7.org/fhir/uv/bulkdata/
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, Response

from intellicare_core.bulk.manager import (
    DEFAULT_RESOURCE_TYPES,
    PATIENT_RESOURCE_TYPES,
    get_bulk_manager,
)
from intellicare_core.bulk.models import BulkExportStatus

bulk_router = APIRouter(tags=["Bulk Export"])


# ── Helpers ────────────────────────────────────────────────────────────────────


def _api_base(request: Request) -> str:
    """Base URL da API (ex: 'http://localhost:8012/api/v1')."""
    return str(request.base_url).rstrip("/") + "/api/v1"


def _session_factory(request: Request):
    """Extrai session_factory do app.state, ou None se não configurado."""
    return getattr(request.app.state, "session_factory", None)


# ── Kick-off: system-level ─────────────────────────────────────────────────────


@bulk_router.get(
    "/$export",
    status_code=202,
    summary="FHIR Bulk Data — System $export",
    description=(
        "Inicia exportação assíncrona de todos os recursos do sistema. "
        "Retorna 202 Accepted com header ``Content-Location`` apontando para a URL de polling. "
        "Use ``_type`` para filtrar tipos de recurso (ex: ``Patient,Observation``)."
    ),
)
async def system_export(
    request: Request,
    background_tasks: BackgroundTasks,
    _type: Optional[str] = Query(
        None,
        alias="_type",
        description="Tipos de recurso separados por vírgula",
    ),
) -> Response:
    resource_types = _type.split(",") if _type else list(DEFAULT_RESOURCE_TYPES)
    return await _kickoff(request, background_tasks, resource_types)


# ── Kick-off: patient-level ────────────────────────────────────────────────────


@bulk_router.get(
    "/Patient/$export",
    status_code=202,
    summary="FHIR Bulk Data — Patient $export",
    description=(
        "Inicia exportação assíncrona centrada no compartimento Patient. "
        "Tipos permitidos: Patient, Observation, Condition, MedicationRequest, "
        "AllergyIntolerance, Encounter, Procedure."
    ),
)
async def patient_export(
    request: Request,
    background_tasks: BackgroundTasks,
    _type: Optional[str] = Query(None, alias="_type"),
) -> Response:
    allowed = set(PATIENT_RESOURCE_TYPES)
    if _type:
        resource_types = [t for t in _type.split(",") if t in allowed]
    else:
        resource_types = list(PATIENT_RESOURCE_TYPES)
    return await _kickoff(request, background_tasks, resource_types)


async def _kickoff(
    request: Request,
    background_tasks: BackgroundTasks,
    resource_types: list[str],
) -> Response:
    manager = get_bulk_manager()
    job = manager.create_job(
        request_url=str(request.url),
        resource_types=resource_types,
        tenant_id=getattr(request.state, "tenant_id", "default"),
    )
    sf = _session_factory(request)
    background_tasks.add_task(manager.run_export, job.job_id, sf)
    return Response(
        status_code=202,
        headers={"Content-Location": f"{_api_base(request)}/bulk-status/{job.job_id}"},
    )


# ── Status polling ─────────────────────────────────────────────────────────────


@bulk_router.get(
    "/bulk-status/{job_id}",
    summary="FHIR Bulk Data — Status",
    description=(
        "Verifica o status de um job de exportação. "
        "Retorna 202 se em andamento (header X-Progress), "
        "200 com manifest JSON se concluído, "
        "500 se erro."
    ),
)
async def bulk_status(job_id: str, request: Request) -> Response:
    manager = get_bulk_manager()
    job = manager.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404, detail=f"Bulk export job '{job_id}' not found"
        )

    if job.status == BulkExportStatus.ERROR:
        raise HTTPException(status_code=500, detail=job.error or "Export failed")

    if job.status == BulkExportStatus.CANCELLED:
        raise HTTPException(status_code=404, detail="Export job was cancelled")

    if job.status in (BulkExportStatus.ACCEPTED, BulkExportStatus.IN_PROGRESS):
        return Response(
            status_code=202,
            headers={"X-Progress": job.status.value},
        )

    # COMPLETED → retorna manifest
    manifest = manager.build_manifest(job, _api_base(request))
    return Response(
        status_code=200,
        content=manifest.model_dump_json(),
        media_type="application/json",
    )


# ── Cancel ─────────────────────────────────────────────────────────────────────


@bulk_router.delete(
    "/bulk-status/{job_id}",
    status_code=202,
    summary="FHIR Bulk Data — Cancelar export",
    description="Cancela um job de exportação em andamento. Retorna 404 se não encontrado ou já finalizado.",
)
async def cancel_bulk_export(job_id: str) -> Response:
    manager = get_bulk_manager()
    ok = manager.cancel_job(job_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found or already finished",
        )
    return Response(status_code=202)


# ── Download NDJSON ────────────────────────────────────────────────────────────


@bulk_router.get(
    "/bulk-data/{job_id}/{resource_type}",
    summary="FHIR Bulk Data — Download NDJSON",
    description=(
        "Baixa o arquivo NDJSON de um tipo de recurso específico de um job concluído. "
        "Content-Type: application/fhir+ndjson."
    ),
)
async def download_ndjson(job_id: str, resource_type: str) -> Response:
    manager = get_bulk_manager()
    job = manager.get_job(job_id)

    if job is None or job.status != BulkExportStatus.COMPLETED:
        raise HTTPException(
            status_code=404,
            detail="Data not available — job not found or not completed",
        )

    content = manager.get_ndjson(job_id, resource_type)
    if content is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resource type '{resource_type}' not in this export",
        )

    return Response(
        content=content,
        media_type="application/fhir+ndjson",
        headers={
            "Content-Disposition": f'attachment; filename="{resource_type}.ndjson"'
        },
    )
