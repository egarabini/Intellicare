"""Regras configuraveis de roteamento e matcher."""

from __future__ import annotations

from typing import Protocol

import comunicacao.routing.models as routing_models


def build_default_rules() -> list[routing_models.RoutingRule]:
    return [
        routing_models.RoutingRule(
            id="rule_critical_professional",
            name="Critico profissional",
            priority=10,
            severities=["critical"],
            recipient_types=[routing_models.RecipientType.PROFESSIONAL],
            channels=[
                routing_models.ChannelStep(channel="rocketchat"),
                routing_models.ChannelStep(channel="sms"),
                routing_models.ChannelStep(channel="push"),
            ],
        ),
        routing_models.RoutingRule(
            id="rule_critical_patient",
            name="Critico paciente",
            priority=20,
            severities=["critical"],
            recipient_types=[routing_models.RecipientType.PATIENT],
            channels=[
                routing_models.ChannelStep(channel="whatsapp"),
                routing_models.ChannelStep(channel="sms"),
                routing_models.ChannelStep(channel="rocketchat"),
            ],
        ),
        routing_models.RoutingRule(
            id="rule_high_default",
            name="High default",
            priority=30,
            severities=["high"],
            channels=[
                routing_models.ChannelStep(channel="rocketchat"),
                routing_models.ChannelStep(channel="email"),
                routing_models.ChannelStep(channel="push"),
            ],
        ),
        routing_models.RoutingRule(
            id="rule_medium_default",
            name="Medium default",
            priority=40,
            severities=["medium"],
            channels=[routing_models.ChannelStep(channel="rocketchat")],
        ),
        routing_models.RoutingRule(
            id="rule_low_default",
            name="Low default",
            priority=50,
            severities=["low"],
            channels=[routing_models.ChannelStep(channel="email")],
        ),
        routing_models.RoutingRule(
            id="rule_fallback_any",
            name="Fallback any",
            priority=999,
            channels=[routing_models.ChannelStep(channel="email"), routing_models.ChannelStep(channel="push")],
        ),
    ]


class RoutingRuleStore(Protocol):
    def list_rules(self) -> list[routing_models.RoutingRule]: ...

    def upsert_rule(self, rule: routing_models.RoutingRule) -> routing_models.RoutingRule: ...


class InMemoryRoutingRuleStore:
    def __init__(self, rules: list[routing_models.RoutingRule] | None = None) -> None:
        self._rules: dict[str, routing_models.RoutingRule] = {}
        for item in rules or build_default_rules():
            self._rules[item.id] = item

    def list_rules(self) -> list[routing_models.RoutingRule]:
        return sorted(self._rules.values(), key=lambda x: x.priority)

    def upsert_rule(self, rule: routing_models.RoutingRule) -> routing_models.RoutingRule:
        self._rules[rule.id] = rule
        return rule


class RuleMatcher:
    def __init__(self, rule_store: RoutingRuleStore) -> None:
        self._rule_store = rule_store

    def resolve_channels(self, intent: routing_models.CommunicationIntentRecord) -> list[routing_models.ChannelStep]:
        rules = self._rule_store.list_rules()
        for rule in rules:
            if not rule.active:
                continue
            if rule.severities and intent.severity.lower() not in {x.lower() for x in rule.severities}:
                continue
            if rule.recipient_types and intent.recipient_type not in rule.recipient_types:
                continue
            if rule.categories and intent.category.lower() not in {x.lower() for x in rule.categories}:
                continue
            return rule.channels
        return [routing_models.ChannelStep(channel="rocketchat")]
