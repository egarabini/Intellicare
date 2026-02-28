import logging
from datetime import datetime, UTC
from uuid import uuid4
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.models import ExternalMessageLog, ExternalMessageStatus
from comunicacao.channels.email.config import EmailConfig
from comunicacao.channels.email.providers.smtp import SMTPEmailProvider
from comunicacao.channels.email.models import EmailMessage as InternalEmailMessage, EmailStatus
from comunicacao.channels.email.templates import EmailTemplateEngine
from comunicacao.dispatchers.base import (
    ChannelMessage,
    DispatchResult,
    DeliveryStatus,
    ChannelHealth,
    ChannelCapabilities,
    ResolvedRecipient,
    RecipientValidation,
    RenderedContent,
    ChannelDispatcher,
)

logger = logging.getLogger("comunicacao.channels.email.dispatcher")

class EmailDispatcher(ChannelDispatcher):
    """Dispatcher for Email using SMTP provider."""
    
    channel = "email"
    
    def __init__(self, db: AsyncSession, config: EmailConfig):
        self._db = db
        self._config = config
        self.template_engine = EmailTemplateEngine(self._config.templates_dir)
        
        # Initialize provider (currently only SMTP)
        self.provider = SMTPEmailProvider(self._config.smtp)
        
    async def send(self, message: ChannelMessage) -> DispatchResult:
        """
        Sends an email using the configured provider.
        """
        try:
            # Extract data
            recipient_email = message.recipient.recipient_id
            subject = message.content.subject or "No Subject"
            body_text = message.content.body if message.content.format == "text" else None
            body_html = message.content.body if message.content.format == "html" else None
            
            # Template handling via metadata
            template_name = message.metadata.get("template_name")
            context = message.metadata.get("context", {})
            
            if template_name:
                try:
                    # If using template, body becomes the rendered HTML
                    rendered = self.template_engine.render(template_name, context)
                    body_html = rendered
                    if not body_text:
                        body_text = "Please view this email in an HTML-compatible client."
                except Exception as e:
                    logger.error(f"Template rendering failed: {e}")
                    # Continue if we have some body, otherwise might fail
            
            # Map to internal model for provider
            internal_message = InternalEmailMessage(
                id=str(uuid4()),
                recipient=recipient_email,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                context=context,
                template_name=template_name
            )
            
            logger.info(f"Sending Email: to={recipient_email}, subject={subject}")
            
            # Send using provider
            success = self.provider.send(internal_message)
            
            # Determine status
            status = ExternalMessageStatus.SENT if success else ExternalMessageStatus.FAILED
            
            # Log to DB
            log = ExternalMessageLog(
                channel=self.channel,
                direction="outbound",
                intent_id=message.intent_id,
                correlation_id=message.correlation_id,
                recipient_id=recipient_email,
                provider_message_id=internal_message.id, # SMTP doesn't always give an ID, using internal
                status=status,
                message_content={
                    "subject": subject,
                    "template": template_name,
                    "provider": "smtp"
                },
                sent_at=datetime.now(UTC)
            )
            
            self._db.add(log)
            await self._db.commit()
            
            if success:
                return DispatchResult(
                    success=True,
                    channel_message_id=internal_message.id,
                    metadata={"provider": "smtp"}
                )
            else:
                return DispatchResult(
                    success=False,
                    error_code="send_failed",
                    error_message=internal_message.error_message or "Unknown error"
                )
                
        except Exception as exc:
            logger.error(f"Error sending email: {exc}", exc_info=True)
            return DispatchResult(
                success=False,
                error_code="exception",
                error_message=str(exc)
            )

    async def get_status(self, channel_message_id: str) -> DeliveryStatus:
        """Query status of a message."""
        stmt = select(ExternalMessageLog).where(
            ExternalMessageLog.provider_message_id == channel_message_id
        )
        result = await self._db.execute(stmt)
        log = result.scalar_one_or_none()
        
        if not log:
            return DeliveryStatus.UNKNOWN
            
        status_map = {
            ExternalMessageStatus.PENDING: DeliveryStatus.PENDING,
            ExternalMessageStatus.SENT: DeliveryStatus.SENT,
            ExternalMessageStatus.DELIVERED: DeliveryStatus.DELIVERED,
            ExternalMessageStatus.FAILED: DeliveryStatus.FAILED,
        }
        return status_map.get(log.status, DeliveryStatus.UNKNOWN)

    async def cancel(self, channel_message_id: str) -> bool:
        """Email does not support cancellation."""
        return False

    async def health_check(self) -> ChannelHealth:
        """Checks health of the email channel."""
        provider_health = self.provider.health_check()
        is_healthy = provider_health.get("status") == "healthy"
        
        return ChannelHealth(
            channel=self.channel,
            available=is_healthy,
            status="healthy" if is_healthy else "unavailable",
            details={
                "providers": {"smtp": provider_health}
            }
        )

    async def test_send(self, recipient: ResolvedRecipient) -> DispatchResult:
        """Sends a test email."""
        message = ChannelMessage(
            intent_id="test-intent",
            correlation_id=f"test-{uuid4()}",
            channel=self.channel,
            recipient=recipient,
            content=RenderedContent(
                format="text",
                body="This is a test email from IntelliCare.",
                subject="IntelliCare Test"
            ),
            metadata={"test": True}
        )
        return await self.send(message)

    async def get_capabilities(self) -> ChannelCapabilities:
        """Returns channel capabilities."""
        return ChannelCapabilities(
            channel=self.channel,
            supports_read_receipt=False,
            supports_rich_content=True, # HTML support
            supports_attachments=True,
            supports_interactive=False,
            max_message_length=100000, # Large limit for email
            metadata={"provider": "smtp"}
        )

    async def validate_recipient(self, recipient: ResolvedRecipient) -> RecipientValidation:
        """Validates email recipient."""
        email = recipient.recipient_id
        if "@" not in email or "." not in email:
            return RecipientValidation(
                valid=False,
                recipient_id=email,
                error_code="invalid_format",
                error_message="Invalid email format",
            )
        return RecipientValidation(valid=True, recipient_id=email)
