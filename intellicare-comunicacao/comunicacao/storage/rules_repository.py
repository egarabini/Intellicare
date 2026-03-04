"""Persistencia de regras de roteamento (Postgres + fallback)."""

from __future__ import annotations
from comunicacao.storage.tenant_utils import get_tenant_conn

import logging
from datetime import UTC, datetime

import comunicacao.routing.models as routing_models
from comunicacao.routing.rules import InMemoryRoutingRuleStore, RoutingRuleStore, build_default_rules

try:
    from sqlalchemy import JSON, BOOLEAN, INTEGER, TIMESTAMP, Column, MetaData, String, Table, create_engine, select
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
    create_engine = None  # type: ignore[assignment]
    select = None  # type: ignore[assignment]
    pg_insert = None  # type: ignore[assignment]
    Engine = object  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class PostgresRoutingRuleStore:
    def __init__(self, database_url: str, schema: str) -> None:
        if create_engine is None or pg_insert is None:
            raise RuntimeError("sqlalchemy nao instalado.")
        self.engine: Engine = create_engine(database_url, future=True, pool_pre_ping=True)
        metadata = MetaData(schema=schema)
        self.table = Table(
            "routing_rules",
            metadata,
            Column("id", String(100), primary_key=True),
            Column("name", String(200), nullable=False),
            Column("priority", INTEGER, nullable=False),
            Column("active", BOOLEAN, nullable=False),
            Column("conditions", JSON, nullable=False),
            Column("action", JSON, nullable=False),
            Column("institution_id", String(200), nullable=True),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        )

    def list_rules(self) -> list[routing_models.RoutingRule]:
        stmt = select(self.table).order_by(self.table.c.priority.asc())
        with get_tenant_conn(self.engine, ctx) as conn:
            rows = conn.execute(stmt).mappings().all()
        items: list[routing_models.RoutingRule] = []
        for row in rows:
            conditions = row["conditions"] or {}
            action = row["action"] or {}
            items.append(
                routing_models.RoutingRule(
                    id=row["id"],
                    name=row["name"],
                    priority=int(row["priority"]),
                    active=bool(row["active"]),
                    severities=list(conditions.get("severities", [])),
                    recipient_types=[routing_models.RecipientType(x) for x in conditions.get("recipient_types", [])],
                    categories=list(conditions.get("categories", [])),
                    channels=[routing_models.ChannelStep(**channel) for channel in action.get("channels", [])],
                )
            )
        return items

    def upsert_rule(self, rule: routing_models.RoutingRule) -> routing_models.RoutingRule:
        payload = rule.model_dump(mode="json")
        conditions = {
            "severities": payload.get("severities", []),
            "recipient_types": payload.get("recipient_types", []),
            "categories": payload.get("categories", []),
        }
        action = {"channels": payload.get("channels", [])}
        stmt = pg_insert(self.table).values(
            id=rule.id,
            name=rule.name,
            priority=rule.priority,
            active=rule.active,
            conditions=conditions,
            action=action,
            institution_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[self.table.c.id],
            set_={
                "name": rule.name,
                "priority": rule.priority,
                "active": rule.active,
                "conditions": conditions,
                "action": action,
                "updated_at": datetime.now(UTC),
            },
        )
        with get_tenant_conn(self.engine, ctx) as conn:
            conn.execute(stmt)
        return rule


def build_routing_rule_store(database_url: str, schema: str) -> RoutingRuleStore:
    if not database_url:
        return InMemoryRoutingRuleStore(rules=build_default_rules())
    if create_engine is None:
        return InMemoryRoutingRuleStore(rules=build_default_rules())
    try:
        store = PostgresRoutingRuleStore(database_url=database_url, schema=schema)
        existing = store.list_rules()
        if not existing:
            for rule in build_default_rules():
                store.upsert_rule(rule)
        return store
    except Exception as exc:  # pragma: no cover
        logger.warning("Falha ao inicializar PostgresRoutingRuleStore (%s); fallback memoria", exc)
        return InMemoryRoutingRuleStore(rules=build_default_rules())

