"""Persistencia de roteamento (Postgres + fallback em memoria)."""

from __future__ import annotations
from comunicacao.storage.tenant_utils import get_tenant_conn

import logging
from datetime import UTC, datetime

from comunicacao.routing.models import CommunicationIntentRecord, DeliveryResultRecord
from comunicacao.routing.store import InMemoryRoutingStore, RoutingStore

try:
    from sqlalchemy import (
        JSON,
        Boolean,
        Integer,
        TIMESTAMP,
        Column,
        MetaData,
        String,
        Table,
        create_engine,
        insert,
        select,
        text,
    )
    from sqlalchemy.dialects.postgresql import UUID as PGUUID
    from sqlalchemy.engine import Engine
except ImportError:  # pragma: no cover - fallback para ambiente sem sqlalchemy
    MetaData = None  # type: ignore[assignment]
    String = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    Column = None  # type: ignore[assignment]
    create_engine = None  # type: ignore[assignment]
    select = None  # type: ignore[assignment]
    text = None  # type: ignore[assignment]
    insert = None  # type: ignore[assignment]
    JSON = None  # type: ignore[assignment]
    Boolean = None  # type: ignore[assignment]
    Integer = None  # type: ignore[assignment]
    TIMESTAMP = None  # type: ignore[assignment]
    PGUUID = None  # type: ignore[assignment]
    Engine = object  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class PostgresRoutingStore:
    """Store de roteamento em schema operacional dedicado."""

    def __init__(self, database_url: str, schema: str) -> None:
        if create_engine is None:
            raise RuntimeError("sqlalchemy nao instalado. Instale as dependencias do modulo.")
        self.schema = schema
        self.engine: Engine = create_engine(database_url, future=True, pool_pre_ping=True)
        self.metadata = MetaData(schema=schema)

        self.communication_intents = Table(
            "communication_intents",
            self.metadata,
            Column("id", PGUUID(as_uuid=True), primary_key=True),
            Column("source_module", String(120), nullable=False),
            Column("source_event_id", String(200), nullable=True),
            Column("recipient_type", String(40), nullable=False),
            Column("recipient_id", String(200), nullable=False),
            Column("severity", String(20), nullable=False),
            Column("category", String(60), nullable=False),
            # Conteúdo (template OU raw)
            Column("content_template_id", String(100), nullable=True),
            Column("content_params", JSON, nullable=True),
            Column("content_raw", String(), nullable=True),
            # Controle de entrega
            Column("correlation_id", String(200), nullable=False),
            Column("preferred_channel", String(30), nullable=True),
            Column("excluded_channels", JSON, nullable=False),
            Column("require_ack", Boolean, nullable=False),
            Column("max_attempts", Integer, nullable=False),
            # Agendamento
            Column("scheduled_at", TIMESTAMP(timezone=True), nullable=True),
            Column("expires_at", TIMESTAMP(timezone=True), nullable=True),
            # Escalonamento
            Column("parent_intent_id", PGUUID(as_uuid=True), nullable=True),
            # Metadados
            Column("metadata", JSON, nullable=False),
            # Controle interno
            Column("status", String(20), nullable=False),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
            Column("timeline", JSON, nullable=False),
        )
        self.delivery_results = Table(
            "delivery_results",
            self.metadata,
            Column("id", PGUUID(as_uuid=True), primary_key=True),
            Column("intent_id", PGUUID(as_uuid=True), nullable=False),
            Column("channel", String(30), nullable=False),
            Column("attempt_number", Integer, nullable=False),
            Column("status", String(20), nullable=False),
            Column("channel_message_id", String(300), nullable=True),
            Column("channel_room_id", String(300), nullable=True),
            Column("error_code", String(80), nullable=True),
            Column("error_message", String(), nullable=True),
            Column("timestamp", TIMESTAMP(timezone=True), nullable=False),
        )

    def save_intent(self, intent: CommunicationIntentRecord, ctx: Any = None) -> None:
        payload = intent.model_dump(mode="json")
        stmt = insert(self.communication_intents).values(
            id=payload["id"],
            source_module=payload["source_module"],
            source_event_id=payload.get("source_event_id"),
            recipient_type=payload["recipient_type"],
            recipient_id=payload["recipient_id"],
            severity=payload["severity"],
            category=payload["category"],
            # Conteúdo
            content_template_id=payload.get("content_template_id"),
            content_params=payload.get("content_params"),
            content_raw=payload.get("content_raw"),
            # Controle de entrega
            correlation_id=payload["correlation_id"],
            preferred_channel=payload.get("preferred_channel"),
            excluded_channels=payload.get("excluded_channels", []),
            require_ack=payload.get("require_ack", False),
            max_attempts=payload.get("max_attempts", 3),
            # Agendamento
            scheduled_at=self._parse_dt(payload.get("scheduled_at")) if payload.get("scheduled_at") else None,
            expires_at=self._parse_dt(payload.get("expires_at")) if payload.get("expires_at") else None,
            # Escalonamento
            parent_intent_id=payload.get("parent_intent_id"),
            # Metadados
            metadata=payload.get("metadata", {}),
            # Controle interno
            status=payload["status"],
            created_at=self._parse_dt(payload["created_at"]),
            updated_at=self._parse_dt(payload["updated_at"]),
            timeline=payload.get("timeline", []),
        )
        with get_tenant_conn(self.engine, ctx) as conn:
            conn.execute(stmt)

    def get_intent(self, intent_id: str, ctx: Any = None) -> CommunicationIntentRecord | None:
        stmt = select(self.communication_intents).where(self.communication_intents.c.id == intent_id)
        with get_tenant_conn(self.engine, ctx) as conn:
            row = conn.execute(stmt).mappings().first()
        if row is None:
            return None
        return CommunicationIntentRecord.model_validate(dict(row))

    def list_intents(self, ctx: Any = None) -> list[CommunicationIntentRecord]:
        stmt = select(self.communication_intents).order_by(self.communication_intents.c.created_at.desc())
        with get_tenant_conn(self.engine, ctx) as conn:
            rows = conn.execute(stmt).mappings().all()
        return [CommunicationIntentRecord.model_validate(dict(row)) for row in rows]

    def update_intent(self, intent: CommunicationIntentRecord, ctx: Any = None) -> None:
        payload = intent.model_dump(mode="json")
        stmt = (
            self.communication_intents.update()
            .where(self.communication_intents.c.id == payload["id"])
            .values(
                status=payload["status"],
                updated_at=self._parse_dt(payload["updated_at"]),
                timeline=payload.get("timeline", []),
            )
        )
        with get_tenant_conn(self.engine, ctx) as conn:
            conn.execute(stmt)

    def append_delivery(self, delivery: DeliveryResultRecord, ctx: Any = None) -> None:
        payload = delivery.model_dump(mode="json")
        stmt = insert(self.delivery_results).values(
            id=payload["id"],
            intent_id=payload["intent_id"],
            channel=payload["channel"],
            attempt_number=int(payload.get("attempt_number", 1)),
            status=payload["status"],
            channel_message_id=payload.get("channel_message_id"),
            channel_room_id=payload.get("channel_room_id"),
            error_code=payload.get("error_code"),
            error_message=payload.get("error_message"),
            timestamp=self._parse_dt(payload["timestamp"]),
        )
        with get_tenant_conn(self.engine, ctx) as conn:
            conn.execute(stmt)

    def get_deliveries(self, intent_id: str, ctx: Any = None) -> list[DeliveryResultRecord]:
        stmt = select(self.delivery_results).where(self.delivery_results.c.intent_id == intent_id)
        with get_tenant_conn(self.engine, ctx) as conn:
            rows = conn.execute(stmt).mappings().all()
        return [DeliveryResultRecord.model_validate(dict(row)) for row in rows]

    def find_by_source_event(self, source_module: str, source_event_id: str, ctx: Any = None) -> CommunicationIntentRecord | None:
        stmt = select(self.communication_intents).where(
            self.communication_intents.c.source_module == source_module,
            self.communication_intents.c.source_event_id == source_event_id,
        )
        with get_tenant_conn(self.engine, ctx) as conn:
            row = conn.execute(stmt).mappings().first()
        if row is None:
            return None
        return CommunicationIntentRecord.model_validate(dict(row))

    @staticmethod
    def _parse_dt(value: str | datetime) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def build_routing_store(database_url: str, schema: str) -> RoutingStore:
    if not database_url:
        logger.warning("DATABASE_URL vazio; usando store em memoria para roteamento")
        return InMemoryRoutingStore()
    if create_engine is None:
        logger.warning("sqlalchemy indisponivel; usando store em memoria para roteamento")
        return InMemoryRoutingStore()
    try:
        return PostgresRoutingStore(database_url=database_url, schema=schema)
    except Exception as exc:  # pragma: no cover - guard runtime
        logger.warning("Falha ao inicializar PostgresRoutingStore (%s); fallback para memoria", exc)
        return InMemoryRoutingStore()
