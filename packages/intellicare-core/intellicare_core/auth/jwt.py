"""
Validacao de JWT emitido pelo Keycloak.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Annotated, Any

import httpx
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwk, jwt
from sqlalchemy import text

from intellicare_core.config.settings import get_settings
from intellicare_core.contracts.base import TenantContext
from intellicare_core.contracts.errors import api_error

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=True)


@lru_cache(maxsize=1)
def _get_jwks() -> dict[str, Any]:
    settings = get_settings()
    response = httpx.get(settings.keycloak_jwks_url, timeout=10.0)
    response.raise_for_status()
    return response.json()


def _refresh_jwks() -> dict[str, Any]:
    _get_jwks.cache_clear()
    return _get_jwks()


def _decode_with_jwks(token: str, jwks: dict[str, Any]) -> dict[str, Any]:
    headers = jwt.get_unverified_header(token)
    kid = headers.get("kid")
    if not kid:
        raise JWTError("missing kid")

    for key_dict in jwks.get("keys", []):
        if key_dict.get("kid") != kid:
            continue

        public_key = jwk.construct(key_dict)
        return jwt.decode(
            token,
            public_key.to_pem().decode(),
            algorithms=[key_dict.get("alg", "RS256")],
            options={"verify_aud": False},
        )

    raise JWTError("matching jwk not found")


async def verify_token(token: str) -> TenantContext:
    try:
        payload = _decode_with_jwks(token, _get_jwks())
    except (JWTError, httpx.HTTPError):
        try:
            payload = _decode_with_jwks(token, _refresh_jwks())
        except (JWTError, httpx.HTTPError) as exc:
            raise api_error(401, "invalid_token", "Token JWT invalido ou expirado") from exc

    tenant_id = payload.get("tenant_id") or payload.get("azp")
    user_id = payload.get("sub", "")
    email = payload.get("email", "")
    roles = payload.get("realm_access", {}).get("roles", [])

    if not tenant_id:
        raise api_error(401, "missing_tenant", "Token nao contem tenant_id")

    return TenantContext.from_slug(
        slug=tenant_id,
        user_id=user_id,
        roles=list(roles),
        email=email,
    )


async def _check_tenant_active(ctx: TenantContext) -> None:
    """Verifica se o tenant esta ativo no banco. Bloqueia suspensos/inativos."""
    # Platform admin nao esta vinculado a tenant — skip
    if ctx.has_role("PLATFORM_ADMIN"):
        return

    from intellicare_core.db.session import get_engine

    async with get_engine().connect() as conn:
        row = (await conn.execute(
            text("SELECT status FROM public.tenants WHERE slug = :slug"),
            {"slug": ctx.tenant_id},
        )).mappings().first()

    if not row or row["status"] != "active":
        logger.warning(
            "Acesso bloqueado: tenant '%s' com status '%s'",
            ctx.tenant_id,
            row["status"] if row else "nao_encontrado",
        )
        raise api_error(403, "tenant_inactive", "Tenant suspenso ou inativo")


async def get_current_tenant(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> TenantContext:
    ctx = await verify_token(token)
    await _check_tenant_active(ctx)
    return ctx


def require_role(role: str):
    async def _check(ctx: Annotated[TenantContext, Depends(get_current_tenant)]) -> TenantContext:
        if not ctx.has_role(role):
            raise api_error(403, "forbidden", f"Role '{role}' necessaria")
        return ctx

    return _check
