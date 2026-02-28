"""Router FHIR Operations — $everything, $summary, $expand, $validate, $evaluate-measure, $find, $book."""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.fhir.fhir_error import fhir_error, operation_outcome_from_errors
from grahame.fhir.operations.appointment_book import appointment_book
from grahame.fhir.operations.measure_evaluate import evaluate_measure
from grahame.fhir.operations.patient_everything import EverythingParams, patient_everything
from grahame.fhir.operations.patient_summary import patient_summary
from grahame.fhir.operations.resource_validate import validate_resource
from grahame.fhir.operations.schedule_find import schedule_find
from grahame.fhir.operations.valueset_expand import expand_valueset

from ..deps import get_db

router = APIRouter(prefix="/fhir", tags=["FHIR Operations"])

FHIR_MEDIA_TYPE = "application/fhir+json"


# ── Patient/$everything ────────────────────────────────────────────────────


@router.get("/Patient/{patient_id}/$everything")
async def everything(
    patient_id: str,
    _since: Optional[str] = Query(None, description="ISO datetime — recursos modificados desde"),
    _count: int = Query(100, ge=1, le=1000, description="Máximo de recursos por página"),
    _offset: int = Query(0, ge=0),
    _type: Optional[str] = Query(None, description="Tipos separados por vírgula (ex: Observation,Condition)"),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    """Retorna todos os recursos clínicos associados a um paciente (Patient Compartment)."""
    from datetime import datetime

    type_list = [t.strip() for t in _type.split(",")] if _type else None
    since_dt = None
    if _since:
        try:
            since_dt = datetime.fromisoformat(_since.replace("Z", "+00:00"))
        except ValueError:
            return fhir_error(400, "invalid", f"Invalid _since format: {_since}")

    params = EverythingParams(
        start=start,
        end=end,
        _since=since_dt,
        _count=_count,
        _offset=_offset,
        _type=type_list,
    )

    try:
        bundle = await patient_everything(patient_id, params, session)
        return JSONResponse(content=bundle, media_type=FHIR_MEDIA_TYPE)
    except Exception as e:
        if hasattr(e, "status_code"):
            return fhir_error(e.status_code, "not-found", str(e.detail))
        return fhir_error(500, "exception", str(e))


# ── Patient/$summary ───────────────────────────────────────────────────────


@router.get("/Patient/{patient_id}/$summary")
async def summary(
    patient_id: str,
    author: Optional[str] = Query(None, description="Referência ao autor (ex: Practitioner/123)"),
    authored_on: Optional[str] = Query(None),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
):
    """Gera International Patient Summary (IPS) para um paciente."""
    try:
        bundle = await patient_summary(
            patient_id=patient_id,
            session=session,
            author_ref=author,
            authored_on=authored_on,
            start=start,
            end=end,
        )
        return JSONResponse(content=bundle, media_type=FHIR_MEDIA_TYPE)
    except Exception as e:
        if hasattr(e, "status_code"):
            return fhir_error(e.status_code, "not-found", str(e.detail))
        return fhir_error(500, "exception", str(e))


# ── ValueSet/$expand ───────────────────────────────────────────────────────


@router.get("/ValueSet/{valueset_id}/$expand")
@router.post("/ValueSet/{valueset_id}/$expand")
async def expand(
    valueset_id: str,
    url: Optional[str] = Query(None),
    filter: Optional[str] = Query(None, description="Texto para filtrar conceitos"),
    _count: int = Query(100, ge=1, le=1000),
    _offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    """Expande um ValueSet, retornando os conceitos que o compõem."""
    try:
        result = await expand_valueset(
            valueset_id=valueset_id,
            session=session,
            url=url,
            filter_text=filter,
            count=_count,
            offset=_offset,
        )
        return JSONResponse(content=result, media_type=FHIR_MEDIA_TYPE)
    except Exception as e:
        if hasattr(e, "status_code"):
            return fhir_error(e.status_code, "not-found", str(e.detail))
        return fhir_error(500, "exception", str(e))


# ── Resource/$validate ─────────────────────────────────────────────────────


@router.post("/{resource_type}/$validate")
async def validate(
    resource_type: str,
    body: dict[str, Any],
    profile: Optional[str] = Query(None),
    mode: str = Query("create", description="create | update"),
):
    """Valida um recurso FHIR R4 contra seu StructureDefinition."""
    outcome, is_valid = validate_resource(resource_type, body, profile=profile, mode=mode)
    status_code = 200 if is_valid else 422
    return JSONResponse(content=outcome, status_code=status_code, media_type=FHIR_MEDIA_TYPE)


# ── Schedule/$find (W9-B) ───────────────────────────────────────────────────


def _param_value(params: dict, name: str, attr: str = "valueReference"):
    """Extrai valor de Parameters.parameter por nome."""
    for p in params.get("parameter", []):
        if p.get("name") == name:
            ref = p.get(attr, {})
            if isinstance(ref, dict):
                return ref.get("reference")
            return ref
    return None


def _param_datetime(params: dict, name: str) -> datetime | None:
    """Extrai valueDateTime de Parameters."""
    for p in params.get("parameter", []):
        if p.get("name") == name:
            v = p.get("valueDateTime")
            if v:
                try:
                    return datetime.fromisoformat(v.replace("Z", "+00:00"))
                except ValueError:
                    pass
    return None


@router.post("/Schedule/$find")
async def schedule_find_op(
    body: dict[str, Any],
    session: AsyncSession = Depends(get_db),
):
    """Busca slots disponíveis para um actor (Practitioner/HealthcareService) no período."""
    actor_ref = _param_value(body, "actor")
    start = _param_datetime(body, "start")
    end = _param_datetime(body, "end")
    try:
        bundle = await schedule_find(
            session=session,
            actor_ref=actor_ref,
            start=start,
            end=end,
        )
        return JSONResponse(content=bundle, media_type=FHIR_MEDIA_TYPE)
    except Exception as e:
        return fhir_error(500, "exception", str(e))


# ── Appointment/$book (W9-B) ───────────────────────────────────────────────


@router.post("/Appointment/$book")
async def appointment_book_op(
    body: dict[str, Any],
    session: AsyncSession = Depends(get_db),
):
    """Reserva um slot e cria Appointment."""
    slot_ref = _param_value(body, "slot")
    patient_ref = _param_value(body, "patient")
    practitioner_ref = _param_value(body, "practitioner")
    comment_param = next((p for p in body.get("parameter", []) if p.get("name") == "comment"), None)
    comment = comment_param.get("valueString") if comment_param else None

    if not slot_ref or not patient_ref:
        return fhir_error(400, "required", "slot e patient são obrigatórios")

    try:
        appointment = await appointment_book(
            session=session,
            slot_ref=slot_ref,
            patient_ref=patient_ref,
            practitioner_ref=practitioner_ref,
            comment=comment,
        )
        return JSONResponse(content=appointment, status_code=201, media_type=FHIR_MEDIA_TYPE)
    except HTTPException as he:
        return fhir_error(he.status_code, "conflict" if he.status_code == 409 else "not-found", str(he.detail))
    except Exception as e:
        return fhir_error(500, "exception", str(e))


# ── Measure/$evaluate-measure ──────────────────────────────────────────────


@router.get("/Measure/{measure_id}/$evaluate-measure")
async def evaluate(
    measure_id: str,
    periodStart: date = Query(..., description="Início do período (YYYY-MM-DD)"),
    periodEnd: date = Query(..., description="Fim do período (YYYY-MM-DD)"),
    subject: Optional[str] = Query(None, description="Patient/{id} ou Group/{id}"),
    session: AsyncSession = Depends(get_db),
):
    """Avalia uma Measure FHIR contra dados reais de pacientes e retorna MeasureReport."""
    try:
        report = await evaluate_measure(
            measure_id=measure_id,
            period_start=periodStart,
            period_end=periodEnd,
            session=session,
            subject=subject,
        )
        return JSONResponse(content=report, media_type=FHIR_MEDIA_TYPE)
    except Exception as e:
        if hasattr(e, "status_code"):
            return fhir_error(e.status_code, "not-found", str(e.detail))
        return fhir_error(500, "exception", str(e))
