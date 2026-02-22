"""SQLAlchemy declarative base para o módulo de comunicação."""

from __future__ import annotations

try:
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        """Base declarativa compartilhada para todos os modelos ORM do módulo."""
        pass

except ImportError:  # pragma: no cover
    Base = object  # type: ignore[assignment,misc]

__all__ = ["Base"]
