"""
DEM-065 — Middleware que bloqueia requests de tenants suspensos.

Intercepta no nível ASGI, antes dos route handlers.
Paths públicos (health, metrics, admin-ui, static) passam sem checagem.
PLATFORM_ADMIN nunca é bloqueado.
"""
from __future__ import annotations

import logging
from typing import Any

from jose import JWTError, jwt as jose_jwt
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("intellicare.tenant_guard")

# Prefixos que não precisam de checagem de tenant
_PUBLIC_PREFIXES = (
    "/health",
    "/metrics",
    "/admin-ui",
    "/gestor-ui",
    "/clinico-ui",
    "/paciente-ui",
    "/portal",
    "/docs",
    "/openapi.json",
    "/admin/",       # admin endpoints usam PLATFORM_ADMIN, não tenants
)


class TenantGuardMiddleware(BaseHTTPMiddleware):
    """Bloqueia com 403 qualquer request de tenant suspenso."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Skip para paths públicos/admin
        if any(path.startswith(prefix) for prefix in _PUBLIC_PREFIXES):
            return await call_next(request)

        # Extrair token do header Authorization
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            # Sem token — deixa o auth handler normal lidar
            return await call_next(request)

        token = auth_header[7:]
        tenant_slug = self._extract_tenant_slug(token)

        if not tenant_slug:
            return await call_next(request)

        # Verificar se tem role PLATFORM_ADMIN — nunca bloquear
        roles = self._extract_roles(token)
        if "PLATFORM_ADMIN" in roles:
            return await call_next(request)

        # Consultar status do tenant
        is_active = await self._is_tenant_active(tenant_slug)
        if not is_active:
            logger.warning("Tenant guard bloqueou request: tenant '%s' suspenso", tenant_slug)
            return JSONResponse(
                status_code=403,
                content={
                    "error": "tenant_suspended",
                    "detail": "Tenant suspenso. Contacte o administrador da plataforma.",
                },
            )

        return await call_next(request)

    @staticmethod
    def _extract_tenant_slug(token: str) -> str | None:
        """Extrai tenant_id do JWT sem validar assinatura (já validada depois)."""
        try:
            payload = jose_jwt.get_unverified_claims(token)
            return payload.get("tenant_id") or payload.get("azp")
        except (JWTError, Exception):
            return None

    @staticmethod
    def _extract_roles(token: str) -> list[str]:
        """Extrai roles do JWT sem validar assinatura."""
        try:
            payload = jose_jwt.get_unverified_claims(token)
            return payload.get("realm_access", {}).get("roles", [])
        except (JWTError, Exception):
            return []

    @staticmethod
    async def _is_tenant_active(slug: str) -> bool:
        """Consulta status do tenant no banco."""
        from intellicare_core.db.session import get_engine

        try:
            async with get_engine().connect() as conn:
                row = (
                    await conn.execute(
                        text("SELECT status FROM public.tenants WHERE slug = :slug AND deleted_at IS NULL"),
                        {"slug": slug},
                    )
                ).mappings().first()
            return row is not None and row["status"] == "active"
        except Exception:
            logger.exception("Erro ao verificar status do tenant '%s'", slug)
            # Em caso de erro de DB, permitir passagem (fail-open para não derrubar tudo)
            return True
