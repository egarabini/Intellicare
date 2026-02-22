"""Testes para modelos de dados do Zilda."""

from zilda.engine.models import (
    CnesValidation,
    HealthEstablishment,
    HealthRegion,
    HealthUnitType,
    TerritorialSummary,
)


class TestHealthUnitType:
    def test_to_dict(self) -> None:
        t = HealthUnitType(code="5", description="HOSPITAL GERAL")
        d = t.to_dict()
        assert d["code"] == "5"
        assert d["description"] == "HOSPITAL GERAL"


class TestHealthEstablishment:
    def test_to_dict_full(self) -> None:
        est = HealthEstablishment(
            cnes_code="2077485",
            cnpj="12345678000199",
            legal_name="Hospital X",
            fantasy_name="Hosp X",
            unit_type_code="5",
            unit_type_description="HOSPITAL GERAL",
            state_code="35",
            city_code="3550308",
            city_name="SAO PAULO",
            address="Rua A 1",
            neighborhood="Centro",
            phone="11999999999",
            latitude=-23.55,
            longitude=-46.63,
            has_surgical_center=True,
            has_obstetric_center=False,
            has_neonatal_center=True,
            active=True,
        )
        d = est.to_dict()
        assert d["cnes_code"] == "2077485"
        assert d["has_surgical_center"] is True
        assert d["has_obstetric_center"] is False
        assert d["latitude"] == -23.55

    def test_to_dict_minimal(self) -> None:
        est = HealthEstablishment(
            cnes_code="1111111",
            cnpj=None,
            legal_name="UBS",
            fantasy_name=None,
            unit_type_code="1",
            unit_type_description="POSTO",
            state_code="35",
            city_code="3550308",
            city_name="SP",
            address=None,
            neighborhood=None,
            phone=None,
        )
        d = est.to_dict()
        assert d["cnpj"] is None
        assert d["latitude"] is None
        assert d["active"] is True


class TestHealthRegion:
    def test_to_dict(self) -> None:
        r = HealthRegion(
            city_code="3550308",
            city_name="SAO PAULO",
            state_code="35",
            state_name="SAO PAULO",
            region_code="35001",
            region_name="Grande SP",
            macro_region_code="35000",
            macro_region_name="Macro SP",
            population=12000000,
        )
        d = r.to_dict()
        assert d["region_code"] == "35001"
        assert d["population"] == 12000000

    def test_to_dict_no_population(self) -> None:
        r = HealthRegion(
            city_code="1",
            city_name="X",
            state_code="11",
            state_name="RO",
            region_code="11001",
            region_name="R",
            macro_region_code="11000",
            macro_region_name="M",
        )
        assert r.to_dict()["population"] is None


class TestTerritorialSummary:
    def test_to_dict(self) -> None:
        est = HealthEstablishment(
            cnes_code="1", cnpj=None, legal_name="X", fantasy_name=None,
            unit_type_code="1", unit_type_description="UBS",
            state_code="35", city_code="3550308", city_name="SP",
            address=None, neighborhood=None, phone=None,
        )
        summary = TerritorialSummary(
            state_code="35",
            city_code="3550308",
            region_name="Grande SP",
            total_establishments=1,
            type_distribution={"UBS": 1},
            has_surgical_center=0,
            has_obstetric_center=0,
            has_neonatal_center=0,
            establishments=[est],
        )
        d = summary.to_dict()
        assert d["total_establishments"] == 1
        assert d["type_distribution"] == {"UBS": 1}
        assert len(d["establishments"]) == 1

    def test_to_dict_empty(self) -> None:
        summary = TerritorialSummary(
            state_code="35",
            city_code="",
            region_name="",
            total_establishments=0,
            type_distribution={},
        )
        d = summary.to_dict()
        assert d["total_establishments"] == 0
        assert d["establishments"] == []


class TestCnesValidation:
    def test_valid_found(self) -> None:
        est = HealthEstablishment(
            cnes_code="2077485", cnpj=None, legal_name="H", fantasy_name="H",
            unit_type_code="5", unit_type_description="HOSP",
            state_code="35", city_code="3550308", city_name="SP",
            address=None, neighborhood=None, phone=None,
        )
        v = CnesValidation(
            cnes_code="2077485", valid_format=True, found=True,
            establishment=est, message="OK",
        )
        d = v.to_dict()
        assert d["valid_format"] is True
        assert d["found"] is True
        assert d["establishment"]["cnes_code"] == "2077485"

    def test_invalid_format(self) -> None:
        v = CnesValidation(
            cnes_code="123", valid_format=False, found=False,
            message="Formato invalido",
        )
        d = v.to_dict()
        assert d["valid_format"] is False
        assert d["establishment"] is None

    def test_valid_not_found(self) -> None:
        v = CnesValidation(
            cnes_code="9999999", valid_format=True, found=False,
            message="Nao encontrado",
        )
        d = v.to_dict()
        assert d["valid_format"] is True
        assert d["found"] is False
