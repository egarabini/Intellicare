"""Configuration for intellicare-admin module."""

from pydantic import AliasChoices, Field

from intellicare_core.config import BaseModuleConfig


class AdminConfig(BaseModuleConfig):
    """Platform administration configuration."""

    module_name: str = "intellicare-admin"
    module_version: str = "1.0.0"

    # Database URL with validation alias for INTELLICARE_ADMIN_DATABASE_URL
    database_url: str = Field(
        default="",
        validation_alias=AliasChoices("INTELLICARE_ADMIN_DATABASE_URL", "INTELLICARE_DATABASE_URL"),
    )

    # Database (schema platform)
    platform_schema: str = "platform"

    # Keycloak Admin
    keycloak_admin_url: str = "https://keycloak.gsi.srv.br"
    keycloak_admin_realm: str = "master"
    keycloak_admin_username: str = ""
    keycloak_admin_password: str = ""
    keycloak_target_realm: str = "intellicare"

    # Provisioning
    migration_script_path: str = "./migrations"

    # Trial
    trial_duration_days: int = 30

    # Billing
    billing_grace_period_days: int = 15

