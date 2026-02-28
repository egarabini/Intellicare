"""Configuração do módulo intellicare-gestor."""

from intellicare_core.config import BaseModuleConfig


class GestorConfig(BaseModuleConfig):
    """Configuração do Gestor — estende BaseModuleConfig."""

    module_name: str = "intellicare-gestor"
    module_version: str = "1.0.0"

    # Porta do serviço
    gestor_port: int = 8011

    # Multi-tenancy — True em produção, False em dev local
    multi_tenant_enabled: bool = False

    # URL do banco do gestor (schema público ou tenant_{id})
    database_url: str = ""


config = GestorConfig()
