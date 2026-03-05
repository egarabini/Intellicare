"""Database package for intellicare-admin."""

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """SQLAlchemy Declarative Base for all admin models."""
    pass
