"""Endpoints de rastreabilidade (EF-W009)."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from wanda.observability import FHIRAuditExporter, TraceQueryService

router = APIRouter(prefix="/api/v1/traces", tags=["traces"])

_trace_store = None
_trace_query_service = None
_fhir_exporter = None


def init_trace_routes(trace_store=None, trace_query_service=None, fhir_exporter=None) -> None:
    global _trace_store, _trace_query_service, _fhir_exporter
    _trace_store = trace_store
    _trace_query_service = trace_query_service or (TraceQueryService(trace_store) if trace_store is not None else None)
    _fhir_exporter = fhir_exporter or FHIRAuditExporter()


@router.get("")
async def search_traces(
    patient_id: Optional[str] = None,
    success: Optional[bool] = None,
    agent: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=200),
):
    if _trace_store is None:
        raise HTTPException(status_code=503, detail="Trace store not initialized")
    traces = await _trace_store.search(patient_id=patient_id, success=success, agent=agent, limit=limit)
    return {
        "total": len(traces),
        "items": [
            {
                "trace_id": trace.trace_id,
                "query": trace.original_query,
                "routing_method": trace.routing_method,
                "success": trace.success,
                "total_latency_ms": trace.total_latency_ms,
                "created_at": trace.created_at.isoformat(),
            }
            for trace in traces
        ],
    }


@router.get("/patterns")
async def trace_patterns(period_days: int = Query(default=30, ge=1, le=365)):
    if _trace_query_service is None:
        raise HTTPException(status_code=503, detail="Trace query service not initialized")
    return await _trace_query_service.analyze_routing_patterns(period_days=period_days)


@router.get("/anomalies")
async def trace_anomalies(period_days: int = Query(default=7, ge=1, le=90)):
    if _trace_query_service is None:
        raise HTTPException(status_code=503, detail="Trace query service not initialized")
    anomalies = await _trace_query_service.find_anomalies(period_days=period_days)
    return {
        "period_days": period_days,
        "count": len(anomalies),
        "items": anomalies,
    }


@router.get("/{trace_id}/fhir")
async def trace_fhir(trace_id: str):
    if _trace_store is None:
        raise HTTPException(status_code=503, detail="Trace store not initialized")
    trace = await _trace_store.get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace nao encontrado")
    if _fhir_exporter is None:
        raise HTTPException(status_code=503, detail="FHIR exporter not initialized")
    return await _fhir_exporter.export_decision(trace)


@router.get("/{trace_id}")
async def get_trace(trace_id: str):
    if _trace_store is None:
        raise HTTPException(status_code=503, detail="Trace store not initialized")
    trace = await _trace_store.get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace nao encontrado")
    return {
        "trace_id": trace.trace_id,
        "query": trace.original_query,
        "patient_id": trace.patient_id,
        "routing_method": trace.routing_method,
        "success": trace.success,
        "total_latency_ms": trace.total_latency_ms,
        "agent_calls": [
            {
                "agent_name": call.agent_name,
                "endpoint": call.endpoint,
                "status_code": call.status_code,
                "latency_ms": call.latency_ms,
                "success": call.success,
                "request_payload_hash": call.request_payload_hash,
            }
            for call in trace.agent_calls
        ],
    }
