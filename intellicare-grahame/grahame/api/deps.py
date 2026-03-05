"""Dependências FastAPI do Grahame."""

from typing import Any
import os
from dataclasses import dataclass
from fastapi import Request, Depends
from sqlalchemy import text
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from redis.asyncio import Redis

from fastapi.security import OAuth2PasswordBearer
from grahame.api.auth import get_tenant_context

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# Note: assuming intellicare_auth and intellicare_core are available in environment
try:
    from intellicare_auth.policy_resolver import PolicyResolver
    from intellicare_core.access.policy_evaluator import PolicyEvaluator
    from intellicare_auth.fastapi.middleware import verify_token
except ImportError:
    # Stub verifier if auth module isn't strictly present
    async def verify_token(token: str) -> dict:
        return {}
    pass

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
        
    evaluator = PolicyEvaluator()

    # Feature flag to enable/disable policy enforcement in production
    enforce = os.getenv("ENFORCE_ACCESS_POLICIES", "false").lower() == "true"
    if not enforce:
        return PolicyContext(
            user_id=user_id, 
            tenant_id=tenant_id, 
            policy={"is_admin": True, "resource_rules": []}, 
            evaluator=evaluator
        )

    resolver = PolicyResolver(session, redis)
    policy = await resolver.resolve(tenant_id, user_id)
    
    return PolicyContext(
        user_id=user_id, 
        tenant_id=tenant_id, 
        policy=policy, 
        evaluator=evaluator
    )
