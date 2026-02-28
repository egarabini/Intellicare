"""Abstract base class for CDS Hook services."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import CDSRequest, CDSResponse, CDSServiceDefinition


class CDSService(ABC):
    """Base class for implementing a CDS Hook service.

    Subclass this, implement ``definition`` and ``handle()``, then register
    the instance with ``CDSServiceRegistry``.

    Example::

        class PatientViewAlerts(CDSService):
            @property
            def definition(self) -> CDSServiceDefinition:
                return CDSServiceDefinition(
                    id="patient-view-alerts",
                    hook="patient-view",
                    title="IntelliCare Patient Alerts",
                    description="Alerts for high-risk patients",
                    prefetch={
                        "patient": "Patient/{{context.patientId}}",
                        "conditions": "Condition?patient={{context.patientId}}&clinical-status=active",
                    },
                )

            def handle(self, request: CDSRequest) -> CDSResponse:
                ...
    """

    @property
    @abstractmethod
    def definition(self) -> CDSServiceDefinition:
        """Return the service metadata used for discovery."""

    @abstractmethod
    def handle(self, request: CDSRequest) -> CDSResponse:
        """Process a hook call and return cards."""

    # Convenience helpers ──────────────────────────────────────────────────────

    @property
    def id(self) -> str:
        return self.definition.id

    @property
    def hook(self) -> str:
        return self.definition.hook
