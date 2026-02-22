"""
Configurações base para canais externos (D4).

Define classes de configuração compartilhadas entre os canais.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field


class BaseChannelConfig(BaseModel):
    """Configuração base para todos os canais."""

    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: int = 5

    class Config:
        """Pydantic config."""

        from_attributes = True


class ExternalChannelsConfig(BaseModel):
    """
    Configuração agregada de todos os canais externos.

    Carrega configurações de variáveis de ambiente.
    """

    # Push
    push_enabled: bool = Field(default=True)
    vapid_private_key: Optional[str] = Field(default=None)
    vapid_public_key: Optional[str] = Field(default=None)
    vapid_subject: str = Field(default="mailto:intellicare@gsi.srv.br")
    
    fcm_enabled: bool = Field(default=False)
    fcm_project_id: Optional[str] = Field(default=None)
    fcm_service_account_key_path: Optional[str] = Field(default=None)

    # WhatsApp
    whatsapp_enabled: bool = Field(default=True)
    whatsapp_graph_api_version: str = Field(default="v18.0")
    whatsapp_phone_number_id: Optional[str] = Field(default=None)
    whatsapp_business_account_id: Optional[str] = Field(default=None)
    whatsapp_access_token: Optional[str] = Field(default=None)
    whatsapp_webhook_verify_token: Optional[str] = Field(default=None)

    # SMS
    sms_enabled: bool = Field(default=True)
    sms_provider: str = Field(default="twilio")  # "twilio" | "zenvia" | "sns"
    
    # Twilio
    twilio_account_sid: Optional[str] = Field(default=None)
    twilio_auth_token: Optional[str] = Field(default=None)
    twilio_from_number: Optional[str] = Field(default=None)
    
    # Zenvia
    zenvia_api_token: Optional[str] = Field(default=None)
    zenvia_from: Optional[str] = Field(default=None)
    
    # Amazon SNS
    aws_region: Optional[str] = Field(default=None)
    aws_access_key: Optional[str] = Field(default=None)
    aws_secret_key: Optional[str] = Field(default=None)

    # Email
    email_enabled: bool = Field(default=True)
    smtp_host: str = Field(default="smtp.gsi.srv.br")
    smtp_port: int = Field(default=587)
    smtp_use_tls: bool = Field(default=True)
    smtp_username: str = Field(default="intellicare@gsi.srv.br")
    smtp_password: Optional[str] = Field(default=None)
    email_from: str = Field(default="intellicare@gsi.srv.br")
    email_from_name: str = Field(default="IntelliCare - Plataforma de Saúde")
    email_reply_to: str = Field(default="noreply@gsi.srv.br")
    email_template_dir: str = Field(default="comunicacao/templates/email")

    @classmethod
    def from_env(cls) -> "ExternalChannelsConfig":
        """
        Carrega configuração de variáveis de ambiente.

        Returns:
            ExternalChannelsConfig: Configuração carregada.
        """
        return cls(
            # Push
            push_enabled=os.getenv("PUSH_ENABLED", "true").lower() == "true",
            vapid_private_key=os.getenv("VAPID_PRIVATE_KEY"),
            vapid_public_key=os.getenv("VAPID_PUBLIC_KEY"),
            vapid_subject=os.getenv("VAPID_SUBJECT", "mailto:intellicare@gsi.srv.br"),
            
            fcm_enabled=os.getenv("FCM_ENABLED", "false").lower() == "true",
            fcm_project_id=os.getenv("FCM_PROJECT_ID"),
            fcm_service_account_key_path=os.getenv("FCM_SERVICE_ACCOUNT_KEY"),
            
            # WhatsApp
            whatsapp_enabled=os.getenv("WHATSAPP_ENABLED", "true").lower() == "true",
            whatsapp_graph_api_version=os.getenv("WHATSAPP_GRAPH_API_VERSION", "v18.0"),
            whatsapp_phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
            whatsapp_business_account_id=os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID"),
            whatsapp_access_token=os.getenv("WHATSAPP_ACCESS_TOKEN"),
            whatsapp_webhook_verify_token=os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN"),
            
            # SMS
            sms_enabled=os.getenv("SMS_ENABLED", "true").lower() == "true",
            sms_provider=os.getenv("SMS_PROVIDER", "twilio"),
            
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            twilio_from_number=os.getenv("TWILIO_FROM_NUMBER"),
            
            zenvia_api_token=os.getenv("ZENVIA_API_TOKEN"),
            zenvia_from=os.getenv("ZENVIA_FROM"),
            
            aws_region=os.getenv("AWS_REGION"),
            aws_access_key=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_key=os.getenv("AWS_SECRET_KEY"),
            
            # Email
            email_enabled=os.getenv("EMAIL_ENABLED", "true").lower() == "true",
            smtp_host=os.getenv("SMTP_HOST", "smtp.gsi.srv.br"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            smtp_username=os.getenv("SMTP_USERNAME", "intellicare@gsi.srv.br"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            email_from=os.getenv("EMAIL_FROM", "intellicare@gsi.srv.br"),
            email_from_name=os.getenv("EMAIL_FROM_NAME", "IntelliCare - Plataforma de Saúde"),
            email_reply_to=os.getenv("EMAIL_REPLY_TO", "noreply@gsi.srv.br"),
            email_template_dir=os.getenv("EMAIL_TEMPLATE_DIR", "comunicacao/templates/email"),
        )

    class Config:
        """Pydantic config."""

        from_attributes = True

