"""Configuracao do Zilda."""

from pydantic import field_validator

from intellicare_core.config import BaseModuleConfig


class ZildaConfig(BaseModuleConfig):
    """Configuracao especifica do Zilda."""

    module_name: str = "intellicare-zilda"
    module_version: str = "1.0.0"

    # CNES API
    cnes_base_url: str = "https://apidadosabertos.saude.gov.br"
    cnes_timeout: int = 30
    cnes_max_retries: int = 3

    # Cache TTLs (em segundos)
    cache_ttl_static: int = 604800  # 7 dias (tipos de unidade, municipios)
    cache_ttl_dynamic: int = 3600  # 1 hora (estabelecimentos)

    # Feature flags
    enable_datasus: bool = False  # v1.1.0
    enable_esus: bool = False  # v1.1.0

    @field_validator("cnes_timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v < 5:
            raise ValueError("cnes_timeout deve ser >= 5 segundos")
        return v
