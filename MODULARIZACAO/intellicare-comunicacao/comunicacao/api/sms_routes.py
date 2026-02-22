"""
API routes para SMS (D4).

Endpoints para enviar mensagens SMS.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.sms.config import SMSConfig
from comunicacao.channels.sms.dispatcher import SMSDispatcher
from comunicacao.channels.sms.models import SMSSendRequest, SMSSendResponse
from comunicacao.dispatchers.base import ChannelMessage, ResolvedRecipient, RenderedContent
from comunicacao.storage.repository import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sms", tags=["sms"])


# Dependency para obter config
def get_sms_config() -> SMSConfig:
    """Obtém configuração de SMS."""
    return SMSConfig.from_env()


# Dependency para obter dispatcher
async def get_sms_dispatcher(
    db: AsyncSession = Depends(get_db_session),
    config: SMSConfig = Depends(get_sms_config),
) -> SMSDispatcher:
    """Obtém dispatcher de SMS."""
    return SMSDispatcher(db=db, config=config)


@router.post("/send", response_model=SMSSendResponse, status_code=status.HTTP_200_OK)
async def send_sms(
    request: SMSSendRequest,
    dispatcher: SMSDispatcher = Depends(get_sms_dispatcher),
    # TODO: Adicionar autenticação Keycloak
    # current_user: User = Depends(get_current_user),
) -> SMSSendResponse:
    """
    Envia mensagem SMS.

    Args:
        request: Dados da mensagem.
        dispatcher: Dispatcher de SMS.

    Returns:
        SMSSendResponse: Resultado do envio.

    Raises:
        HTTPException: Se erro no envio.
    """
    # Criar mensagem
    message = ChannelMessage(
        intent_id="manual-send",
        correlation_id=f"api-{request.to}",
        channel="sms",
        recipient=ResolvedRecipient(
            recipient_id=request.to,
            recipient_type="phone",
        ),
        content=RenderedContent(
            format="text",
            body=request.text,
            subject="",
        ),
        metadata={"provider": request.provider} if request.provider else {},
    )

    # Enviar
    result = await dispatcher.send(message)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message or "Erro ao enviar SMS",
        )

    return SMSSendResponse(
        message_id=result.channel_message_id or "",
        status="sent",
        to=request.to,
        provider=result.metadata.get("provider", "unknown"),
    )


@router.get("/providers")
async def get_providers(
    config: SMSConfig = Depends(get_sms_config),
) -> dict:
    """
    Lista providers SMS disponíveis.

    Args:
        config: Configuração SMS.

    Returns:
        dict: Providers disponíveis.
    """
    providers = []

    if config.twilio and config.twilio.enabled:
        providers.append("twilio")

    if config.zenvia and config.zenvia.enabled:
        providers.append("zenvia")

    if config.sns and config.sns.enabled:
        providers.append("sns")

    return {
        "providers": providers,
        "default_provider": config.default_provider,
        "fallback_providers": config.fallback_providers,
    }

