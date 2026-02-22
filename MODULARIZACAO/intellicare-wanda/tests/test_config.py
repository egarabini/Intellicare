"""Testes da configuracao do Wanda."""

from wanda.config import WandaConfig


class TestConfig:
    def test_defaults(self):
        config = WandaConfig()
        assert config.module_name == "intellicare-wanda"
        assert config.module_version == "3.0.0"
        assert config.enable_ips_first is True
        assert config.enable_safety_guardrails is True
        assert config.max_modules_per_query == 3

    def test_module_urls(self):
        config = WandaConfig()
        urls = config.module_urls
        assert "intellicare-oswaldo" in urls
        assert "intellicare-florence" in urls
        assert "intellicare-zilda" in urls
        assert "intellicare-geralda" in urls
        assert len(urls) == 6

    def test_discovery_settings(self):
        config = WandaConfig()
        assert config.discovery_timeout_seconds == 5
        assert config.health_check_interval_seconds == 30
