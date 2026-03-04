"""Contrato e gerenciamento de dispatchers de canais."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
import inspect
from typing import Any, Protocol


class DeliveryStatus(str, Enum):
    """Status normalizado de entrega."""

    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    EXPIRED = "expired"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class ResolvedRecipient:
    """Destinatario resolvido para roteamento por canal."""

    recipient_id: str
    recipient_type: str
    channels: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RenderedContent:
    """Conteudo renderizado para um canal especifico."""

    format: str
    body: str
    subject: str | None = None
    title: str | None = None
    max_length: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChannelMessage:
    """Mensagem pronta para envio em um canal."""

    intent_id: str
    correlation_id: str
    channel: str
    recipient: ResolvedRecipient
    content: RenderedContent
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChannelHealth:
    """Estado de saude de um canal de envio."""

    channel: str
    available: bool
    status: str
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class DispatchResult:
    """Resultado padronizado de tentativa de envio."""

    success: bool
    channel_message_id: str | None = None
    channel_room_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ChannelCapabilities:
    """Capacidades de um canal de comunicação."""

    channel: str
    supports_read_receipt: bool = False
    supports_rich_content: bool = False
    supports_attachments: bool = False
    supports_interactive: bool = False
    max_message_length: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RecipientValidation:
    """Resultado de validação de destinatário."""

    valid: bool
    recipient_id: str
    channel_address: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ChannelDispatcher(Protocol):
    """Contrato completo esperado para canais do D1 (7 métodos obrigatórios)."""

    channel: str

    async def send(self, message: ChannelMessage, ctx: Any = None) -> DispatchResult:
        """Envia mensagem pelo canal. Método principal de dispatch."""
        ...

    async def get_status(self, channel_message_id: str, ctx: Any = None) -> DeliveryStatus:
        """Consulta status de entrega de uma mensagem específica."""
        ...

    async def cancel(self, channel_message_id: str, ctx: Any = None) -> bool:
        """Cancela envio pendente (se suportado pelo canal). Retorna True se cancelado."""
        ...

    async def health_check(self, ctx: Any = None) -> ChannelHealth:
        """Verifica saúde/disponibilidade do canal."""
        ...

    async def test_send(self, recipient: ResolvedRecipient, ctx: Any = None) -> DispatchResult:
        """Envia mensagem de teste sem persistir (para diagnóstico)."""
        ...

    async def get_capabilities(self, ctx: Any = None) -> ChannelCapabilities:
        """Retorna capacidades do canal (read receipts, rich content, etc)."""
        ...

    async def validate_recipient(self, recipient: ResolvedRecipient, ctx: Any = None) -> RecipientValidation:
        """Valida se destinatário é válido para este canal."""
        ...


class DispatcherManager:
    """Registro central de dispatchers por canal."""

    def __init__(self) -> None:
        self._dispatchers: dict[str, ChannelDispatcher] = {}

    def register(self, dispatcher: ChannelDispatcher) -> None:
        """Registra um dispatcher para um canal específico."""
        self._dispatchers[dispatcher.channel] = dispatcher

    def get_dispatcher(self, channel: str) -> ChannelDispatcher | None:
        """Retorna dispatcher registrado para o canal."""
        return self._dispatchers.get(channel)

    def list_channels(self) -> list[str]:
        """Lista todos os canais registrados."""
        return sorted(self._dispatchers.keys())

    async def dispatch(self, channel: str, message: ChannelMessage, ctx: Any = None) -> DispatchResult:
        """Despacha mensagem para o canal especificado."""
        dispatcher = self.get_dispatcher(channel=channel)
        if dispatcher is None:
            return DispatchResult(
                success=False,
                error_code="channel_not_registered",
                error_message=f"canal nao registrado: {channel}",
            )
        return await dispatcher.send(message)

    async def get_status(self, channel: str, channel_message_id: str, ctx: Any = None) -> DeliveryStatus:
        """Consulta status de entrega de uma mensagem."""
        dispatcher = self.get_dispatcher(channel=channel)
        if dispatcher is None:
            return DeliveryStatus.UNKNOWN
        if hasattr(dispatcher, "get_status"):
            return await dispatcher.get_status(channel_message_id)  # type: ignore[attr-defined]
        if hasattr(dispatcher, "check_delivery_status"):
            return await dispatcher.check_delivery_status(channel_message_id)  # type: ignore[attr-defined]
        return DeliveryStatus.UNKNOWN

    async def cancel(self, channel: str, channel_message_id: str, ctx: Any = None) -> bool:
        """Cancela envio pendente."""
        dispatcher = self.get_dispatcher(channel=channel)
        if dispatcher is None:
            return False
        if hasattr(dispatcher, "cancel"):
            return await dispatcher.cancel(channel_message_id)  # type: ignore[attr-defined]
        return False

    async def health_check(self, channel: str, ctx: Any = None) -> ChannelHealth | None:
        """Verifica saúde de um canal."""
        dispatcher = self.get_dispatcher(channel=channel)
        if dispatcher is None:
            return None
        if hasattr(dispatcher, "health_check"):
            return await dispatcher.health_check()  # type: ignore[attr-defined]
        if hasattr(dispatcher, "get_health"):
            return await dispatcher.get_health()  # type: ignore[attr-defined]
        if hasattr(dispatcher, "is_available"):
            available = await dispatcher.is_available()  # type: ignore[attr-defined]
            return ChannelHealth(channel=channel, available=available, status="up" if available else "down")
        return ChannelHealth(channel=channel, available=False, status="unknown")

    async def get_health(self, channel: str, ctx: Any = None) -> ChannelHealth | None:
        """Alias de compatibilidade para health_check()."""
        return await self.health_check(channel)

    async def test_send(self, channel: str, recipient: ResolvedRecipient, ctx: Any = None) -> DispatchResult:
        """Envia mensagem de teste."""
        dispatcher = self.get_dispatcher(channel=channel)
        if dispatcher is None:
            return DispatchResult(
                success=False,
                error_code="channel_not_registered",
                error_message=f"canal nao registrado: {channel}",
            )
        if hasattr(dispatcher, "test_send"):
            return await dispatcher.test_send(recipient)  # type: ignore[attr-defined]
        if hasattr(dispatcher, "send"):
            message = ChannelMessage(
                intent_id="test-intent",
                correlation_id="test-correlation",
                channel=channel,
                recipient=recipient,
                content=RenderedContent(format="plain", body="Mensagem de teste"),
            )
            return await dispatcher.send(message)  # type: ignore[attr-defined]
        return DispatchResult(success=False, error_code="not_implemented", error_message="test_send indisponivel")

    async def get_capabilities(self, channel: str, ctx: Any = None) -> ChannelCapabilities | None:
        """Retorna capacidades de um canal."""
        dispatcher = self.get_dispatcher(channel=channel)
        if dispatcher is None:
            return None
        if hasattr(dispatcher, "get_capabilities"):
            raw = dispatcher.get_capabilities()  # type: ignore[attr-defined]
            result = await raw if inspect.isawaitable(raw) else raw
            if isinstance(result, ChannelCapabilities):
                return result
            if isinstance(result, dict):
                return ChannelCapabilities(
                    channel=channel,
                    supports_read_receipt=bool(result.get("read_receipt", False)),
                    supports_rich_content=bool(result.get("rich_content", False)),
                    supports_attachments=bool(result.get("attachments", False)),
                    supports_interactive=bool(result.get("interactive", False)),
                    metadata={"raw": result},
                )
            return ChannelCapabilities(channel=channel)
        supports_read = False
        supports_rich = False
        if hasattr(dispatcher, "supports_read_receipt"):
            supports_read = bool(await dispatcher.supports_read_receipt())  # type: ignore[attr-defined]
        if hasattr(dispatcher, "supports_rich_content"):
            supports_rich = bool(await dispatcher.supports_rich_content())  # type: ignore[attr-defined]
        return ChannelCapabilities(
            channel=channel,
            supports_read_receipt=supports_read,
            supports_rich_content=supports_rich,
        )

    async def validate_recipient(self, channel: str, recipient: ResolvedRecipient, ctx: Any = None) -> RecipientValidation:
        """Valida destinatário para um canal."""
        dispatcher = self.get_dispatcher(channel=channel)
        if dispatcher is None:
            return RecipientValidation(
                valid=False,
                recipient_id=recipient.recipient_id,
                error_code="channel_not_registered",
                error_message=f"canal nao registrado: {channel}",
            )
        raw = dispatcher.validate_recipient(recipient)
        result = await raw if inspect.isawaitable(raw) else raw
        if isinstance(result, RecipientValidation):
            return result
        if isinstance(result, tuple) and len(result) == 2:
            valid, error_message = result
            return RecipientValidation(
                valid=bool(valid),
                recipient_id=recipient.recipient_id,
                error_message=error_message,
            )
        return RecipientValidation(valid=False, recipient_id=recipient.recipient_id, error_message="invalid_result")


def get_default_dispatcher_manager() -> DispatcherManager | None:
    """Returns None — use create_default_dispatcher_manager() or get manager from _state."""
    return None


def create_default_dispatcher_manager() -> DispatcherManager:
    """
    Cria DispatcherManager com todos os dispatchers padrão registrados.

    Dispatchers incluídos:
    - RocketChatDispatcher (stack oficial V5)
    - EmailDispatcher
    - SMSDispatcher
    - WhatsAppDispatcher
    - PushDispatcher
    - JitsiDispatcher
    """
    # Import aqui para evitar dependências circulares
    from comunicacao.dispatchers.email_dispatcher import EmailDispatcher
    from comunicacao.dispatchers.jitsi_dispatcher import JitsiDispatcher
    from comunicacao.dispatchers.push_dispatcher import PushDispatcher
    from comunicacao.dispatchers.rocketchat_dispatcher import RocketChatDispatcher
    from comunicacao.dispatchers.sms_dispatcher import SMSDispatcher
    from comunicacao.dispatchers.whatsapp_dispatcher import WhatsAppDispatcher

    manager = DispatcherManager()

    # Registra todos os dispatchers
    manager.register(RocketChatDispatcher())
    manager.register(EmailDispatcher())
    manager.register(SMSDispatcher())
    manager.register(WhatsAppDispatcher())
    manager.register(PushDispatcher())
    manager.register(JitsiDispatcher())

    return manager
