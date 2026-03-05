"""Database session block for intellicare-admin."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import Request
from admin.config import AdminConfig

config = AdminConfig()

# In production, this uses config.database_url
engine = create_async_engine(
    config.database_url or "sqlite+aiosqlite:///:memory:", 
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db(request: Request) -> AsyncSession:
    """FastAPI Dependency for DB Session."""
    # Attempt to use app state if initialized in lifespan, otherwise fallback
    try:
        factory = request.app.state.session_factory
        async with factory() as session:
            yield session
    except AttributeError:
        # Fallback for scripts/tests
        async with AsyncSessionLocal() as session:
            yield session
