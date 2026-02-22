"""Testes para CnesClient com respx mock."""

import httpx
import pytest
import respx

from zilda.engine.cnes_client import CnesClient
from zilda.engine.models import HealthEstablishment, HealthRegion, HealthUnitType

from conftest import (
    CNES_BASE_URL,
    FAKE_ESTABLISHMENT,
    FAKE_ESTABLISHMENT_2,
    FAKE_REGION,
    FAKE_REGION_2,
    FAKE_UNIT_TYPES,
)


@pytest.fixture
def mock_client() -> CnesClient:
    """Client com cache limpo para cada teste."""
    return CnesClient(base_url=CNES_BASE_URL, timeout=5)


class TestGetUnitTypes:
    @respx.mock
    def test_success(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/tipounidades").mock(
            return_value=httpx.Response(200, json=FAKE_UNIT_TYPES)
        )
        types = mock_client.get_unit_types()
        assert len(types) == 3
        assert isinstance(types[0], HealthUnitType)
        assert types[0].code == "1"
        assert types[1].description == "HOSPITAL GERAL"

    @respx.mock
    def test_cached(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/tipounidades").mock(
            return_value=httpx.Response(200, json=FAKE_UNIT_TYPES)
        )
        types1 = mock_client.get_unit_types()
        types2 = mock_client.get_unit_types()
        assert types1 == types2
        assert respx.calls.call_count == 1  # cached on 2nd call

    @respx.mock
    def test_api_error(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/tipounidades").mock(
            return_value=httpx.Response(500)
        )
        types = mock_client.get_unit_types()
        assert types == []


class TestSearchEstablishments:
    @respx.mock
    def test_search_by_state(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[FAKE_ESTABLISHMENT, FAKE_ESTABLISHMENT_2])
        )
        results = mock_client.search_establishments(state_code="35")
        assert len(results) == 2
        assert isinstance(results[0], HealthEstablishment)
        assert results[0].cnes_code == "2077485"

    @respx.mock
    def test_search_by_city(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[FAKE_ESTABLISHMENT])
        )
        results = mock_client.search_establishments(city_code="3550308")
        assert len(results) == 1
        assert results[0].city_name == "SAO PAULO"

    @respx.mock
    def test_search_empty(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[])
        )
        results = mock_client.search_establishments(state_code="99")
        assert results == []

    @respx.mock
    def test_search_with_wrapper(self, mock_client: CnesClient) -> None:
        """API retorna dados em wrapper dict."""
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json={"data": [FAKE_ESTABLISHMENT]})
        )
        results = mock_client.search_establishments(city_code="3550308")
        assert len(results) == 1

    @respx.mock
    def test_limit_cap(self, mock_client: CnesClient) -> None:
        """Limit eh capped em 100."""
        route = respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[])
        )
        mock_client.search_establishments(limit=200)
        request = route.calls[0].request
        assert "limit=100" in str(request.url)


class TestGetEstablishmentByCnes:
    @respx.mock
    def test_found(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[FAKE_ESTABLISHMENT])
        )
        est = mock_client.get_establishment_by_cnes("2077485")
        assert est is not None
        assert est.cnes_code == "2077485"
        assert est.has_surgical_center is True
        assert est.has_neonatal_center is False
        assert est.active is True

    @respx.mock
    def test_not_found(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[])
        )
        est = mock_client.get_establishment_by_cnes("9999999")
        assert est is None

    @respx.mock
    def test_cached(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[FAKE_ESTABLISHMENT])
        )
        est1 = mock_client.get_establishment_by_cnes("2077485")
        est2 = mock_client.get_establishment_by_cnes("2077485")
        assert est1 == est2
        assert respx.calls.call_count == 1


class TestGetHealthRegions:
    @respx.mock
    def test_success(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/macrorregiao-e-regiao-de-saude/municipio").mock(
            return_value=httpx.Response(200, json=[FAKE_REGION, FAKE_REGION_2])
        )
        regions = mock_client.get_health_regions(state_code="35")
        assert len(regions) == 2
        assert isinstance(regions[0], HealthRegion)
        assert regions[0].region_name == "Grande Sao Paulo"

    @respx.mock
    def test_empty(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/macrorregiao-e-regiao-de-saude/municipio").mock(
            return_value=httpx.Response(200, json=[])
        )
        regions = mock_client.get_health_regions(state_code="99")
        assert regions == []


class TestValidateCnes:
    @respx.mock
    def test_valid_found(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[FAKE_ESTABLISHMENT])
        )
        v = mock_client.validate_cnes("2077485")
        assert v.valid_format is True
        assert v.found is True
        assert v.establishment is not None

    @respx.mock
    def test_valid_not_found(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[])
        )
        v = mock_client.validate_cnes("9999999")
        assert v.valid_format is True
        assert v.found is False

    def test_invalid_format_short(self, mock_client: CnesClient) -> None:
        v = mock_client.validate_cnes("123")
        assert v.valid_format is False
        assert "esperados 7 digitos" in v.message

    def test_invalid_format_long(self, mock_client: CnesClient) -> None:
        v = mock_client.validate_cnes("12345678")
        assert v.valid_format is False

    @respx.mock
    def test_strips_non_digits(self, mock_client: CnesClient) -> None:
        respx.get(f"{CNES_BASE_URL}/cnes/estabelecimentos").mock(
            return_value=httpx.Response(200, json=[FAKE_ESTABLISHMENT])
        )
        v = mock_client.validate_cnes("207-7485")
        assert v.valid_format is True
        assert v.cnes_code == "2077485"


class TestHelpers:
    def test_safe_float_valid(self) -> None:
        assert CnesClient._safe_float("23.5") == 23.5
        assert CnesClient._safe_float(10) == 10.0

    def test_safe_float_none(self) -> None:
        assert CnesClient._safe_float(None) is None

    def test_safe_float_invalid(self) -> None:
        assert CnesClient._safe_float("abc") is None
        assert CnesClient._safe_float("") is None

    @respx.mock
    def test_request_error(self) -> None:
        client = CnesClient(base_url=CNES_BASE_URL, timeout=1)
        respx.get(f"{CNES_BASE_URL}/cnes/tipounidades").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        result = client._get("/cnes/tipounidades")
        assert result == []

    def test_close(self) -> None:
        client = CnesClient(base_url=CNES_BASE_URL)
        client.close()  # should not raise
