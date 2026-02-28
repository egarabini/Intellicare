"""Consolidation module - processamento de eventos para sincronização.

Classes principais:
- ConsolidationConsumer: Lê eventos de Redis e consolida em analytics schema
- OperationType: Enum de operações (CREATE, UPDATE, DELETE)
- ConsolidationEvent: Dataclass do evento tratado
"""

from .consumer import ConsolidationConsumer, OperationType, ConsolidationEvent

__all__ = ["ConsolidationConsumer", "OperationType", "ConsolidationEvent"]
