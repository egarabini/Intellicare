"""Dependências de banco para FastAPI routes."""

from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency que fornece uma sessão de banco de dados.

    Uso em FastAPI routes:
        @app.get("/plans")
        async def list_plans(db: AsyncSession = Depends(get_db)):
            ...

    Args:
        request: FastAPI Request (contém app.state.session_factory)

    Yields:
        AsyncSession: Sessão do banco de dados
    """
    async with request.app.state.session_factory() as session:
        yield session
