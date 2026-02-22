"""Persistencia de templates (Postgres + fallback)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from comunicacao.templates.models import MessageTemplate
from comunicacao.templates.store import InMemoryTemplateStore, TemplateStore

try:
    from sqlalchemy import JSON, BOOLEAN, INTEGER, TIMESTAMP, Column, MetaData, String, Table, Text, create_engine, select
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.engine import Engine
except ImportError:  # pragma: no cover
    JSON = None  # type: ignore[assignment]
    BOOLEAN = None  # type: ignore[assignment]
    INTEGER = None  # type: ignore[assignment]
    TIMESTAMP = None  # type: ignore[assignment]
    Column = None  # type: ignore[assignment]
    MetaData = None  # type: ignore[assignment]
    String = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    Text = None  # type: ignore[assignment]
    create_engine = None  # type: ignore[assignment]
    select = None  # type: ignore[assignment]
    pg_insert = None  # type: ignore[assignment]
    Engine = object  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class PostgresTemplateStore:
    def __init__(self, database_url: str, schema: str) -> None:
        if create_engine is None or pg_insert is None:
            raise RuntimeError("sqlalchemy nao instalado.")
        self.engine: Engine = create_engine(database_url, future=True, pool_pre_ping=True)
        metadata = MetaData(schema=schema)
        self.table = Table(
            "message_templates",
            metadata,
            Column("id", String(100), primary_key=True),
            Column("name", String(200), nullable=False),
            Column("description", Text, nullable=True),
            Column("category", String(60), nullable=False),
            Column("version", INTEGER, nullable=False),
            Column("channel_variants", JSON, nullable=False),
            Column("params_schema", JSON, nullable=False),
            Column("sample_params", JSON, nullable=True),
            Column("active", BOOLEAN, nullable=False),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        )

    def create(self, item: MessageTemplate) -> MessageTemplate:
        stmt = pg_insert(self.table).values(**self._to_row(item))
        with self.engine.begin() as conn:
            conn.execute(stmt)
        return item

    def get(self, template_id: str) -> MessageTemplate | None:
        stmt = select(self.table).where(self.table.c.id == template_id)
        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().first()
        if row is None:
            return None
        return MessageTemplate.model_validate(dict(row))

    def list(self) -> list[MessageTemplate]:
        stmt = select(self.table).order_by(self.table.c.id.asc())
        with self.engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        return [MessageTemplate.model_validate(dict(row)) for row in rows]

    def update(self, template_id: str, item: MessageTemplate) -> MessageTemplate | None:
        existing = self.get(template_id)
        if existing is None:
            return None
        item.version = existing.version + 1
        item.created_at = existing.created_at
        item.updated_at = datetime.now(UTC)
        stmt = (
            self.table.update()
            .where(self.table.c.id == template_id)
            .values(**self._to_row(item))
        )
        with self.engine.begin() as conn:
            conn.execute(stmt)
        return item

    def deactivate(self, template_id: str) -> MessageTemplate | None:
        existing = self.get(template_id)
        if existing is None:
            return None
        existing.active = False
        existing.updated_at = datetime.now(UTC)
        stmt = (
            self.table.update()
            .where(self.table.c.id == template_id)
            .values(active=False, updated_at=existing.updated_at)
        )
        with self.engine.begin() as conn:
            conn.execute(stmt)
        return existing

    @staticmethod
    def _to_row(item: MessageTemplate) -> dict[str, object]:
        payload = item.model_dump(mode="json")
        return {
            "id": payload["id"],
            "name": payload["name"],
            "description": payload.get("description"),
            "category": payload["category"],
            "version": int(payload["version"]),
            "channel_variants": payload.get("channel_variants", {}),
            "params_schema": payload.get("params_schema", {}),
            "sample_params": payload.get("sample_params", {}),
            "active": bool(payload.get("active", True)),
            "created_at": datetime.fromisoformat(payload["created_at"].replace("Z", "+00:00")).astimezone(UTC),
            "updated_at": datetime.fromisoformat(payload["updated_at"].replace("Z", "+00:00")).astimezone(UTC),
        }


def build_template_store(database_url: str, schema: str) -> TemplateStore:
    if not database_url:
        return InMemoryTemplateStore()
    if create_engine is None:
        return InMemoryTemplateStore()
    try:
        return PostgresTemplateStore(database_url=database_url, schema=schema)
    except Exception as exc:  # pragma: no cover
        logger.warning("Falha ao inicializar PostgresTemplateStore (%s); fallback memoria", exc)
        return InMemoryTemplateStore()

