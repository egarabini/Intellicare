"""Middleware X-On-Behalf-Of — delegação de acesso (W9-C)."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _parse_delegate(header_value: str) -> dict | None:
    """Parse header X-On-Behalf-Of. Aceita Practitioner/123 ou id simples."""
    if not header_value:
        return None
    ref = header_value.strip()
    if not ref:
        return None
    if "/" in ref:
        parts = ref.split("/", 1)
        return {"reference": ref, "type": parts[0], "id": parts[1] if len(parts) > 1 else ""}
    return {"reference": f"Practitioner/{ref}", "type": "Practitioner", "id": ref}


class OnBehalfOfMiddleware(BaseHTTPMiddleware):
    """Middleware que processa header X-On-Behalf-Of para delegação (W9-C)."""

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled:
            return await call_next(request)

        header_value = request.headers.get("X-On-Behalf-Of")
        request.state.on_behalf_of = None
        request.state.audit_actor = getattr(request.state, "user_id", None) or getattr(
            request.state, "actor_id", None
        )

        if header_value and header_value.strip():
            delegate = _parse_delegate(header_value)
            if delegate:
                request.state.on_behalf_of = delegate
            else:
                return JSONResponse(
                    status_code=403,
                    content={"error": "delegation_denied", "detail": "X-On-Behalf-Of inválido"},
                )

        return await call_next(request)
