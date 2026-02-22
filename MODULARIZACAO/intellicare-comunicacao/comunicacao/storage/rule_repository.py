"""Repositório de regras de roteamento."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from comunicacao.routing.models import RoutingRule

# Re-export for test compatibility
__all__ = [
    "RoutingRuleChannel",
    "RoutingRule",
    "RoutingRuleStore",
    "InMemoryRuleStore",
    "PostgresRuleStore",
    "build_rule_store",
]


@dataclass
class RoutingRuleChannel:
    """Canal de roteamento com ordem de prioridade (compatibilidade com testes)."""

    channel: str
    timeout_seconds: int = 30
    order: int = 1

logger = logging.getLogger(__name__)


class RoutingRuleStore(Protocol):
    """Interface para persistência de regras de roteamento."""

    def save_rule(self, rule: RoutingRule) -> None:
        """Salva ou atualiza uma regra de roteamento."""
        ...

    def get_rule(self, rule_id: str) -> RoutingRule | None:
        """Busca regra por ID."""
        ...

    def list_rules(self, active_only: bool = True) -> list[RoutingRule]:
        """Lista todas as regras, opcionalmente apenas ativas."""
        ...

    def delete_rule(self, rule_id: str) -> bool:
        """Remove uma regra. Retorna True se removida."""
        ...

    def find_matching_rules(
        self,
        severity: str,
        recipient_type: str,
        category: str,
    ) -> list[RoutingRule]:
        """Busca regras que correspondem aos critérios (ordenadas por prioridade)."""
        ...


class InMemoryRuleStore:
    """Store de regras em memória (para testes e fallback)."""

    def __init__(self) -> None:
        self._rules: dict[str, RoutingRule] = {}

    def save_rule(self, rule: RoutingRule) -> None:
        self._rules[rule.id] = rule

    def get_rule(self, rule_id: str) -> RoutingRule | None:
        return self._rules.get(rule_id)

    def list_rules(self, active_only: bool = True) -> list[RoutingRule]:
        rules = list(self._rules.values())
        if active_only:
            rules = [r for r in rules if r.active]
        return sorted(rules, key=lambda r: r.priority)

    def upsert(self, rule: RoutingRule) -> None:
        """Alias de save_rule para compatibilidade com testes."""
        self.save_rule(rule)

    def delete_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False

    def find_matching_rules(
        self,
        severity: str,
        recipient_type: str,
        category: str,
    ) -> list[RoutingRule]:
        """Busca regras que correspondem aos critérios."""
        matching = []
        for rule in self._rules.values():
            if not rule.active:
                continue
            
            # Verifica se a regra se aplica
            severity_match = not rule.severities or severity in rule.severities
            recipient_match = not rule.recipient_types or recipient_type in [rt.value for rt in rule.recipient_types]
            category_match = not rule.categories or category in rule.categories
            
            if severity_match and recipient_match and category_match:
                matching.append(rule)
        
        # Ordena por prioridade (menor = maior prioridade)
        return sorted(matching, key=lambda r: r.priority)


class PostgresRuleStore:
    """Store de regras em PostgreSQL."""

    def __init__(self, database_url: str, schema: str) -> None:
        try:
            from sqlalchemy import (
                JSON,
                Boolean,
                Column,
                Integer,
                MetaData,
                String,
                TIMESTAMP,
                Table,
                create_engine,
                delete,
                insert,
                select,
                text,
                update,
            )
            from sqlalchemy.engine import Engine
        except ImportError:
            raise RuntimeError("sqlalchemy não instalado")

        self.schema = schema
        self.engine: Engine = create_engine(database_url, future=True, pool_pre_ping=True)
        self.metadata = MetaData(schema=schema)

        self.routing_rules = Table(
            "routing_rules",
            self.metadata,
            Column("id", String(100), primary_key=True),
            Column("name", String(200), nullable=False),
            Column("priority", Integer, nullable=False),
            Column("active", Boolean, nullable=False),
            Column("conditions", JSON, nullable=False),
            Column("action", JSON, nullable=False),
            Column("institution_id", String(200), nullable=True),
            Column("created_at", TIMESTAMP(timezone=True), nullable=False),
            Column("updated_at", TIMESTAMP(timezone=True), nullable=False),
        )

    def save_rule(self, rule: RoutingRule) -> None:
        """Salva ou atualiza regra (upsert)."""
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from datetime import UTC, datetime

        payload = rule.model_dump(mode="json")
        
        # Converte para formato de conditions/action
        conditions = {
            "severities": payload.get("severities", []),
            "recipient_types": payload.get("recipient_types", []),
            "categories": payload.get("categories", []),
        }
        action = {
            "channels": payload.get("channels", []),
        }

        stmt = pg_insert(self.routing_rules).values(
            id=payload["id"],
            name=payload["name"],
            priority=payload["priority"],
            active=payload["active"],
            conditions=conditions,
            action=action,
            institution_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_=dict(
                name=stmt.excluded.name,
                priority=stmt.excluded.priority,
                active=stmt.excluded.active,
                conditions=stmt.excluded.conditions,
                action=stmt.excluded.action,
                updated_at=datetime.now(UTC),
            ),
        )

        with self.engine.begin() as conn:
            conn.execute(stmt)

    def get_rule(self, rule_id: str) -> RoutingRule | None:
        from sqlalchemy import select

        stmt = select(self.routing_rules).where(self.routing_rules.c.id == rule_id)
        with self.engine.begin() as conn:
            row = conn.execute(stmt).mappings().first()
        
        if row is None:
            return None
        
        return self._row_to_rule(dict(row))

    def list_rules(self, active_only: bool = True) -> list[RoutingRule]:
        from sqlalchemy import select

        stmt = select(self.routing_rules).order_by(self.routing_rules.c.priority)
        if active_only:
            stmt = stmt.where(self.routing_rules.c.active == True)
        
        with self.engine.begin() as conn:
            rows = conn.execute(stmt).mappings().all()
        
        return [self._row_to_rule(dict(row)) for row in rows]

    def delete_rule(self, rule_id: str) -> bool:
        from sqlalchemy import delete

        stmt = delete(self.routing_rules).where(self.routing_rules.c.id == rule_id)
        with self.engine.begin() as conn:
            result = conn.execute(stmt)
        return result.rowcount > 0

    def find_matching_rules(
        self,
        severity: str,
        recipient_type: str,
        category: str,
    ) -> list[RoutingRule]:
        """Busca regras que correspondem aos critérios."""
        # Por simplicidade, busca todas as regras ativas e filtra em memória
        # Em produção, poderia usar JSONB queries para filtrar no DB
        all_rules = self.list_rules(active_only=True)
        
        matching = []
        for rule in all_rules:
            severity_match = not rule.severities or severity in rule.severities
            recipient_match = not rule.recipient_types or recipient_type in [rt.value for rt in rule.recipient_types]
            category_match = not rule.categories or category in rule.categories
            
            if severity_match and recipient_match and category_match:
                matching.append(rule)
        
        return sorted(matching, key=lambda r: r.priority)

    @staticmethod
    def _row_to_rule(row: dict) -> RoutingRule:
        """Converte row do DB para RoutingRule."""
        from comunicacao.routing.models import RecipientType, ChannelStep

        conditions = row.get("conditions", {})
        action = row.get("action", {})
        
        return RoutingRule(
            id=row["id"],
            name=row["name"],
            priority=row["priority"],
            active=row["active"],
            severities=conditions.get("severities", []),
            recipient_types=[RecipientType(rt) for rt in conditions.get("recipient_types", [])],
            categories=conditions.get("categories", []),
            channels=[ChannelStep(**ch) for ch in action.get("channels", [])],
        )


def build_rule_store(database_url: str, schema: str) -> RoutingRuleStore:
    """Factory para criar store de regras."""
    if not database_url:
        logger.warning("DATABASE_URL vazio; usando store em memória para regras")
        return InMemoryRuleStore()
    
    try:
        return PostgresRuleStore(database_url=database_url, schema=schema)
    except Exception as exc:
        logger.warning("Falha ao inicializar PostgresRuleStore (%s); fallback para memória", exc)
        return InMemoryRuleStore()

