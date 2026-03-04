"""
Dependency injection for FastAPI routes.

Provides reusable dependencies for database sessions, authentication, etc.
"""


from typing import AsyncGenerator, Any
from donabedian.api.auth import get_tenant_context, check_module_active
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.database import get_session


# Database session dependency
async def get_db(
    ctx: Any = Depends(get_tenant_context),
    _check: Any = Depends(check_module_active('intellicare-donabedian'))
) -> AsyncGenerator[AsyncSession, None]:
    """Tenant-isolated database session."""
    async for session in get_session(ctx):
        yield session

