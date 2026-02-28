"""
Donabedian consolidation module.

Provides:
- DonabedianConsolidationService: Consolidates events from operacional to analitico
- DonabedianConsolidationConsumer: Redis consumer for consolidation events
"""

from donabedian.consolidation.service import DonabedianConsolidationService
from donabedian.consolidation.worker import DonabedianConsolidationConsumer

__all__ = [
    "DonabedianConsolidationService",
    "DonabedianConsolidationConsumer",
]
