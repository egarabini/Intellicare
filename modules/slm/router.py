"""SLM Router — endpoints REST do modulo SLM."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from intellicare_core.auth.jwt import get_current_tenant
from intellicare_core.contracts.base import TenantContext
from .schemas import AskRequest, AskResponse, ModelInfo
from .service import SLMService

router = APIRouter(prefix="/slm", tags=["slm"])
_svc = SLMService()
Auth = Annotated[TenantContext, Depends(get_current_tenant)]


@router.get("/health")
async def health() -> dict:
    return {"status": "healthy", "module": "slm", "version": "1.0.0"}


@router.get("/models", response_model=list[ModelInfo])
async def list_models(ctx: Auth) -> list[dict]:
    return await _svc.list_models()


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, ctx: Auth):
    if payload.stream:
        return StreamingResponse(
            _svc.stream_ask(
                payload.query, ctx, payload.limit, payload.min_similarity,
            ),
            media_type="text/event-stream",
        )
    try:
        return await _svc.ask(
            payload.query, ctx, payload.limit, payload.min_similarity,
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=504, detail=str(e))

