"""Endpoints de metricas (EF-W010)."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["metrics"])

_metrics_registry = None


def init_metrics_routes(metrics_registry=None) -> None:
    global _metrics_registry
    _metrics_registry = metrics_registry


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    if _metrics_registry is None:
        raise HTTPException(status_code=503, detail="Metrics not initialized")
    return PlainTextResponse(_metrics_registry.render().decode("utf-8"))


@router.get("/api/v1/metrics/summary")
async def metrics_summary():
    if _metrics_registry is None:
        raise HTTPException(status_code=503, detail="Metrics not initialized")
    return _metrics_registry.summary()


@router.get("/api/v1/slos")
async def slos_status():
    if _metrics_registry is None:
        raise HTTPException(status_code=503, detail="Metrics not initialized")
    return _metrics_registry.slos_snapshot()


@router.get("/api/v1/slos/history")
async def slos_history(limit: int = 50):
    if _metrics_registry is None:
        raise HTTPException(status_code=503, detail="Metrics not initialized")
    return {
        "total": len(_metrics_registry.slos_history(limit=200)),
        "items": _metrics_registry.slos_history(limit=limit),
    }
