"""FastAPI dependency injection for admin module."""

from typing import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from admin.services.tenant_service import TenantService
from admin.services.provisioning_service import ProvisioningService


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Get database session from app state."""
    async with request.app.state.sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_tenant_service(session: AsyncSession = Depends(get_session)) -> TenantService:
    """Inject TenantService with session."""
    return TenantService(session=session)


async def get_provisioning_service(
    session: AsyncSession = Depends(get_session),
    request: Request = None,
) -> ProvisioningService:
    """Inject ProvisioningService with session + optional Keycloak admin."""
    kc_admin = getattr(request.app.state, "kc_admin", None) if request else None
    return ProvisioningService(
        session=session,
        keycloak_admin=kc_admin,
    )


async def get_actor_id(request: Request) -> str:
    """Extract actor ID from request (JWT or fallback to anonymous).

    Uses intellicare_auth if available.
    """
    try:
        from intellicare_auth import get_current_user
        user = await get_current_user(request)
        return f"admin:{user.get('sub', 'unknown')}"
    except (ImportError, Exception):
        return "admin:system"
