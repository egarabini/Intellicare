"""Alembic migration environment — WANDA v2.0 (Fase 1)."""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import Wanda models so Alembic can autogenerate migrations
from wanda.database.models import Base  # noqa: F401 — registers all models

# Alembic Config object
config = context.config

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLAlchemy metadata for autogenerate
target_metadata = Base.metadata

# Database URL from environment (overrides alembic.ini)
_db_url = os.environ.get(
    "INTELLICARE_DATABASE_URL",
    "postgresql+asyncpg://wanda:wanda@localhost:5432/intellicare",
)
config.set_main_option("sqlalchemy.url", _db_url)

# Schema for all Wanda tables
_schema = os.environ.get("INTELLICARE_DATABASE_SCHEMA", "wanda")


def include_object(object, name, type_, reflected, compare_to):
    """Only migrate objects in the wanda schema."""
    if type_ == "table":
        return object.schema == _schema or object.schema is None
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection, just SQL output)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        version_table_schema=_schema,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations with the given DB connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table_schema=_schema,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations using asyncpg engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Create schema if it doesn't exist
        await connection.execute(
            __import__("sqlalchemy").text(f"CREATE SCHEMA IF NOT EXISTS {_schema}")
        )
        await connection.commit()

        # Set search_path to wanda schema
        await connection.execute(
            __import__("sqlalchemy").text(f"SET search_path TO {_schema}, public")
        )

        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connected to DB)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
