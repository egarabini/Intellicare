"""Registry that holds CDSService instances and dispatches hook calls."""

from __future__ import annotations

from typing import Optional

from .models import CDSRequest, CDSResponse, CDSServiceDefinition
from .service import CDSService


class CDSServiceRegistry:
    """Central registry for CDS Hook services.

    Usage::

        registry = CDSServiceRegistry()
        registry.register(PatientViewAlerts())
        registry.register(OrderSignChecker())

        # Discovery
        definitions = registry.list_services()

        # Invoke
        response = registry.call("patient-view-alerts", request)
    """

    def __init__(self) -> None:
        self._services: dict[str, CDSService] = {}

    def register(self, service: CDSService) -> None:
        """Register a CDSService. Raises if id already taken."""
        if service.id in self._services:
            raise ValueError(f"CDS service '{service.id}' already registered")
        self._services[service.id] = service

    def unregister(self, service_id: str) -> None:
        """Remove a registered service (useful for testing)."""
        self._services.pop(service_id, None)

    def list_services(self) -> list[CDSServiceDefinition]:
        """Return all service definitions for the discovery endpoint."""
        return [svc.definition for svc in self._services.values()]

    def get(self, service_id: str) -> Optional[CDSService]:
        return self._services.get(service_id)

    def call(self, service_id: str, request: CDSRequest) -> Optional[CDSResponse]:
        """Invoke a registered service. Returns None if service_id not found."""
        svc = self._services.get(service_id)
        if svc is None:
            return None
        return svc.handle(request)

    def __len__(self) -> int:
        return len(self._services)

    def __contains__(self, service_id: str) -> bool:
        return service_id in self._services
