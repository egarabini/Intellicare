"""Alembic environment configuration."""

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import text
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models for autogenerate
from src.oswaldo.models.oswaldo_models import Base

# Get database configuration
DB_USER = os.getenv("OSWALDO_DB_USER", "admin_intellicare")
DB_PASSWORD = os.getenv("OSWALDO_DB_PASSWORD", "Crazy#57LB")
DB_HOST = os.getenv("OSWALDO_DB_HOST", "161.97.141.186")
DB_PORT = os.getenv("OSWALDO_DB_PORT", "5432")
DB_NAME = os.getenv("OSWALDO_DB_NAME", "intellicareDB")
DB_SCHEMA = os.getenv("OSWALDO_DB_SCHEMA", "oswaldo")

# this is the Alembic Config object
config = context.config

# Setup logging
logger = logging.getLogger('alembic.env')

# Set target metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    
    url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Create schema if not exists
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}"))
        connection.commit()
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            version_table_schema=DB_SCHEMA,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

