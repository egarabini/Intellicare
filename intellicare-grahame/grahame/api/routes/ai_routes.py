"""Rotas AI Operation — POST /ai e POST /fhir/$ai com suporte a SSE (W9-A)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from grahame.fhir.fhir_error import fhir_error
from grahame.services.ai_operation_service import AIOperationService

router = APIRouter(tags=["AI Operation"])


class AIOperationRequest(BaseModel):
    """Payload para operação AI."""

    prompt: str
    agent: str = "florence"  # florence | geralda | wanda
    context: dict[str, Any] | None = None


def _get_ai_service(request: Request) -> AIOperationService:
    config = getattr(request.app.state, "config", None) or __import__(
        "grahame.config", fromlist=["config"]
    ).config
    return AIOperationService(
        wanda_url=config.wanda_url,
        florence_url=config.florence_url,
        geralda_url=config.geralda_url,
        timeout=getattr(config, "ai_operation_timeout", 120),
    )


def _sse_format(event: str, data: dict) -> str:
    """Formata mensagem SSE."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_generator(prompt: str, agent: str, context: dict | None):
    """Generator para SSE streaming."""
    from grahame.config import config

    svc = AIOperationService(
        wanda_url=config.wanda_url,
        florence_url=config.florence_url,
        geralda_url=config.geralda_url,
        timeout=config.ai_operation_timeout,
    )
    full_text = ""
    async for chunk in svc.stream_response(prompt, agent, context):
        full_text += chunk
        yield _sse_format("chunk", {"text": chunk})
    yield _sse_format("done", {"full_text": full_text, "tokens_used": len(full_text) // 4})


@router.post("/ai")
async def ai_operation(
    body: AIOperationRequest,
    request: Request,
):
    """Operação AI — suporta SSE (Accept: text/event-stream) ou JSON."""
    accept = request.headers.get("Accept", "")
    wants_sse = "text/event-stream" in accept

    if wants_sse:
        return StreamingResponse(
            _stream_generator(body.prompt, body.agent, body.context),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # Fallback JSON
    try:
        svc = _get_ai_service(request)
        result = await svc.generate_response(body.prompt, body.agent, body.context)
        return {
            "resourceType": "Parameters",
            "parameter": [
                {"name": "result", "valueString": result},
            ],
        }
    except Exception as e:
        return fhir_error(500, "exception", str(e))


@router.post("/fhir/$ai")
async def fhir_ai_operation(
    body: AIOperationRequest,
    request: Request,
):
    """Operação FHIR $ai — mesmo contrato que /ai."""
    return await ai_operation(body, request)
