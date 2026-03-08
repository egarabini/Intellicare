"""Auth middleware for intellicare-admin protected API routes."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from intellicare_auth.middleware import get_keycloak_client


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate Bearer token for protected admin API routes."""

    _PUBLIC_PATHS = {
        "/api/v1/health",
        "/api/v1/info",
        "/openapi.json",
        "/docs",
        "/redoc",
    }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Keep dashboard/static and health/info public.
        if not path.startswith("/api/") or path in self._PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Token ausente ou invalido."})

        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return JSONResponse(status_code=401, content={"detail": "Token ausente ou invalido."})

        try:
            payload = await get_keycloak_client().validate_token(token)
        except Exception as exc:  # noqa: BLE001
            return JSONResponse(status_code=401, content={"detail": f"Token invalido: {exc}"})

        request.state.auth_payload = payload
        return await call_next(request)
