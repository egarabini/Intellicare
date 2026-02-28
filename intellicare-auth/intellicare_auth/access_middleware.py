"""AccessPolicyMiddleware — FastAPI middleware that resolves and injects Access Policies.

The middleware:
1. Extracts the Bearer token from the Authorization header (if present).
2. Decodes it via KeycloakClient (silent — does not raise on failure).
3. Builds the EffectiveAccessPolicy via PolicyResolver.
4. Injects it into ``request.state.access_policy``.

Routes can then use ``request.state.access_policy`` to enforce authorization.

Notes:
    - This middleware is *non-blocking* — if no token or policy resolution fails,
      an empty (deny-all) EffectiveAccessPolicy is injected.
    - Routes that need strict auth should still use ``get_current_user`` dependency.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class AccessPolicyMiddleware(BaseHTTPMiddleware):
    """Starlette/FastAPI middleware that injects an EffectiveAccessPolicy.

    Args:
        app:             The ASGI application.
        policy_resolver: An instance of ``intellicare_auth.PolicyResolver``.
        skip_paths:      URL path prefixes that bypass policy resolution
                         (e.g. '/api/v1/health').
    """

    def __init__(
        self,
        app: ASGIApp,
        policy_resolver: Any,
        skip_paths: Optional[list[str]] = None,
    ) -> None:
        super().__init__(app)
        self._resolver = policy_resolver
        self._skip_paths = skip_paths or ["/api/v1/health", "/api/v1/info", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Short-circuit for skip paths
        if any(request.url.path.startswith(p) for p in self._skip_paths):
            return await call_next(request)

        jwt_payload: dict[str, Any] = {}

        # Try to decode JWT (silently)
        token = self._extract_token(request)
        if token:
            try:
                from intellicare_auth.client import KeycloakClient  # noqa: PLC0415
                from intellicare_auth.config import KeycloakConfig  # noqa: PLC0415

                client = KeycloakClient(KeycloakConfig())
                jwt_payload = await client.validate_token(token)
            except Exception as exc:
                logger.debug("access_middleware.jwt_decode_failed: %s", exc)

        # Extract tenant from header (X-Tenant-ID)
        request_tenant = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id")

        # Build policy
        try:
            policy = await self._resolver.resolve(jwt_payload, request_tenant)
        except Exception as exc:
            logger.warning("access_middleware.policy_resolve_failed: %s", exc)
            policy = _empty_policy()

        request.state.access_policy = policy
        return await call_next(request)

    @staticmethod
    def _extract_token(request: Request) -> Optional[str]:
        """Extract Bearer token from Authorization header."""
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return auth_header[7:].strip()
        return None


def _empty_policy() -> Any:
    """Return an empty EffectiveAccessPolicy (deny-all) as fallback."""
    try:
        from intellicare_core.access.models import EffectiveAccessPolicy  # noqa: PLC0415
        return EffectiveAccessPolicy()
    except ImportError:
        return None
