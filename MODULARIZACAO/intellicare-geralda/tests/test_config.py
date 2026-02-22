"""Testes da configuracao do Geralda."""

from geralda.config import GeraldaConfig


class TestConfig:
    def test_defaults(self):
        config = GeraldaConfig()
        assert config.module_name == "intellicare-geralda"
        assert config.module_version == "1.0.0"
        assert config.default_reminder_advance_minutes == 30
        assert config.max_reminders_per_patient == 50

    def test_education_data_dir(self):
        config = GeraldaConfig()
        assert "education" in config.education_data_dir
        assert "data" in config.education_data_dir
