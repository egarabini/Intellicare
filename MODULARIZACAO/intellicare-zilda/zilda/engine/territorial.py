"""Motor de analise territorial — agrega dados CNES por regiao."""

import logging
from collections import Counter
from typing import Any

from zilda.engine.cnes_client import CnesClient
from zilda.engine.models import HealthEstablishment, HealthRegion, TerritorialSummary

logger = logging.getLogger(__name__)


class TerritorialEngine:
    """Analisa contexto territorial de saude a partir de dados CNES."""

    def __init__(self, client: CnesClient) -> None:
        self._client = client

    def get_territorial_summary(
        self,
        state_code: str | None = None,
        city_code: str | None = None,
        limit: int = 100,
    ) -> TerritorialSummary:
        """Gera resumo territorial com estabelecimentos e distribuicao por tipo."""
        establishments = self._client.search_establishments(
            state_code=state_code,
            city_code=city_code,
            active_only=True,
            limit=limit,
        )

        type_distribution = self._count_by_type(establishments)
        capabilities = self._extract_capabilities(establishments)

        regions: list[HealthRegion] = []
        if state_code:
            regions = self._client.get_health_regions(state_code=state_code)

        region_name = ""
        if city_code and regions:
            for r in regions:
                if r.city_code == city_code:
                    region_name = r.region_name
                    break

        return TerritorialSummary(
            state_code=state_code or "",
            city_code=city_code or "",
            region_name=region_name,
            total_establishments=len(establishments),
            type_distribution=type_distribution,
            has_surgical_center=capabilities.get("surgical", 0),
            has_obstetric_center=capabilities.get("obstetric", 0),
            has_neonatal_center=capabilities.get("neonatal", 0),
            establishments=establishments,
        )

    def find_nearby_establishments(
        self,
        city_code: str,
        unit_type_code: str | None = None,
        limit: int = 20,
    ) -> list[HealthEstablishment]:
        """Busca estabelecimentos no municipio, opcionalmente filtrando por tipo."""
        return self._client.search_establishments(
            city_code=city_code,
            unit_type_code=unit_type_code,
            active_only=True,
            limit=limit,
        )

    def get_region_context(self, city_code: str, state_code: str) -> dict[str, Any]:
        """Retorna contexto da regiao de saude para um municipio."""
        regions = self._client.get_health_regions(state_code=state_code)

        city_region = None
        for r in regions:
            if r.city_code == city_code:
                city_region = r
                break

        if not city_region:
            return {
                "found": False,
                "city_code": city_code,
                "message": f"Municipio {city_code} nao encontrado nas regioes de saude",
            }

        same_region = [r for r in regions if r.region_code == city_region.region_code]
        total_population = sum(r.population or 0 for r in same_region)

        return {
            "found": True,
            "city_code": city_code,
            "city_name": city_region.city_name,
            "state_code": state_code,
            "state_name": city_region.state_name,
            "region_code": city_region.region_code,
            "region_name": city_region.region_name,
            "macro_region_code": city_region.macro_region_code,
            "macro_region_name": city_region.macro_region_name,
            "cities_in_region": len(same_region),
            "total_population": total_population,
            "population": city_region.population,
        }

    @staticmethod
    def _count_by_type(establishments: list[HealthEstablishment]) -> dict[str, int]:
        """Conta estabelecimentos por tipo."""
        counter: Counter[str] = Counter()
        for est in establishments:
            label = est.unit_type_description or est.unit_type_code
            counter[label] += 1
        return dict(counter.most_common())

    @staticmethod
    def _extract_capabilities(establishments: list[HealthEstablishment]) -> dict[str, int]:
        """Conta capacidades especiais (centros cirurgico, obstetrico, neonatal)."""
        caps: dict[str, int] = {"surgical": 0, "obstetric": 0, "neonatal": 0}
        for est in establishments:
            if est.has_surgical_center:
                caps["surgical"] += 1
            if est.has_obstetric_center:
                caps["obstetric"] += 1
            if est.has_neonatal_center:
                caps["neonatal"] += 1
        return caps
