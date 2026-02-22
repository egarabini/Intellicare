"""Configuracao do Geralda."""

from pathlib import Path

from intellicare_core.config import BaseModuleConfig


class GeraldaConfig(BaseModuleConfig):
    """Configuracao do modulo Geralda — acompanhamento do paciente."""

    module_name: str = "intellicare-geralda"
    module_version: str = "1.0.0"

    # Educacao em saude
    education_data_dir: str = str(
        Path(__file__).parent / "engine" / "education" / "data"
    )

    # Lembretes
    default_reminder_advance_minutes: int = 30
    max_reminders_per_patient: int = 50

    # Integracao (opcional)
    comunicacao_url: str = ""
    oswaldo_url: str = ""
    florence_url: str = ""
