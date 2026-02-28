"""Base de dados para Geralda - SQLAlchemy setup."""

from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(AsyncAttrs, DeclarativeBase):
    """Base declarativa para modelos SQLAlchemy."""

    pass


def get_engine(database_url: str):
    """
    Cria engine assíncrono SQLAlchemy.

    Args:
        database_url: URL do banco (ex: postgresql+asyncpg://...)

    Returns:
        AsyncEngine
    """
    return create_async_engine(
        database_url,
        echo=False,  # Set True para debug SQL
        pool_pre_ping=True,  # Verificar conexões antes de usar
        pool_size=10,
        max_overflow=20,
    )


def get_session_factory(engine):
    """
    Cria fábrica de sessões assíncronas.

    Args:
        engine: SQLAlchemy AsyncEngine

    Returns:
        sessionmaker assíncrono
    """
    return sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Evitar lazy loading após commit
        autocommit=False,
        autoflush=False,
    )
