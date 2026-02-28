"""Tests for CDSServiceRegistry — 9 scenarios."""

import pytest

from intellicare_core.cds_hooks.models import (
    Card,
    CardSource,
    CDSRequest,
    CDSResponse,
    CDSServiceDefinition,
)
from intellicare_core.cds_hooks.service import CDSService
from intellicare_core.cds_hooks.registry import CDSServiceRegistry


class _FakeService(CDSService):
    def __init__(self, service_id: str = "fake-service", hook: str = "patient-view") -> None:
        self._id = service_id
        self._hook = hook

    @property
    def definition(self) -> CDSServiceDefinition:
        return CDSServiceDefinition(id=self._id, hook=self._hook, title="Fake", description="Test")

    def handle(self, request: CDSRequest) -> CDSResponse:
        return CDSResponse(cards=[Card(summary="Fake card", source=CardSource(label="Fake"))])


def test_registry_register_and_len() -> None:
    reg = CDSServiceRegistry()
    reg.register(_FakeService())
    assert len(reg) == 1


def test_registry_contains() -> None:
    reg = CDSServiceRegistry()
    reg.register(_FakeService("svc-a"))
    assert "svc-a" in reg
    assert "svc-b" not in reg


def test_registry_duplicate_raises() -> None:
    reg = CDSServiceRegistry()
    reg.register(_FakeService("svc-a"))
    with pytest.raises(ValueError, match="already registered"):
        reg.register(_FakeService("svc-a"))


def test_registry_unregister() -> None:
    reg = CDSServiceRegistry()
    reg.register(_FakeService("svc-x"))
    reg.unregister("svc-x")
    assert "svc-x" not in reg
    assert len(reg) == 0


def test_registry_list_services() -> None:
    reg = CDSServiceRegistry()
    reg.register(_FakeService("svc-1", "patient-view"))
    reg.register(_FakeService("svc-2", "order-sign"))
    defns = reg.list_services()
    assert len(defns) == 2
    assert {d.id for d in defns} == {"svc-1", "svc-2"}


def test_registry_call_returns_response() -> None:
    reg = CDSServiceRegistry()
    reg.register(_FakeService("svc-a"))
    req = CDSRequest(hook="patient-view", context={"patientId": "p-001"})
    resp = reg.call("svc-a", req)
    assert resp is not None
    assert resp.cards[0].summary == "Fake card"


def test_registry_call_unknown_returns_none() -> None:
    reg = CDSServiceRegistry()
    assert reg.call("nonexistent", CDSRequest(hook="patient-view", context={})) is None


def test_registry_get_returns_service() -> None:
    reg = CDSServiceRegistry()
    svc = _FakeService("svc-z")
    reg.register(svc)
    assert reg.get("svc-z") is svc


def test_registry_get_unknown_returns_none() -> None:
    reg = CDSServiceRegistry()
    assert reg.get("missing") is None
