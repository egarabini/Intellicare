"""Testes para ZildaConfig."""

from zilda.config import ZildaConfig


class TestZildaConfig:
    def test_defaults(self) -> None:
        config = ZildaConfig()
        assert config.module_name == "intellicare-zilda"
        assert config.module_version == "1.0.0"
        assert config.cnes_base_url == "https://apidadosabertos.saude.gov.br"
        assert config.cnes_timeout == 30
        assert config.cache_ttl_static == 604800
        assert config.cache_ttl_dynamic == 3600
        assert config.enable_datasus is False
        assert config.enable_esus is False

    def test_custom_values(self) -> None:
        config = ZildaConfig(
            cnes_base_url="http://localhost:8080",
            cnes_timeout=10,
            cache_ttl_dynamic=300,
        )
        assert config.cnes_base_url == "http://localhost:8080"
        assert config.cnes_timeout == 10
        assert config.cache_ttl_dynamic == 300
