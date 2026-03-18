"""Configuracao do CarePlanner."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from intellicare_core.config.settings import REPO_ROOT


class CareplannerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / "infra" / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    kestra_url: str = "http://kestra:8080"
    kestra_api_key: str = ""
    kestra_timeout: float = 30.0

    rocketchat_url: str = "http://rocketchat:3001"
    rocketchat_bot_username: str = "intellicare_bot"
    rocketchat_bot_password: str = ""
    rocketchat_webhook_token: str = ""
    rocketchat_max_requests_per_second: int = 10
    rocketchat_max_retries: int = 3

    jitsi_base_url: str = "https://meet.intellicare.ia.br"
    jitsi_app_id: str = "intellicare"
    jitsi_app_secret: str = ""
    jitsi_default_room_duration: int = 120
    jitsi_max_participants: int = 10
    jicofo_auth_password: str = ""
    jvb_auth_password: str = ""

    # Evolution API (WhatsApp)
    evolution_api_url: str = "http://evolution-api:8080"
    evolution_api_key: str = ""
    evolution_instance_name: str = "intellicare"
    evolution_webhook_secret: str = ""
    evolution_max_retries: int = 3
    
    # Listmonk (E-mail transacional)
    listmonk_url: str = "http://listmonk:9000"
    listmonk_username: str = "intellicare"
    listmonk_password: str = ""
    listmonk_sender_email: str = "noreply@intellicare.ia.br"

    # Jasmin SMS Gateway
    jasmin_url: str = "http://jasmin:1401"
    jasmin_username: str = "admin"
    jasmin_password: str = ""
    jasmin_sender_id: str = "INTELLICARE"
    jasmin_webhook_secret: str = ""


@lru_cache
def get_careplanner_settings() -> CareplannerSettings:
    return CareplannerSettings()
