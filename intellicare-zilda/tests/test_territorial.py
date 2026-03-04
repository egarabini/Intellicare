"""Testes para TerritorialEngine do Zilda."""

from unittest.mock import MagicMock

import pytest

from zilda.engine.models import HealthEstablishment, HealthRegion, TerritorialSummary
from zilda.engine.territorial import TerritorialEngine


def _make_est(
    cnes: str = "1111111",
    unit_type_desc: str = "HOSPITAL GERAL",
    unit_type_code: str = "5",
    surgical: bool = False,
    obstetric: bool = False,
    neonatal: bool = False,
) -> HealthEstablishment:
    return HealthEstablishment(
        cnes_code=cnes, cnpj=None, legal_name="Test",
        fantasy_name=None, unit_type_code=unit_type_code,
        unit_type_description=unit_type_desc,
        state_code="35", city_code="3550308", city_name="SP",
        address=None, neighborhood=None, phone=None,
        has_surgical_center=surgical,
        has_obstetric_center=obstetric,
        has_neonatal_center=neonatal,
    )


def _make_region(
    city_code: str = "3550308",
    city_name: str = "SAO PAULO",
    region_code: str = "35001",
    region_name: str = "Grande SP",
    population: int = 12000000,
) -> HealthRegion:
    return HealthRegion(
        city_code=city_code, city_name=city_name,
        state_code="35", state_name="SAO PAULO",
        region_code=region_code, region_name=region_name,
        macro_region_code="35000", macro_region_name="Macro SP",
        population=population,
    )


class TestTerritorialSummary:
    def test_basic_summary(self) -> None:
        mock_client = MagicMock()
        mock_client.search_establishments.return_value = [
            _make_est("1", "HOSPITAL GERAL", surgical=True),
            _make_est("2", "HOSPITAL GERAL", obstetric=True),
            _make_est("3", "POSTO DE SAUDE", unit_type_code="1"),
        ]
        mock_client.get_health_regions.return_value = [
            _make_region(),
        ]
        engine = TerritorialEngine(mock_client)
        summary = engine.get_territorial_summary(state_code="35", city_code="3550308")

        assert summary.total_establishments == 3
        assert summary.type_distribution["HOSPITAL GERAL"] == 2
        assert summary.type_distribution["POSTO DE SAUDE"] == 1
        assert summary.has_surgical_center == 1
        assert summary.has_obstetric_center == 1
        assert summary.has_neonatal_center == 0
        assert summary.region_name == "Grande SP"

    def test_summary_no_state(self) -> None:
        mock_client = MagicMock()
        mock_client.search_establishments.return_value = []
        engine = TerritorialEngine(mock_client)
        summary = engine.get_territorial_summary()

        assert summary.total_establishments == 0
        assert summary.type_distribution == {}
        mock_client.get_health_regions.assert_not_called()

    def test_summary_city_not_in_regions(self) -> None:
        mock_client = MagicMock()
        mock_client.search_establishments.return_value = [_make_est()]
        mock_client.get_health_regions.return_value = [
            _make_region(city_code="9999999"),
        ]
        engine = TerritorialEngine(mock_client)
        summary = engine.get_territorial_summary(state_code="35", city_code="3550308")
        assert summary.region_name == ""


class TestFindNearby:
    def test_find_nearby(self) -> None:
        mock_client = MagicMock()
        mock_client.search_establishments.return_value = [
            _make_est("1"), _make_est("2"),
        ]
        engine = TerritorialEngine(mock_client)
        results = engine.find_nearby_establishments(city_code="3550308")
        assert len(results) == 2
        mock_client.search_establishments.assert_called_once_with(
            city_code="3550308",
            unit_type_code=None,
            active_only=True,
            limit=20,
            ctx=None,
        )

    def test_find_nearby_with_type(self) -> None:
        mock_client = MagicMock()
        mock_client.search_establishments.return_value = [_make_est()]
        engine = TerritorialEngine(mock_client)
        results = engine.find_nearby_establishments(city_code="3550308", unit_type_code="5")
        mock_client.search_establishments.assert_called_once_with(
            city_code="3550308",
            unit_type_code="5",
            active_only=True,
            limit=20,
            ctx=None,
        )


class TestRegionContext:
    def test_found(self) -> None:
        mock_client = MagicMock()
        r1 = _make_region("3550308", "SAO PAULO", "35001", "Grande SP", 12000000)
        r2 = _make_region("3509502", "CAMPINAS", "35002", "Campinas", 1200000)
        r3 = _make_region("3548500", "SANTOS", "35001", "Grande SP", 500000)
        mock_client.get_health_regions.return_value = [r1, r2, r3]

        engine = TerritorialEngine(mock_client)
        ctx = engine.get_region_context(city_code="3550308", state_code="35")

        assert ctx["found"] is True
        assert ctx["city_name"] == "SAO PAULO"
        assert ctx["region_name"] == "Grande SP"
        assert ctx["cities_in_region"] == 2  # SP + Santos
        assert ctx["total_population"] == 12500000  # 12M + 500K

    def test_not_found(self) -> None:
        mock_client = MagicMock()
        mock_client.get_health_regions.return_value = [
            _make_region("9999999"),
        ]
        engine = TerritorialEngine(mock_client)
        ctx = engine.get_region_context(city_code="3550308", state_code="35")
        assert ctx["found"] is False

    def test_empty_regions(self) -> None:
        mock_client = MagicMock()
        mock_client.get_health_regions.return_value = []
        engine = TerritorialEngine(mock_client)
        ctx = engine.get_region_context(city_code="3550308", state_code="35")
        assert ctx["found"] is False


class TestStaticHelpers:
    def test_count_by_type(self) -> None:
        ests = [
            _make_est("1", "HOSPITAL GERAL"),
            _make_est("2", "HOSPITAL GERAL"),
            _make_est("3", "UBS"),
        ]
        result = TerritorialEngine._count_by_type(ests)
        assert result == {"HOSPITAL GERAL": 2, "UBS": 1}

    def test_count_by_type_empty(self) -> None:
        assert TerritorialEngine._count_by_type([]) == {}

    def test_extract_capabilities(self) -> None:
        ests = [
            _make_est("1", surgical=True, obstetric=True, neonatal=True),
            _make_est("2", surgical=True),
            _make_est("3"),
        ]
        caps = TerritorialEngine._extract_capabilities(ests)
        assert caps == {"surgical": 2, "obstetric": 1, "neonatal": 1}

    def test_extract_capabilities_empty(self) -> None:
        caps = TerritorialEngine._extract_capabilities([])
        assert caps == {"surgical": 0, "obstetric": 0, "neonatal": 0}
