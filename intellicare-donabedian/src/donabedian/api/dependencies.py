"""
Dependency injection for FastAPI routes.

Provides reusable dependencies for database sessions, authentication, etc.
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.database import get_session


# Database session dependency (re-export for convenience)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for FastAPI routes.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    
    Yields:
        AsyncSession: Database session
    """
    async for session in get_session():
        yield session

