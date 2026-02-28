"""Regression tests for W10-A Custom Operations Framework."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from grahame.api.app import app


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _create_operation(client: TestClient, payload: dict, tenant: str = "tenant-a") -> dict:
    resp = client.post(
        "/api/v1/admin/custom-operations",
        headers={"X-Tenant-ID": tenant},
        json=payload,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_custom_ops_router_system(client: TestClient):
    _create_operation(
        client,
        {
            "name": "relatorio-consolidado",
            "type": "system",
            "handlerType": "url",
            "handlerConfig": {"url": "https://example.org/op"},
        },
    )
    with patch(
        "grahame.services.custom_ops_service.CustomOpsService._execute_url",
        new_callable=AsyncMock,
    ) as mocked:
        mocked.return_value = {
            "resourceType": "Parameters",
            "parameter": [{"name": "result", "valueString": "ok"}],
        }
        resp = client.post(
            "/api/v1/fhir/$relatorio-consolidado",
            headers={"X-Tenant-ID": "tenant-a"},
            json={"resourceType": "Parameters", "parameter": []},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["resourceType"] == "Parameters"
    assert data["parameter"][0]["name"] == "result"


def test_custom_ops_router_instance(client: TestClient):
    _create_operation(
        client,
        {
            "name": "exames-laboratoriais",
            "type": "instance",
            "resourceType": "Patient",
            "handlerType": "url",
            "handlerConfig": {"url": "https://example.org/op"},
        },
        tenant="default",
    )

    with patch(
        "grahame.services.custom_ops_service.CustomOpsService._execute_url",
        new_callable=AsyncMock,
    ) as mocked:
        with patch("grahame.services.fhir_service.FHIRService.get", new_callable=AsyncMock) as get_resource:
            get_resource.return_value = type(
                "FHIRRow",
                (),
                {"resource": {"resourceType": "Patient", "id": "p-001"}},
            )()
            mocked.return_value = {
                "resourceType": "Parameters",
                "parameter": [{"name": "result", "valueString": "lista"}],
            }
            resp = client.post(
                "/api/v1/fhir/Patient/p-001/$exames-laboratoriais",
                headers={"X-Tenant-ID": "default"},
                json={"resourceType": "Parameters", "parameter": []},
            )

    assert resp.status_code == 200
    assert resp.json()["resourceType"] == "Parameters"


def test_custom_ops_404_when_not_registered(client: TestClient):
    resp = client.post(
        "/api/v1/fhir/$operacao-inexistente",
        headers={"X-Tenant-ID": "tenant-missing"},
        json={"resourceType": "Parameters", "parameter": []},
    )
    assert resp.status_code == 404
    assert resp.json()["resourceType"] == "OperationOutcome"


def test_admin_custom_operations_crud(client: TestClient):
    created = _create_operation(
        client,
        {
            "name": "consolidar",
            "type": "system",
            "handlerType": "url",
            "handlerConfig": {"url": "https://example.org/op"},
            "timeoutSeconds": 10,
        },
        tenant="tenant-crud",
    )
    op_id = created["id"]

    list_resp = client.get("/api/v1/admin/custom-operations", headers={"X-Tenant-ID": "tenant-crud"})
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

    update_resp = client.put(
        f"/api/v1/admin/custom-operations/{op_id}",
        headers={"X-Tenant-ID": "tenant-crud"},
        json={"timeoutSeconds": 15},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["timeoutSeconds"] == 15

    delete_resp = client.delete(
        f"/api/v1/admin/custom-operations/{op_id}",
        headers={"X-Tenant-ID": "tenant-crud"},
    )
    assert delete_resp.status_code == 204


def test_custom_operation_rate_limit(client: TestClient):
    _create_operation(
        client,
        {
            "name": "rate-limit-op",
            "type": "system",
            "handlerType": "url",
            "handlerConfig": {"url": "https://example.org/op"},
            "rateLimitPerMinute": 1,
        },
        tenant="tenant-rate",
    )

    with patch(
        "grahame.services.custom_ops_service.CustomOpsService._execute_url",
        new_callable=AsyncMock,
    ) as mocked:
        mocked.return_value = {
            "resourceType": "Parameters",
            "parameter": [{"name": "result", "valueString": "ok"}],
        }
        first = client.post(
            "/api/v1/fhir/$rate-limit-op",
            headers={"X-Tenant-ID": "tenant-rate"},
            json={"resourceType": "Parameters", "parameter": []},
        )
        second = client.post(
            "/api/v1/fhir/$rate-limit-op",
            headers={"X-Tenant-ID": "tenant-rate"},
            json={"resourceType": "Parameters", "parameter": []},
        )

    assert first.status_code == 200
    assert second.status_code == 429
