"""Matcher de regras de roteamento."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from comunicacao.routing.models import CommunicationIntentRecord, RoutingRule
    from comunicacao.storage.rule_repository import RoutingRuleStore

logger = logging.getLogger(__name__)


class RuleMatcher:
    """Seleciona regras de roteamento baseado em critérios da intent."""

    def __init__(self, rule_store: RoutingRuleStore) -> None:
        self.rule_store = rule_store

    def find_matching_rules(self, intent: CommunicationIntentRecord) -> list[RoutingRule]:
        """
        Busca regras que correspondem à intent.
        
        Retorna lista ordenada por prioridade (menor = maior prioridade).
        """
        matching_rules = self.rule_store.find_matching_rules(
            severity=intent.severity,
            recipient_type=intent.recipient_type.value,
            category=intent.category,
        )

        logger.info(
            "RuleMatcher: encontradas %d regras para intent %s (severity=%s, recipient=%s, category=%s)",
            len(matching_rules),
            intent.id,
            intent.severity,
            intent.recipient_type.value,
            intent.category,
        )

        return matching_rules

    def select_best_rule(self, intent: CommunicationIntentRecord) -> RoutingRule | None:
        """
        Seleciona a melhor regra (maior prioridade = menor valor numérico).
        
        Retorna None se nenhuma regra corresponder.
        """
        matching_rules = self.find_matching_rules(intent)
        
        if not matching_rules:
            logger.warning(
                "RuleMatcher: nenhuma regra encontrada para intent %s (severity=%s, recipient=%s, category=%s)",
                intent.id,
                intent.severity,
                intent.recipient_type.value,
                intent.category,
            )
            return None

        # Regras já vêm ordenadas por prioridade do store
        best_rule = matching_rules[0]
        
        logger.info(
            "RuleMatcher: selecionada regra '%s' (priority=%d) para intent %s",
            best_rule.name,
            best_rule.priority,
            intent.id,
        )

        return best_rule

    def get_channel_sequence(self, intent: CommunicationIntentRecord) -> list[str]:
        """
        Retorna sequência de canais a tentar, baseado na melhor regra.
        
        Considera:
        - preferred_channel da intent
        - excluded_channels da intent
        - channels da regra selecionada
        
        Retorna lista vazia se nenhuma regra corresponder.
        """
        best_rule = self.select_best_rule(intent)
        
        if not best_rule:
            return []

        # Extrai canais da regra
        channels = [step.channel for step in best_rule.channels]

        # Aplica preferred_channel (move para início se presente)
        if intent.preferred_channel and intent.preferred_channel in channels:
            channels.remove(intent.preferred_channel)
            channels.insert(0, intent.preferred_channel)

        # Remove excluded_channels
        if intent.excluded_channels:
            channels = [ch for ch in channels if ch not in intent.excluded_channels]

        logger.info(
            "RuleMatcher: sequência de canais para intent %s: %s",
            intent.id,
            channels,
        )

        return channels

