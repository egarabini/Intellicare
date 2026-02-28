import logging
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.email.models import EmailSendRequest, EmailSendResponse, EmailStatus
from comunicacao.channels.email.dispatcher import EmailDispatcher
from comunicacao.channels.email.config import EmailConfig
from comunicacao.dispatchers.base import ChannelMessage, ResolvedRecipient, RenderedContent
from comunicacao.storage.repository import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["Email"])

# Dependency for config
def get_email_config() -> EmailConfig:
    return EmailConfig.from_env()

# Dependency for dispatcher
async def get_email_dispatcher(
    db: AsyncSession = Depends(get_db_session),
    config: EmailConfig = Depends(get_email_config),
) -> EmailDispatcher:
    return EmailDispatcher(db=db, config=config)

@router.post("/send", response_model=EmailSendResponse)
async def send_email(
    request: EmailSendRequest,
    dispatcher: EmailDispatcher = Depends(get_email_dispatcher)
):
    """
    Sends an email using the configured SMTP provider.
    Supports templates (jinja2) or raw body.
    """
    try:
        # Create channel message structure
        message = ChannelMessage(
            intent_id="manual-send",
            correlation_id=f"api-{request.recipient}",
            channel="email",
            recipient=ResolvedRecipient(
                recipient_id=request.recipient,
                recipient_type="email"
            ),
            content=RenderedContent(
                format="html" if request.body_html else "text",
                body=request.body_text or request.body_html or "No content",
                subject=request.subject
            ),
            metadata={
                "template_name": request.template_name,
                "context": request.context
            }
        )
        
        result = await dispatcher.send(message)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=f"Failed to send email: {result.error_message}")
            
        return EmailSendResponse(
            message_id=str(result.channel_message_id),
            status="sent", # Simplified status
            recipient=request.recipient,
            provider="smtp"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_email endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(
    dispatcher: EmailDispatcher = Depends(get_email_dispatcher)
):
    """Checks the health of the email subsystem."""
    return await dispatcher.health_check()
