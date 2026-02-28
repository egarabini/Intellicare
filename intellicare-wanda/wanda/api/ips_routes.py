"""IPS API routes — /api/v1/ips/* (EF-W002).

Endpoints for IPS cache management, validation, and statistics.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/ips", tags=["ips"])

# Injected by app.py at startup
_ips_manager = None
_ips_enricher = None


def init_ips_routes(ips_manager, ips_enricher=None) -> None:
    """Initialize dependencies (called from app.py)."""
    global _ips_manager, _ips_enricher
    _ips_manager = ips_manager
    _ips_enricher = ips_enricher


@router.get("/stats")
async def ips_stats():
    """Cache statistics for IPS subsystem."""
    if _ips_manager is None:
        raise HTTPException(status_code=503, detail="IPS manager not initialized")

    stats = await _ips_manager.get_stats()
    return {"success": True, "data": stats}


@router.get("/{patient_id}")
async def get_ips(patient_id: str):
    """Get IPS for a patient (with caching).

    Returns the IPS bundle including source metadata
    (florence, cache, stale, degraded, empty).
    """
    if _ips_manager is None:
        raise HTTPException(status_code=503, detail="IPS manager not initialized")

    ips = await _ips_manager.get(patient_id)

    # Optionally enrich
    enriched_data = None
    if _ips_enricher and not ips.is_degraded:
        try:
            enriched = await _ips_enricher.enrich(ips)
            enriched_data = enriched.to_dict()
        except Exception:
            enriched_data = None

    return {
        "success": True,
        "data": enriched_data if enriched_data else ips.to_dict(),
    }


@router.delete("/{patient_id}/cache")
async def invalidate_ips_cache(patient_id: str):
    """Invalidate cached IPS for a patient."""
    if _ips_manager is None:
        raise HTTPException(status_code=503, detail="IPS manager not initialized")

    await _ips_manager.invalidate(patient_id)
    return {
        "success": True,
        "message": f"IPS cache invalidated for {patient_id}",
    }


@router.get("/{patient_id}/validate")
async def validate_ips(patient_id: str):
    """Validate the current IPS for a patient."""
    if _ips_manager is None:
        raise HTTPException(status_code=503, detail="IPS manager not initialized")

    ips = await _ips_manager.get(patient_id)
    validation = _ips_manager.validate(ips)

    return {
        "success": True,
        "data": {
            "patient_id": patient_id,
            "source": ips.source,
            "validation": validation.to_dict(),
        },
    }
