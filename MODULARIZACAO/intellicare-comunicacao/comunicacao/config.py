"""Configuracao do modulo de comunicacao Matrix."""

from pydantic import AliasChoices, Field

from intellicare_core.config import BaseModuleConfig


class ComunicacaoConfig(BaseModuleConfig):
    """Configuracao do modulo intellicare-comunicacao."""

    module_name: str = "intellicare-comunicacao"
    module_version: str = "0.1.0"
    database_url: str = Field(
        default="",
        validation_alias=AliasChoices("INTELLICARE_DATABASE_URL", "DATABASE_URL"),
    )
    database_schema: str = Field(
        default="intellicare_comunicacao",
        validation_alias=AliasChoices("INTELLICARE_DATABASE_SCHEMA", "DATABASE_SCHEMA"),
    )
    routing_operational_schema: str = Field(
        default="comunicacao_operacional",
        validation_alias=AliasChoices(
            "INTELLICARE_ROUTING_OPERATIONAL_SCHEMA",
            "ROUTING_OPERATIONAL_SCHEMA",
        ),
    )

    matrix_homeserver_url: str = Field(
        default="http://localhost:8008",
        validation_alias=AliasChoices("INTELLICARE_MATRIX_HOMESERVER_URL", "MATRIX_HOMESERVER_URL"),
    )
    matrix_username: str = Field(
        default="@intellicare_bot:localhost",
        validation_alias=AliasChoices("INTELLICARE_MATRIX_USERNAME", "MATRIX_USERNAME"),
    )
    matrix_password: str = Field(
        default="",
        validation_alias=AliasChoices("INTELLICARE_MATRIX_PASSWORD", "MATRIX_PASSWORD"),
    )
    matrix_device_id: str = Field(
        default="INTELLICARE_COMUNICACAO",
        validation_alias=AliasChoices("INTELLICARE_MATRIX_DEVICE_ID", "MATRIX_DEVICE_ID"),
    )
    matrix_default_room_id: str = Field(
        default="",
        validation_alias=AliasChoices("INTELLICARE_MATRIX_DEFAULT_ROOM_ID", "MATRIX_DEFAULT_ROOM_ID"),
    )
    matrix_enable_health_login_check: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "INTELLICARE_MATRIX_ENABLE_HEALTH_LOGIN_CHECK",
            "MATRIX_ENABLE_HEALTH_LOGIN_CHECK",
        ),
    )
    matrix_login_timeout_seconds: int = Field(
        default=20,
        validation_alias=AliasChoices(
            "INTELLICARE_MATRIX_LOGIN_TIMEOUT_SECONDS",
            "MATRIX_LOGIN_TIMEOUT_SECONDS",
        ),
    )
    matrix_send_timeout_seconds: int = Field(
        default=30,
        validation_alias=AliasChoices(
            "INTELLICARE_MATRIX_SEND_TIMEOUT_SECONDS",
            "MATRIX_SEND_TIMEOUT_SECONDS",
        ),
    )
    matrix_enable_event_consumer: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "INTELLICARE_MATRIX_ENABLE_EVENT_CONSUMER",
            "MATRIX_ENABLE_EVENT_CONSUMER",
        ),
    )
    matrix_enable_legacy_stack: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "INTELLICARE_MATRIX_ENABLE_LEGACY_STACK",
            "MATRIX_ENABLE_LEGACY_STACK",
        ),
    )
    event_stream_prefix: str = Field(
        default="intellicare",
        validation_alias=AliasChoices("INTELLICARE_EVENT_STREAM_PREFIX", "EVENT_STREAM_PREFIX"),
    )
    event_alert_type: str = Field(
        default="alert.created",
        validation_alias=AliasChoices("INTELLICARE_EVENT_ALERT_TYPE", "EVENT_ALERT_TYPE"),
    )
    event_poll_timeout_ms: int = Field(
        default=10_000,
        validation_alias=AliasChoices("INTELLICARE_EVENT_POLL_TIMEOUT_MS", "EVENT_POLL_TIMEOUT_MS"),
    )
    routing_enable_delayed_worker: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "INTELLICARE_ROUTING_ENABLE_DELAYED_WORKER",
            "ROUTING_ENABLE_DELAYED_WORKER",
        ),
    )
    routing_delayed_poll_seconds: int = Field(
        default=5,
        validation_alias=AliasChoices(
            "INTELLICARE_ROUTING_DELAYED_POLL_SECONDS",
            "ROUTING_DELAYED_POLL_SECONDS",
        ),
    )
    routing_ack_timeout_seconds: int = Field(
        default=300,
        validation_alias=AliasChoices(
            "INTELLICARE_ROUTING_ACK_TIMEOUT_SECONDS",
            "ROUTING_ACK_TIMEOUT_SECONDS",
        ),
    )
    routing_delayed_queue_key: str = Field(
        default="comm:scheduled_intents",
        validation_alias=AliasChoices(
            "INTELLICARE_ROUTING_DELAYED_QUEUE_KEY",
            "ROUTING_DELAYED_QUEUE_KEY",
        ),
    )
