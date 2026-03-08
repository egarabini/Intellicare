"""Persistencia de vinculos paciente->sala para o modulo de comunicacao."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import AsyncGenerator, Protocol

from contextlib import contextmanager
from typing import Any

@contextmanager
def get_tenant_conn(engine, ctx: Any = None):
    schema = ctx.schema_name if ctx and hasattr(ctx, "schema_name") else "public"
    with engine.begin() as conn:
        if "postgresql" in str(engine.url):
            from sqlalchemy import text
            conn.execute(text(f"SET search_path TO {schema}"))
        yield conn

try:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    _ASYNC_SQLALCHEMY_AVAILABLE = True
except ImportError:
    _ASYNC_SQLALCHEMY_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI dependency — async DB session
# ---------------------------------------------------------------------------

_async_session_factory: "async_sessionmaker[AsyncSession] | None" = None


def _get_or_create_session_factory() -> "async_sessionmaker[AsyncSession] | None":
    """Lazy-creates the async session factory on first call."""
    global _async_session_factory
    if _async_session_factory is not None:
        return _async_session_factory
    if not _ASYNC_SQLALCHEMY_AVAILABLE:
        return None
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        return None
    # Convert sync URL to async (postgres → postgresql+asyncpg)
    async_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(async_url, pool_pre_ping=True)
    _async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _async_session_factory


async def get_db_session() -> "AsyncGenerator[AsyncSession | None, None]":
    """FastAPI dependency that yields an async SQLAlchemy session.

    Yields None when DATABASE_URL is not configured (development/testing).
    """
    factory = _get_or_create_session_factory()
    if factory is None:
        yield None  # type: ignore[misc]
        return
    async with factory() as session:
        yield session

try:
    from sqlalchemy import Column, MetaData, String, Table, create_engine, select, text
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.engine import Engine
except ImportError:  # pragma: no cover - fallback para ambiente sem sqlalchemy
    MetaData = None  # type: ignore[assignment]
    String = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    Column = None  # type: ignore[assignment]
    create_engine = None  # type: ignore[assignment]
    select = None  # type: ignore[assignment]
    text = None  # type: ignore[assignment]
    pg_insert = None  # type: ignore[assignment]
    Engine = object  # type: ignore[assignment]


class PatientRoomRepository(Protocol):
    def upsert_link(self, patient_id: str, room_id: str, ctx: Any = None) -> None: ...

    def get_room_id(self, patient_id: str, ctx: Any = None) -> str | None: ...

    def list_links(self, limit: int, offset: int, ctx: Any = None) -> list[dict[str, str]]: ...

    def delete_link(self, patient_id: str, ctx: Any = None) -> bool: ...

    def close(self) -> None: ...


@dataclass
class InMemoryPatientRoomRepository:
    """Repositorio em memoria para desenvolvimento/testes."""

    links: dict[str, str]

    def upsert_link(self, patient_id: str, room_id: str, ctx: Any = None) -> None:
        self.links[patient_id] = room_id

    def get_room_id(self, patient_id: str, ctx: Any = None) -> str | None:
        return self.links.get(patient_id)

    def list_links(self, limit: int, offset: int, ctx: Any = None) -> list[dict[str, str]]:
        items = sorted(self.links.items(), key=lambda x: x[0])
        page = items[offset : offset + limit]
        return [{"patient_id": patient_id, "room_id": room_id} for patient_id, room_id in page]

    def delete_link(self, patient_id: str, ctx: Any = None) -> bool:
        if patient_id not in self.links:
            return False
        del self.links[patient_id]
        return True

    def close(self) -> None:
        return


class PostgresPatientRoomRepository:
    """Repositorio em Postgres com schema dedicado do modulo."""

    def __init__(self, database_url: str, schema: str) -> None:
        if create_engine is None:
            raise RuntimeError("sqlalchemy nao instalado. Instale as dependencias do modulo.")
        self.schema = schema
        self.engine: Engine = create_engine(database_url, future=True, pool_pre_ping=True)
        self.metadata = MetaData(schema=schema)
        self.patient_room_links = Table(
            "patient_room_links",
            self.metadata,
            Column("patient_id", String(120), primary_key=True),
            Column("room_id", String(255), nullable=False),
        )
        self._ensure_schema_and_table()

    def _ensure_schema_and_table(self) -> None:
        with get_tenant_conn(self.engine, ctx) as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self.schema}"))
        self.metadata.create_all(self.engine)

    def upsert_link(self, patient_id: str, room_id: str, ctx: Any = None) -> None:
        stmt = pg_insert(self.patient_room_links).values(patient_id=patient_id, room_id=room_id)
        stmt = stmt.on_conflict_do_update(
            index_elements=[self.patient_room_links.c.patient_id],
            set_={"room_id": room_id},
        )
        with get_tenant_conn(self.engine, ctx) as conn:
            conn.execute(stmt)

    def get_room_id(self, patient_id: str, ctx: Any = None) -> str | None:
        stmt = select(self.patient_room_links.c.room_id).where(self.patient_room_links.c.patient_id == patient_id)
        with get_tenant_conn(self.engine, ctx) as conn:
            room_id = conn.execute(stmt).scalar_one_or_none()
        return room_id

    def list_links(self, limit: int, offset: int, ctx: Any = None) -> list[dict[str, str]]:
        stmt = (
            select(self.patient_room_links.c.patient_id, self.patient_room_links.c.room_id)
            .order_by(self.patient_room_links.c.patient_id.asc())
            .limit(limit)
            .offset(offset)
        )
        with get_tenant_conn(self.engine, ctx) as conn:
            rows = conn.execute(stmt).all()
        return [{"patient_id": row.patient_id, "room_id": row.room_id} for row in rows]

    def delete_link(self, patient_id: str, ctx: Any = None) -> bool:
        stmt = self.patient_room_links.delete().where(self.patient_room_links.c.patient_id == patient_id)
        with get_tenant_conn(self.engine, ctx) as conn:
            result = conn.execute(stmt)
        return result.rowcount > 0

    def close(self) -> None:
        self.engine.dispose()


def build_patient_room_repository(database_url: str, schema: str) -> PatientRoomRepository:
    if not database_url:
        logger.warning("DATABASE_URL vazio; usando repositorio em memoria para patient-room links")
        return InMemoryPatientRoomRepository(links={})
    if create_engine is None:
        logger.warning("sqlalchemy indisponivel; usando repositorio em memoria para patient-room links")
        return InMemoryPatientRoomRepository(links={})
    return PostgresPatientRoomRepository(database_url=database_url, schema=schema)
