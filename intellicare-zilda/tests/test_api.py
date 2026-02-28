"""Testes para API REST do Zilda."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from zilda.api.app import _state, create_app
from zilda.config import ZildaConfig
from zilda.engine.cnes_client import CnesClient
from zilda.engine.models import (
    CnesValidation,
    HealthEstablishment,
    HealthRegion,
    HealthUnitType,
    TerritorialSummary,
)
from zilda.engine.territorial import TerritorialEngine


def _make_est(cnes: str = "2077485") -> HealthEstablishment:
    return HealthEstablishment(
        cnes_code=cnes, cnpj="12345678000199",
        legal_name="Hospital Exemplo", fantasy_name="Hosp Exemplo",
        unit_type_code="5", unit_type_description="HOSPITAL GERAL",
        state_code="35", city_code="3550308", city_name="SAO PAULO",
        address="Rua A 1", neighborhood="Centro", phone="11999999999",
        has_surgical_center=True, active=True,
    )


def _make_region() -> HealthRegion:
    return HealthRegion(
        city_code="3550308", city_name="SAO PAULO",
        state_code="35", state_name="SAO PAULO",
        region_code="35001", region_name="Grande SP",
        macro_region_code="35000", macro_region_name="Macro SP",
        population=12000000,
    )


@pytest.fixture
def app_client() -> TestClient:
    """Client de teste com mocks injetados."""
    app = create_app()

    mock_cnes = MagicMock(spec=CnesClient)
    mock_cnes.get_unit_types.return_value = [
        HealthUnitType(code="1", description="POSTO DE SAUDE"),
        HealthUnitType(code="5", description="HOSPITAL GERAL"),
    ]
    mock_cnes.search_establishments.return_value = [_make_est()]
    mock_cnes.get_establishment_by_cnes.return_value = _make_est()
    mock_cnes.validate_cnes.return_value = CnesValidation(
        cnes_code="2077485", valid_format=True, found=True,
        establishment=_make_est(), message="OK",
    )
    mock_cnes.get_health_regions.return_value = [_make_region()]

    mock_engine = MagicMock(spec=TerritorialEngine)
    mock_engine.get_territorial_summary.return_value = TerritorialSummary(
        state_code="35", city_code="3550308", region_name="Grande SP",
        total_establishments=1, type_distribution={"HOSPITAL GERAL": 1},
        has_surgical_center=1, establishments=[_make_est()],
    )
    mock_engine.get_region_context.return_value = {
        "found": True, "city_name": "SAO PAULO",
        "region_name": "Grande SP", "cities_in_region": 5,
    }

    _state["config"] = ZildaConfig()
    _state["client"] = mock_cnes
    _state["engine"] = mock_engine

    client = TestClient(app, raise_server_exceptions=False)
    yield client
    _state.clear()


class TestHealthEndpoint:
    def test_health_ok(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module_name"] == "intellicare-zilda"

    def test_health_degraded(self, app_client: TestClient) -> None:
        _state["client"].get_unit_types.return_value = []
        response = app_client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "degraded"


class TestInfoEndpoint:
    def test_info(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/info")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "intellicare-zilda"
        assert "cnes-lookup" in data["capabilities"]
        assert "cnes_base_url" in data["metadata"]


class TestUnitTypesEndpoint:
    def test_list(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/unit-types")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["code"] == "1"


class TestEstablishmentsEndpoint:
    def test_search(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/establishments?state_code=35")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["cnes_code"] == "2077485"

    def test_get_by_cnes(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/establishment/2077485")
        assert response.status_code == 200
        data = response.json()
        assert data["cnes_code"] == "2077485"

    def test_get_by_cnes_not_found(self, app_client: TestClient) -> None:
        _state["client"].get_establishment_by_cnes.return_value = None
        response = app_client.get("/api/v1/establishment/9999999")
        assert response.status_code == 404


class TestValidateEndpoint:
    def test_validate(self, app_client: TestClient) -> None:
        response = app_client.post("/api/v1/validate", json={"cnes_code": "2077485"})
        assert response.status_code == 200
        data = response.json()
        assert data["valid_format"] is True
        assert data["found"] is True


class TestRegionsEndpoint:
    def test_list(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/regions?state_code=35")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["region_name"] == "Grande SP"


class TestTerritorialEndpoints:
    def test_summary(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/territorial-summary?state_code=35&city_code=3550308")
        assert response.status_code == 200
        data = response.json()
        assert data["total_establishments"] == 1

    def test_region_context(self, app_client: TestClient) -> None:
        response = app_client.get("/api/v1/region-context/3550308?state_code=35")
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is True
        assert data["region_name"] == "Grande SP"
