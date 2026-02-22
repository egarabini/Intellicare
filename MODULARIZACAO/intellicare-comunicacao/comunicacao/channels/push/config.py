"""
Configuração para Push Notifications (D4).

Define classes de configuração para VAPID e FCM.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field


class VAPIDConfig(BaseModel):
    """Configuração VAPID para Web Push."""

    private_key: str  # VAPID private key (base64url)
    public_key: str  # VAPID public key (base64url)
    subject: str = "mailto:intellicare@gsi.srv.br"
    ttl: int = 86400  # Time-to-live em segundos (24h)

    class Config:
        """Pydantic config."""

        from_attributes = True


class FCMConfig(BaseModel):
    """Configuração Firebase Cloud Messaging."""

    project_id: str
    service_account_key_path: str  # Caminho para o JSON da service account
    default_topic: str = "intellicare-alerts"

    class Config:
        """Pydantic config."""

        from_attributes = True


class PushConfig(BaseModel):
    """Configuração agregada de Push Notifications."""

    vapid: VAPIDConfig
    fcm: Optional[FCMConfig] = None
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "PushConfig":
        """
        Carrega configuração de variáveis de ambiente.

        Returns:
            PushConfig: Configuração carregada.

        Raises:
            ValueError: Se VAPID keys não estiverem configuradas.
        """
        vapid_private = os.getenv("VAPID_PRIVATE_KEY")
        vapid_public = os.getenv("VAPID_PUBLIC_KEY")

        if not vapid_private or not vapid_public:
            raise ValueError("VAPID_PRIVATE_KEY e VAPID_PUBLIC_KEY são obrigatórios")

        vapid_config = VAPIDConfig(
            private_key=vapid_private,
            public_key=vapid_public,
            subject=os.getenv("VAPID_SUBJECT", "mailto:intellicare@gsi.srv.br"),
            ttl=int(os.getenv("VAPID_TTL", "86400")),
        )

        fcm_config = None
        if os.getenv("FCM_ENABLED", "false").lower() == "true":
            fcm_project_id = os.getenv("FCM_PROJECT_ID")
            fcm_key_path = os.getenv("FCM_SERVICE_ACCOUNT_KEY")

            if fcm_project_id and fcm_key_path:
                fcm_config = FCMConfig(
                    project_id=fcm_project_id,
                    service_account_key_path=fcm_key_path,
                    default_topic=os.getenv("FCM_DEFAULT_TOPIC", "intellicare-alerts"),
                )

        return cls(
            vapid=vapid_config,
            fcm=fcm_config,
            enabled=os.getenv("PUSH_ENABLED", "true").lower() == "true",
            timeout_seconds=int(os.getenv("PUSH_TIMEOUT", "30")),
            max_retries=int(os.getenv("PUSH_MAX_RETRIES", "3")),
        )

    class Config:
        """Pydantic config."""

        from_attributes = True

