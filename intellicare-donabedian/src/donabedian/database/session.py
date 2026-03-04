"""
Database session management for intellicare-donabedian.

Provides async SQLAlchemy session factory and dependency injection
for FastAPI routes.
"""

from typing import AsyncGenerator, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)

from donabedian.config import settings


# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.intellicare_database_url,
    echo=settings.is_development,  # Log SQL queries in development
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session(ctx: Any = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI routes to get a tenant-aware database session.
    """
    tenant_schema = ctx.schema_name if ctx and hasattr(ctx, "schema_name") else "public"
    
    async with AsyncSessionLocal() as session:
        try:
            if "postgresql" in settings.intellicare_database_url:
                await session.execute(text(f"SET search_path TO {tenant_schema}"))
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            if "postgresql" in settings.intellicare_database_url:
                await session.execute(text("SET search_path TO public"))
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    This is useful for testing or initial setup.
    In production, use Alembic migrations instead.
    """
    from donabedian.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This will delete all data!
    Only use in testing or development.
    """
    from donabedian.models import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

