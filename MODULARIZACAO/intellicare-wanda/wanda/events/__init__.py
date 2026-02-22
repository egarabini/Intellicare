"""Proactive event consumption from the IntelliCare ecosystem (EF-W006)."""

from wanda.events.consumer import EcosystemEventConsumer
from wanda.events.coordinator import EventCoordinator
from wanda.events.models import IntelliCareEvent, CoordinationResult

__all__ = ["EcosystemEventConsumer", "EventCoordinator", "IntelliCareEvent", "CoordinationResult"]
