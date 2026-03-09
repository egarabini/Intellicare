"""Pacote bridge — contratos e contexto para adaptadores HIS."""

from intellicare_core.bridge.context import HISContext, HISSystem
from intellicare_core.bridge.adapter import BaseHISAdapter
from intellicare_core.bridge.registry import HISAdapterRegistry

__all__ = ["HISContext", "HISSystem", "BaseHISAdapter", "HISAdapterRegistry"]
