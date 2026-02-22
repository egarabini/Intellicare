"""Routing diagnostic endpoints for WANDA (EF-W003).

POST /api/v1/routing/explain  — explains how a query would be routed
GET  /api/v1/routing/method   — returns current routing method
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/routing", tags=["routing"])

# Global references injected at startup
_intent_router = None
_keyword_router = None
_registry = None
_routing_method = "keyword"


def init_routing_routes(
    intent_router=None,
    keyword_router=None,
    registry=None,
    routing_method: str = "keyword",
) -> None:
    """Inject dependencies at application startup."""
    global _intent_router, _keyword_router, _registry, _routing_method
    _intent_router = intent_router
    _keyword_router = keyword_router
    _registry = registry
    _routing_method = "llm" if intent_router is not None else "keyword"


class RoutingExplainRequest(BaseModel):
    query: str
    patient_id: Optional[str] = None


class RoutingExplainResponse(BaseModel):
    query: str
    target_modules: list[str]
    reason: str
    confidence: float
    routing_method: str
    available_modules: list[str]


@router.post("/explain", response_model=RoutingExplainResponse)
async def explain_routing(request: RoutingExplainRequest):
    """Explain how a query would be routed without actually calling modules.

    Useful for debugging and understanding routing decisions.
    """
    if _registry is None:
        raise HTTPException(status_code=503, detail="Registry not initialized")

    available = _registry.get_online_modules() if _registry else []

    if not available:
        return RoutingExplainResponse(
            query=request.query,
            target_modules=[],
            reason="Nenhum modulo disponivel",
            confidence=0.0,
            routing_method=_routing_method,
            available_modules=[],
        )

    # Try LLM routing if available
    if _intent_router is not None:
        try:
            decision = await _intent_router.route(
                query=request.query,
                available_modules=available,
                patient_id=request.patient_id,
            )
            return RoutingExplainResponse(
                query=request.query,
                target_modules=decision.target_modules,
                reason=decision.reason,
                confidence=decision.confidence,
                routing_method=decision.routing_method,
                available_modules=[m.name for m in available],
            )
        except Exception as e:
            logger.warning("IntentRouter error in explain: %s", e)

    # Keyword fallback
    if _keyword_router is not None:
        decision = _keyword_router.route(
            query=request.query,
            available_modules=available,
        )
        return RoutingExplainResponse(
            query=request.query,
            target_modules=decision.target_modules,
            reason=decision.reason,
            confidence=decision.confidence,
            routing_method="keyword",
            available_modules=[m.name for m in available],
        )

    raise HTTPException(status_code=503, detail="No router available")


@router.get("/method")
async def get_routing_method():
    """Return the current active routing method."""
    return {
        "routing_method": _routing_method,
        "llm_available": _intent_router is not None,
        "description": (
            "LLM-based intent routing via Ollama"
            if _intent_router is not None
            else "Keyword-based routing (v1.0 fallback)"
        ),
    }
