"""Dependências FastAPI do Grahame."""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_db(request: Request):
    """Provê sessão AsyncSession por request."""
    factory: async_sessionmaker = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
