"""Database session block for intellicare-admin."""

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from admin.config import AdminConfig
from intellicare_core.tenant import TenantAwareSessionFactory

config = AdminConfig()

session_factory = TenantAwareSessionFactory(
    config.database_url or "sqlite+aiosqlite:///:memory:",
    echo=False,
)

async def get_db(request: Request) -> AsyncSession:
    """FastAPI Dependency for DB Session."""
    # Attempt to use app state if initialized in lifespan, otherwise fallback
    try:
        factory = request.app.state.session_factory
        async with await factory.get_platform_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except AttributeError:
        # Fallback for scripts/tests
        async with await session_factory.get_platform_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
