"""
Database module for intellicare-donabedian.

Exports:
- engine: Async SQLAlchemy engine
- AsyncSessionLocal: Async session factory
- get_session: FastAPI dependency for database sessions
- init_db: Initialize database tables
- drop_db: Drop all database tables
"""

from donabedian.database.session import (
    engine,
    AsyncSessionLocal,
    get_session,
    init_db,
    drop_db,
)

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_session",
    "init_db",
    "drop_db",
]
