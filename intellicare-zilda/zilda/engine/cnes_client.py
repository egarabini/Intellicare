"""Cliente CNES — consulta de dados do Cadastro Nacional de Estabelecimentos de Saude."""

import logging
from typing import Any

import httpx

from zilda.engine.cache import SimpleCache
from zilda.engine.models import CnesValidation, HealthEstablishment, HealthRegion, HealthUnitType

logger = logging.getLogger(__name__)


class CnesClient:
    """Cliente para a API de dados abertos do CNES/MS."""

    def __init__(
        self,
        base_url: str = "https://apidadosabertos.saude.gov.br",
        timeout: int = 30,
        cache_ttl_static: int = 604800,
        cache_ttl_dynamic: int = 3600,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._cache = SimpleCache()
        self._ttl_static = cache_ttl_static
        self._ttl_dynamic = cache_ttl_dynamic
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        """Fecha o client HTTP."""
        self._client.close()

    # --- Tipos de Unidade ---

    def get_unit_types(self, ctx: Any = None) -> list[HealthUnitType]:
        """Lista tipos de unidade de saude."""
        tenant_prefix = f"tenant:{ctx.tenant_id}:" if ctx and hasattr(ctx, "tenant_id") else ""
        cache_key = f"{tenant_prefix}unit_types"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._get("/cnes/tipounidades")
        types = [
            HealthUnitType(
                code=str(item.get("codigo_tipo_unidade", "")),
                description=item.get("descricao_tipo_unidade", ""),
            )
            for item in data
        ]
        self._cache.set(cache_key, types, self._ttl_static)
        return types

    # --- Estabelecimentos ---

    def search_establishments(
        self,
        state_code: str | None = None,
        city_code: str | None = None,
        unit_type_code: str | None = None,
        active_only: bool = True,
        limit: int = 20,
        offset: int = 0,
        ctx: Any = None,
    ) -> list[HealthEstablishment]:
        """Busca estabelecimentos de saude com filtros."""
        params: dict[str, Any] = {"limit": min(limit, 100), "offset": offset}
        if state_code:
            params["codigo_uf"] = state_code
        if city_code:
            params["codigo_municipio"] = city_code
        if unit_type_code:
            params["codigo_tipo_unidade"] = unit_type_code
        if active_only:
            params["status"] = 1

        tenant_prefix = f"tenant:{ctx.tenant_id}:" if ctx and hasattr(ctx, "tenant_id") else ""
        cache_key = f"{tenant_prefix}establishments:{hash(frozenset(params.items()))}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._get("/cnes/estabelecimentos", params)
        establishments = [self._parse_establishment(item) for item in data]
        self._cache.set(cache_key, establishments, self._ttl_dynamic)
        return establishments

    def get_establishment_by_cnes(self, cnes_code: str, ctx: Any = None) -> HealthEstablishment | None:
        """Busca estabelecimento por codigo CNES."""
        tenant_prefix = f"tenant:{ctx.tenant_id}:" if ctx and hasattr(ctx, "tenant_id") else ""
        cache_key = f"{tenant_prefix}establishment:{cnes_code}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._get("/cnes/estabelecimentos", {"codigo_cnes": cnes_code, "limit": 1})
        if not data:
            return None

        establishment = self._parse_establishment(data[0])
        self._cache.set(cache_key, establishment, self._ttl_dynamic)
        return establishment

    # --- Regioes de Saude ---

    def get_health_regions(
        self,
        state_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
        ctx: Any = None,
    ) -> list[HealthRegion]:
        """Lista municipios com suas regioes de saude."""
        params: dict[str, Any] = {"limit": min(limit, 100), "offset": offset}
        if state_code:
            params["codigo_uf"] = state_code

        tenant_prefix = f"tenant:{ctx.tenant_id}:" if ctx and hasattr(ctx, "tenant_id") else ""
        cache_key = f"{tenant_prefix}regions:{hash(frozenset(params.items()))}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        data = self._get("/macrorregiao-e-regiao-de-saude/municipio", params)
        regions = [self._parse_region(item) for item in data]
        self._cache.set(cache_key, regions, self._ttl_static)
        return regions

    # --- Validacao CNES ---

    def validate_cnes(self, cnes_code: str, ctx: Any = None) -> CnesValidation:
        """Valida um codigo CNES (formato + existencia)."""
        digits = "".join(c for c in cnes_code if c.isdigit())
        if len(digits) != 7:
            return CnesValidation(
                cnes_code=cnes_code,
                valid_format=False,
                found=False,
                message=f"CNES invalido: esperados 7 digitos, recebidos {len(digits)}",
            )

        establishment = self.get_establishment_by_cnes(digits, ctx=ctx)
        if establishment:
            return CnesValidation(
                cnes_code=digits,
                valid_format=True,
                found=True,
                establishment=establishment,
                message=f"CNES {digits} encontrado: {establishment.fantasy_name or establishment.legal_name}",
            )

        return CnesValidation(
            cnes_code=digits,
            valid_format=True,
            found=False,
            message=f"CNES {digits} com formato valido mas nao encontrado na base",
        )

    # --- Helpers ---

    def _get(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Faz GET na API e retorna lista de resultados."""
        url = f"{self._base_url}{path}"
        try:
            response = self._client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            # API retorna lista diretamente ou em wrapper
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("data", data.get("estabelecimentos", [data]))
            return []
        except httpx.HTTPStatusError as e:
            logger.error("CNES API error %d: %s", e.response.status_code, path)
            return []
        except httpx.RequestError as e:
            logger.error("CNES API request error: %s", e)
            return []

    def _parse_establishment(self, item: dict[str, Any]) -> HealthEstablishment:
        """Converte resposta da API em HealthEstablishment."""
        return HealthEstablishment(
            cnes_code=str(item.get("codigo_cnes", "")),
            cnpj=item.get("cnpj"),
            legal_name=item.get("nome_razao_social", ""),
            fantasy_name=item.get("nome_fantasia"),
            unit_type_code=str(item.get("codigo_tipo_unidade", "")),
            unit_type_description=item.get("descricao_tipo_unidade", ""),
            state_code=str(item.get("codigo_uf", "")),
            city_code=str(item.get("codigo_municipio", "")),
            city_name=item.get("nome_municipio", ""),
            address=item.get("endereco_estabelecimento"),
            neighborhood=item.get("bairro_estabelecimento"),
            phone=item.get("numero_telefone_estabelecimento"),
            latitude=self._safe_float(item.get("latitude_estabelecimento_decimo_grau")),
            longitude=self._safe_float(item.get("longitude_estabelecimento_decimo_grau")),
            has_surgical_center=item.get("estabelecimento_possui_centro_cirurgico") == 1,
            has_obstetric_center=item.get("estabelecimento_possui_centro_obstetrico") == 1,
            has_neonatal_center=item.get("estabelecimento_possui_centro_neonatal") == 1,
            active=item.get("codigo_motivo_desabilitacao") is None,
        )

    def _parse_region(self, item: dict[str, Any]) -> HealthRegion:
        """Converte resposta da API em HealthRegion."""
        return HealthRegion(
            city_code=str(item.get("codigo_municipio", "")),
            city_name=item.get("nome_municipio", ""),
            state_code=str(item.get("codigo_uf", "")),
            state_name=item.get("nome_uf", ""),
            region_code=str(item.get("codigo_regiao_saude", "")),
            region_name=item.get("nome_regiao_saude", ""),
            macro_region_code=str(item.get("codigo_macrorregiao_saude", "")),
            macro_region_name=item.get("nome_macrorregiao_saude", ""),
            population=item.get("populacao_ibge_2022"),
        )

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
