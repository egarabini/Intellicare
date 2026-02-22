"""Aggregation debug endpoint for WANDA (EF-W004).

POST /api/v1/aggregate  — debug endpoint to test aggregation
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["aggregation"])

# Global references injected at startup
_intelligent_aggregator = None
_simple_aggregator = None


def init_aggregation_routes(
    intelligent_aggregator=None,
    simple_aggregator=None,
) -> None:
    """Inject dependencies at application startup."""
    global _intelligent_aggregator, _simple_aggregator
    _intelligent_aggregator = intelligent_aggregator
    _simple_aggregator = simple_aggregator


class AggregationRequest(BaseModel):
    query: str
    responses: list[dict]                      # List of {module_name, data, success}
    recipient_type: str = "professional"       # professional | patient
    patient_context: Optional[str] = None


@router.post("/aggregate")
async def aggregate_debug(request: AggregationRequest):
    """Debug endpoint: test response aggregation without calling live modules.

    Useful for testing LLM aggregation with mock agent responses.
    """
    from wanda.discovery.models import ModuleResponse

    # Convert request dicts to ModuleResponse objects
    module_responses = []
    for r in request.responses:
        module_responses.append(
            ModuleResponse(
                module_name=r.get("module_name", "unknown"),
                endpoint="/api/v1/info",
                status_code=200 if r.get("success", True) else 500,
                data=r.get("data", {}),
                error=r.get("error", ""),
            )
        )

    if not module_responses:
        raise HTTPException(status_code=400, detail="No responses provided")

    # Use intelligent aggregator if available
    if _intelligent_aggregator is not None:
        try:
            result = await _intelligent_aggregator.aggregate(
                query=request.query,
                responses=module_responses,
                patient_context=request.patient_context,
                recipient_type=request.recipient_type,
            )
            return {
                "query": request.query,
                "aggregated_response": result.aggregated_response,
                "modules_used": result.modules_used,
                "aggregation_method": "llm",
            }
        except Exception as e:
            logger.warning("IntelligentAggregator error in debug: %s", e)

    # Fallback to simple aggregator
    if _simple_aggregator is not None:
        result = _simple_aggregator.aggregate(
            query=request.query,
            responses=module_responses,
        )
        return {
            "query": request.query,
            "aggregated_response": result.aggregated_response,
            "modules_used": result.modules_used,
            "aggregation_method": "simple",
        }

    raise HTTPException(status_code=503, detail="No aggregator available")
