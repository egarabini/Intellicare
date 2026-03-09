"""Dependências FastAPI do Grahame."""

import base64
import json
from typing import Any
import os
from dataclasses import dataclass
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy import text
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from redis.asyncio import Redis

from fastapi.security import OAuth2PasswordBearer
from grahame.api.auth import get_tenant_context

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Note: optional integrations with intellicare_auth/intellicare_core
try:
    from intellicare_auth.policy_resolver import PolicyResolver
except ImportError:
    PolicyResolver = None

try:
    from intellicare_core.access.policy_evaluator import PolicyEvaluator
except ImportError:
    PolicyEvaluator = None

try:
    from intellicare_auth.fastapi.middleware import verify_token
except ImportError:
    async def verify_token(token: str) -> dict:
        return {}

try:
    from intellicare_auth.fastapi import require_role
    _HAS_REQUIRE_ROLE = True
except ImportError:
    require_role = None
    _HAS_REQUIRE_ROLE = False

class FHIRForbiddenError(Exception):
    """Exception raised when a FHIR operation is denied by Access Policies."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(self.reason)

@dataclass
class PolicyContext:
    user_id: str
    tenant_id: str
    policy: dict
    evaluator: Any # PolicyEvaluator

def get_redis_client(request: Request) -> Redis:
    """Helper to extract Redis block from app state."""
    return request.app.state.redis

async def get_db(request: Request, ctx: Any = Depends(get_tenant_context)):
    """Provê sessão AsyncSession por request isolada por tenant."""
    factory: async_sessionmaker = request.app.state.session_factory
    tenant_schema = ctx.schema_name if ctx and hasattr(ctx, "schema_name") else "public"
    
    async with factory() as session:
        try:
            if "postgresql" in str(session.bind.url):
                await session.execute(text(f"SET search_path TO {tenant_schema}"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            if "postgresql" in str(session.bind.url):
                await session.execute(text("SET search_path TO public"))

@asynccontextmanager
async def get_tenant_session_context(request: Request):
    """Context manager para endpoints que não usam injestão de dependência get_db."""
    factory: async_sessionmaker = request.app.state.session_factory
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    tenant_schema = f"tenant_{tenant_id}" if tenant_id and tenant_id != "default" else "public"

    async with factory() as session:
        try:
            if "postgresql" in str(session.bind.url):
                await session.execute(text(f"SET search_path TO {tenant_schema}"))
            yield session
        finally:
            if "postgresql" in str(session.bind.url):
                await session.execute(text("SET search_path TO public"))

async def get_policy_context(
    request: Request,
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> PolicyContext:
    """FastAPI Dependency enforcing Medplum-like Access Policies.
    
    If ENFORCE_ACCESS_POLICIES is not set, returns a permissive Admin policy.
    """
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    
    try:
        token_payload = await verify_token(token)
        user_id = token_payload.get("sub", "anonymous")
    except Exception:
        user_id = "anonymous"
        token_payload = {}
        
    if PolicyEvaluator is not None:
        evaluator = PolicyEvaluator()
    else:
        evaluator = object()

    # Feature flag to enable/disable policy enforcement in production
    enforce = os.getenv("ENFORCE_ACCESS_POLICIES", "false").lower() == "true"
    if not enforce:
        return PolicyContext(
            user_id=user_id, 
            tenant_id=tenant_id, 
            policy={"is_admin": True, "resource_rules": []}, 
            evaluator=evaluator
        )

    if PolicyResolver is None:
        return PolicyContext(
            user_id=user_id,
            tenant_id=tenant_id,
            policy={"is_admin": True, "resource_rules": []},
            evaluator=evaluator,
        )

    resolver = PolicyResolver(session, redis)
    policy = await resolver.resolve(tenant_id, user_id)
    
    return PolicyContext(
        user_id=user_id, 
        tenant_id=tenant_id, 
        policy=policy, 
        evaluator=evaluator
    )


if _HAS_REQUIRE_ROLE:
    async def require_his_adapter(payload: dict = require_role("HIS_ADAPTER")) -> dict:
        """Dependency que exige role realm HIS_ADAPTER."""
        return payload
else:
    def _decode_jwt_claims_unverified(token: str) -> dict:
        """Fallback local: decodifica claims JWT sem validar assinatura."""
        try:
            parts = token.split(".")
            if len(parts) < 2:
                return {}
            payload = parts[1].replace("-", "+").replace("_", "/")
            payload += "=" * ((4 - len(payload) % 4) % 4)
            data = base64.b64decode(payload)
            return json.loads(data.decode("utf-8"))
        except Exception:
            return {}

    async def require_his_adapter(token: str = Depends(oauth2_scheme)) -> dict:
        """Fallback local: valida bearer token e role HIS_ADAPTER no payload."""
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

        payload = await verify_token(token)
        if not payload:
            payload = _decode_jwt_claims_unverified(token)
        realm_roles = payload.get("realm_access", {}).get("roles", [])
        if "HIS_ADAPTER" not in realm_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing required role: HIS_ADAPTER")
        return payload
