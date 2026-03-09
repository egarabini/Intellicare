# Re-export para facilitar imports dentro do bridge
from intellicare_core.bridge.adapter import BaseHISAdapter
from intellicare_core.bridge.context import HISContext, HISSystem

__all__ = ["BaseHISAdapter", "HISContext", "HISSystem"]
