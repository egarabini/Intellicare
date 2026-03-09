"""HISAdapterRegistry — registro de adaptadores HIS disponíveis no runtime."""

from __future__ import annotations

from intellicare_core.bridge.adapter import BaseHISAdapter


class HISAdapterRegistry:
    """Registro de adaptadores HIS disponíveis no runtime.

    Adaptadores se registram no startup do intellicare-bridge.
    O GRAHAME e o WANDA consultam o registry para descobrir quais HIS estão ativos.
    """

    _adapters: dict[str, BaseHISAdapter] = {}

    @classmethod
    def register(cls, adapter: BaseHISAdapter) -> None:
        """Registra um adaptador. Chamado no lifespan do intellicare-bridge."""
        cls._adapters[adapter.his_system] = adapter

    @classmethod
    def get(cls, his_system: str) -> BaseHISAdapter | None:
        """Retorna o adaptador para um sistema HIS específico, ou None."""
        return cls._adapters.get(his_system)

    @classmethod
    def list_available(cls) -> list[str]:
        """Lista os sistemas HIS com adaptador registrado."""
        return list(cls._adapters.keys())
