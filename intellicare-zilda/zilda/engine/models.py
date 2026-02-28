"""Modelos de dados do Zilda."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HealthUnitType:
    """Tipo de unidade de saude CNES."""

    code: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "description": self.description}


@dataclass
class HealthEstablishment:
    """Estabelecimento de saude do CNES."""

    cnes_code: str
    cnpj: str | None
    legal_name: str
    fantasy_name: str | None
    unit_type_code: str
    unit_type_description: str
    state_code: str
    city_code: str
    city_name: str
    address: str | None
    neighborhood: str | None
    phone: str | None
    latitude: float | None = None
    longitude: float | None = None
    has_surgical_center: bool = False
    has_obstetric_center: bool = False
    has_neonatal_center: bool = False
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "cnes_code": self.cnes_code,
            "cnpj": self.cnpj,
            "legal_name": self.legal_name,
            "fantasy_name": self.fantasy_name,
            "unit_type_code": self.unit_type_code,
            "unit_type_description": self.unit_type_description,
            "state_code": self.state_code,
            "city_code": self.city_code,
            "city_name": self.city_name,
            "address": self.address,
            "neighborhood": self.neighborhood,
            "phone": self.phone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "has_surgical_center": self.has_surgical_center,
            "has_obstetric_center": self.has_obstetric_center,
            "has_neonatal_center": self.has_neonatal_center,
            "active": self.active,
        }


@dataclass
class HealthRegion:
    """Regiao de saude com dados do municipio."""

    city_code: str
    city_name: str
    state_code: str
    state_name: str
    region_code: str
    region_name: str
    macro_region_code: str
    macro_region_name: str
    population: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "city_code": self.city_code,
            "city_name": self.city_name,
            "state_code": self.state_code,
            "state_name": self.state_name,
            "region_code": self.region_code,
            "region_name": self.region_name,
            "macro_region_code": self.macro_region_code,
            "macro_region_name": self.macro_region_name,
            "population": self.population,
        }


@dataclass
class TerritorialSummary:
    """Resumo territorial de uma regiao de saude."""

    state_code: str
    city_code: str
    region_name: str
    total_establishments: int
    type_distribution: dict[str, int]
    has_surgical_center: int = 0
    has_obstetric_center: int = 0
    has_neonatal_center: int = 0
    establishments: list["HealthEstablishment"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_code": self.state_code,
            "city_code": self.city_code,
            "region_name": self.region_name,
            "total_establishments": self.total_establishments,
            "type_distribution": self.type_distribution,
            "has_surgical_center": self.has_surgical_center,
            "has_obstetric_center": self.has_obstetric_center,
            "has_neonatal_center": self.has_neonatal_center,
            "establishments": [e.to_dict() for e in self.establishments],
        }


@dataclass
class CnesValidation:
    """Resultado de validacao de codigo CNES."""

    cnes_code: str
    valid_format: bool
    found: bool
    establishment: HealthEstablishment | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "cnes_code": self.cnes_code,
            "valid_format": self.valid_format,
            "found": self.found,
            "establishment": self.establishment.to_dict() if self.establishment else None,
            "message": self.message,
        }
