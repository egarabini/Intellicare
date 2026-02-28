"""HL7v2 Authentication Dependencies — Validação de API Keys.

Este módulo fornece dependencies FastAPI para autenticação de requisições HL7v2
usando API Keys no header X-API-Key.

Features:
- Validação de API Key
- Verificação de expiração
- IP whitelist
- Rate limiting (básico)
- Auditoria automática
"""

import logging
import inspect
import time
from typing import Optional, Annotated

from fastapi import Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.hl7v2_api_key import HL7v2APIKey
from grahame.models.hl7v2_audit import HL7v2AuditLog
from grahame.services.rate_limiter import RateLimiter, RateLimitExceeded

logger = logging.getLogger(__name__)


# Cache simples para API Keys (evita consultas repetidas ao DB)
_api_key_cache: dict[str, tuple[HL7v2APIKey, float]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutos


async def get_db_session(request: Request):
    """Get database session from app state.

    Args:
        request: FastAPI request

    Yields:
        AsyncSession: Database session
    """
    session_factory = getattr(request.app.state, "session_factory", None)
    if session_factory is None:
        from grahame.models.base import Base
        from grahame.models import (  # noqa: F401
            HL7v2APIKey,
            HL7v2AuditLog,
        )
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        request.app.state.session_factory = session_factory
    async with session_factory() as session:
        yield session


async def _resolve_db_session(request: Request):
    """Resolve DB session dynamically and compatibly with test patches."""
    provider = get_db_session
    try:
        result = provider(request)
    except TypeError:
        result = provider()

    if inspect.isasyncgen(result):
        session = await anext(result)
        return session, result

    if inspect.isawaitable(result):
        return await result, None

    return result, None


async def validate_hl7v2_api_key(
    request: Request,
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> HL7v2APIKey:
    """Validate HL7v2 API Key from X-API-Key header.
    
    Args:
        request: FastAPI request
        x_api_key: API Key from X-API-Key header
        db: Database session
    
    Returns:
        HL7v2APIKey: Validated API Key object
    
    Raises:
        HTTPException: 401 if API Key is missing or invalid
        HTTPException: 403 if IP is not whitelisted
    """
    # Check if API Key is provided
    if not x_api_key:
        logger.warning("Missing X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check cache first
    cached = _api_key_cache.get(x_api_key)
    if cached:
        api_key_obj, cached_at = cached
        if time.time() - cached_at < _CACHE_TTL_SECONDS:
            # Cache hit - validate again (in case it was disabled)
            if api_key_obj.is_valid():
                # Check IP whitelist
                client_ip = request.client.host if request.client else "unknown"
                if not api_key_obj.is_ip_allowed(client_ip):
                    logger.warning(
                        f"IP not whitelisted: {client_ip} for API Key {api_key_obj.system_identifier}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"IP {client_ip} is not whitelisted for this API Key",
                    )
                
                return api_key_obj
    
    db = None
    db_gen = None
    try:
        db, db_gen = await _resolve_db_session(request)

        # Cache miss - query database
        stmt = select(HL7v2APIKey).where(HL7v2APIKey.api_key == x_api_key)
        result = await db.execute(stmt)
        api_key_obj = result.scalar_one_or_none()
        if inspect.isawaitable(api_key_obj):
            api_key_obj = await api_key_obj
    finally:
        if db_gen is not None:
            await db_gen.aclose()

    if not api_key_obj:
        logger.warning(f"Invalid API Key: {x_api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate API Key
    if not api_key_obj.is_valid():
        logger.warning(
            f"API Key is inactive or expired: {api_key_obj.system_identifier}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key is inactive or expired",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check IP whitelist
    client_ip = request.client.host if request.client else "unknown"
    if not api_key_obj.is_ip_allowed(client_ip):
        logger.warning(
            f"IP not whitelisted: {client_ip} for API Key {api_key_obj.system_identifier}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"IP {client_ip} is not whitelisted for this API Key",
        )
    
    # Update cache
    _api_key_cache[x_api_key] = (api_key_obj, time.time())
    
    logger.info(
        f"API Key validated: {api_key_obj.system_identifier} from IP {client_ip}"
    )
    
    return api_key_obj


async def update_api_key_usage(
    api_key: HL7v2APIKey,
    db: AsyncSession,
) -> None:
    """Update API Key usage statistics.

    Args:
        api_key: API Key object
        db: Database session
    """
    from datetime import datetime, timezone

    api_key.last_used_at = datetime.now(timezone.utc)
    api_key.usage_count += 1

    await db.commit()


async def check_rate_limit(
    request: Request,
    api_key: HL7v2APIKey,
) -> None:
    """Check rate limit for API Key.

    Args:
        request: FastAPI request
        api_key: API Key object

    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Skip if no rate limit configured
    if api_key.rate_limit_per_minute <= 0:
        return

    # Get rate limiter from app state
    if not hasattr(request.app.state, "rate_limiter"):
        logger.warning("Rate limiter not initialized in app state")
        return

    rate_limiter: RateLimiter = request.app.state.rate_limiter

    # Check rate limit
    key = f"api_key:{api_key.id}"
    try:
        allowed, current, limit, reset_time = await rate_limiter.check_rate_limit(
            key=key,
            limit=api_key.rate_limit_per_minute,
            window_seconds=60,
        )
    except Exception as exc:
        logger.warning(f"rate_limiter.runtime_failed: {exc}")
        return

    if not allowed:
        # Add rate limit headers
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} requests per minute.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(60),  # Retry after 60 seconds
            },
        )

    # Add rate limit headers to response (will be added by middleware)
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(limit - current - 1),  # -1 for current request
        "X-RateLimit-Reset": str(reset_time),
    }
