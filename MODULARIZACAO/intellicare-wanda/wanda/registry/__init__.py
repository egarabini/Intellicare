"""Registry package for persistent module registration (EF-W001)."""

from wanda.registry.persistent_registry import PersistentModuleRegistry
from wanda.registry.discovery_service import DiscoveryService

__all__ = ["PersistentModuleRegistry", "DiscoveryService"]
