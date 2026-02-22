"""
Configuração para SMS (D4).

Define classes de configuração para múltiplos providers SMS.
"""

import os
from typing import Optional

from pydantic import BaseModel, Field


class TwilioConfig(BaseModel):
    """Configuração Twilio."""

    account_sid: str
    auth_token: str
    from_number: str  # Número Twilio (+1...)
    enabled: bool = True

    class Config:
        """Pydantic config."""

        from_attributes = True


class ZenviaConfig(BaseModel):
    """Configuração Zenvia."""

    api_token: str
    from_name: str  # Nome do remetente (ex: "IntelliCare")
    enabled: bool = True

    class Config:
        """Pydantic config."""

        from_attributes = True


class SNSConfig(BaseModel):
    """Configuração Amazon SNS."""

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"
    enabled: bool = True

    class Config:
        """Pydantic config."""

        from_attributes = True


class SMSConfig(BaseModel):
    """Configuração SMS (múltiplos providers)."""

    # Providers
    twilio: Optional[TwilioConfig] = None
    zenvia: Optional[ZenviaConfig] = None
    sns: Optional[SNSConfig] = None

    # Provider padrão
    default_provider: str = "twilio"  # "twilio" | "zenvia" | "sns"

    # Fallback chain
    fallback_providers: list[str] = Field(default_factory=lambda: ["twilio", "zenvia"])

    # Geral
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    max_message_length: int = 160

    @classmethod
    def from_env(cls) -> "SMSConfig":
        """
        Carrega configuração de variáveis de ambiente.

        Returns:
            SMSConfig: Configuração carregada.
        """
        # Twilio
        twilio = None
        if os.getenv("TWILIO_ACCOUNT_SID"):
            twilio = TwilioConfig(
                account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
                auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
                from_number=os.getenv("TWILIO_FROM_NUMBER", ""),
                enabled=os.getenv("TWILIO_ENABLED", "true").lower() == "true",
            )

        # Zenvia
        zenvia = None
        if os.getenv("ZENVIA_API_TOKEN"):
            zenvia = ZenviaConfig(
                api_token=os.getenv("ZENVIA_API_TOKEN", ""),
                from_name=os.getenv("ZENVIA_FROM_NAME", "IntelliCare"),
                enabled=os.getenv("ZENVIA_ENABLED", "true").lower() == "true",
            )

        # SNS
        sns = None
        if os.getenv("AWS_ACCESS_KEY_ID"):
            sns = SNSConfig(
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                aws_region=os.getenv("AWS_REGION", "us-east-1"),
                enabled=os.getenv("SNS_ENABLED", "true").lower() == "true",
            )

        return cls(
            twilio=twilio,
            zenvia=zenvia,
            sns=sns,
            default_provider=os.getenv("SMS_DEFAULT_PROVIDER", "twilio"),
            fallback_providers=os.getenv("SMS_FALLBACK_PROVIDERS", "twilio,zenvia").split(","),
            enabled=os.getenv("SMS_ENABLED", "true").lower() == "true",
            timeout_seconds=int(os.getenv("SMS_TIMEOUT", "30")),
            max_retries=int(os.getenv("SMS_MAX_RETRIES", "3")),
            max_message_length=int(os.getenv("SMS_MAX_MESSAGE_LENGTH", "160")),
        )

    class Config:
        """Pydantic config."""

        from_attributes = True

