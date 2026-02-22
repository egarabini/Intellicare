"""Configuração do Rocket.Chat."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RocketChatConfig(BaseModel):
    """Configuração do Rocket.Chat."""
    
    # Servidor
    url: str = Field(
        "https://rocket.gsi.srv.br",
        description="URL do servidor Rocket.Chat"
    )
    
    # Autenticação do Bot
    bot_username: str = Field(
        "intellicare-bot",
        description="Username do bot"
    )
    bot_password: str = Field(
        ...,
        description="Senha do bot (obrigatório)"
    )
    
    # Autenticação Admin (opcional, para operações administrativas)
    admin_user_id: str | None = Field(
        None,
        description="User ID do admin (para operações admin)"
    )
    admin_auth_token: str | None = Field(
        None,
        description="Auth token do admin (para operações admin)"
    )
    
    # Timeouts
    connect_timeout: int = Field(
        10,
        description="Timeout de conexão (segundos)",
        ge=1,
        le=60
    )
    request_timeout: int = Field(
        30,
        description="Timeout de requisição (segundos)",
        ge=1,
        le=300
    )
    
    # Rate Limiting
    max_requests_per_second: int = Field(
        10,
        description="Máximo de requisições por segundo",
        ge=1,
        le=100
    )
    
    # Canais Padrão
    default_alert_channel: str = Field(
        "alertas-clinicos",
        description="Canal padrão para alertas clínicos"
    )
    default_team_channel_prefix: str = Field(
        "equipe-",
        description="Prefixo para canais de equipe"
    )
    default_case_channel_prefix: str = Field(
        "caso-",
        description="Prefixo para canais de caso clínico"
    )
    
    # Webhook
    webhook_token: str | None = Field(
        None,
        description="Token para validar webhooks incoming"
    )
    
    # Retry
    max_retries: int = Field(
        3,
        description="Número máximo de tentativas em caso de erro",
        ge=0,
        le=10
    )
    retry_delay: float = Field(
        1.0,
        description="Delay entre tentativas (segundos)",
        ge=0.1,
        le=60.0
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://rocket.gsi.srv.br",
                "bot_username": "intellicare-bot",
                "bot_password": "strong_password_here",
                "admin_user_id": "69921c312277eacd60658bc4",
                "admin_auth_token": "admin_token_here",
                "connect_timeout": 10,
                "request_timeout": 30,
                "max_requests_per_second": 10,
                "default_alert_channel": "alertas-clinicos",
                "default_team_channel_prefix": "equipe-",
                "default_case_channel_prefix": "caso-",
                "webhook_token": "webhook_secret_token",
                "max_retries": 3,
                "retry_delay": 1.0,
            }
        }
    
    @classmethod
    def from_env(cls) -> RocketChatConfig:
        """Cria configuração a partir de variáveis de ambiente."""
        import os
        
        return cls(
            url=os.getenv("ROCKETCHAT_URL", "https://rocket.gsi.srv.br"),
            bot_username=os.getenv("ROCKETCHAT_BOT_USERNAME", "intellicare-bot"),
            bot_password=os.getenv("ROCKETCHAT_BOT_PASSWORD", ""),
            admin_user_id=os.getenv("ROCKETCHAT_ADMIN_USER_ID"),
            admin_auth_token=os.getenv("ROCKETCHAT_ADMIN_AUTH_TOKEN"),
            connect_timeout=int(os.getenv("ROCKETCHAT_CONNECT_TIMEOUT", "10")),
            request_timeout=int(os.getenv("ROCKETCHAT_REQUEST_TIMEOUT", "30")),
            max_requests_per_second=int(os.getenv("ROCKETCHAT_MAX_REQUESTS_PER_SECOND", "10")),
            default_alert_channel=os.getenv("ROCKETCHAT_DEFAULT_ALERT_CHANNEL", "alertas-clinicos"),
            default_team_channel_prefix=os.getenv("ROCKETCHAT_TEAM_CHANNEL_PREFIX", "equipe-"),
            default_case_channel_prefix=os.getenv("ROCKETCHAT_CASE_CHANNEL_PREFIX", "caso-"),
            webhook_token=os.getenv("ROCKETCHAT_WEBHOOK_TOKEN"),
            max_retries=int(os.getenv("ROCKETCHAT_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("ROCKETCHAT_RETRY_DELAY", "1.0")),
        )

