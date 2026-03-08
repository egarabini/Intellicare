"""
Dependency injection for FastAPI routes.

Provides reusable dependencies for database sessions, authentication, etc.
"""


from typing import AsyncGenerator, Any
from intellicare_auth import get_tenant_context
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.database import get_session


# Database session dependency
async def get_db(
    ctx: Any = Depends(get_tenant_context)
) -> AsyncGenerator[AsyncSession, None]:
    """Tenant-isolated database session."""
    async for session in get_session(ctx):
        yield session

