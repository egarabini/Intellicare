"""
API routes para WhatsApp (D4).

Endpoints para enviar mensagens WhatsApp e listar templates.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.whatsapp.config import WhatsAppConfig
from comunicacao.channels.whatsapp.dispatcher import WhatsAppDispatcher
from comunicacao.channels.whatsapp.models import WhatsAppSendRequest, WhatsAppSendResponse
from comunicacao.channels.whatsapp.templates import list_templates, get_template
from comunicacao.dispatchers.base import ChannelMessage, ResolvedRecipient, RenderedContent
from comunicacao.storage.repository import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])


# Dependency para obter config
def get_whatsapp_config() -> WhatsAppConfig:
    """Obtém configuração de WhatsApp."""
    return WhatsAppConfig.from_env()


# Dependency para obter dispatcher
async def get_whatsapp_dispatcher(
    db: AsyncSession = Depends(get_db_session),
    config: WhatsAppConfig = Depends(get_whatsapp_config),
) -> WhatsAppDispatcher:
    """Obtém dispatcher de WhatsApp."""
    return WhatsAppDispatcher(db=db, config=config)


@router.post("/send", response_model=WhatsAppSendResponse, status_code=status.HTTP_200_OK)
async def send_whatsapp(
    request: WhatsAppSendRequest,
    dispatcher: WhatsAppDispatcher = Depends(get_whatsapp_dispatcher),
    # TODO: Adicionar autenticação Keycloak
    # current_user: User = Depends(get_current_user),
) -> WhatsAppSendResponse:
    """
    Envia mensagem WhatsApp usando template.

    Args:
        request: Dados da mensagem.
        dispatcher: Dispatcher de WhatsApp.

    Returns:
        WhatsAppSendResponse: Resultado do envio.

    Raises:
        HTTPException: Se erro no envio.
    """
    # Criar mensagem
    message = ChannelMessage(
        intent_id="manual-send",
        correlation_id=f"api-{request.to}",
        channel="whatsapp",
        recipient=ResolvedRecipient(
            recipient_id=request.to,
            recipient_type="phone",
        ),
        content=RenderedContent(
            format="template",
            body="",
            subject="",
        ),
        metadata={
            "template_name": request.template_name,
            "template_params": request.template_params,
        },
    )

    # Enviar
    result = await dispatcher.send(message)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error_message or "Erro ao enviar WhatsApp",
        )

    return WhatsAppSendResponse(
        message_id=result.channel_message_id or "",
        status="sent",
        to=request.to,
    )


@router.get("/templates", response_model=List[str])
async def get_templates() -> List[str]:
    """
    Lista templates WhatsApp disponíveis.

    Returns:
        List[str]: Nomes dos templates.
    """
    return list_templates()


@router.get("/templates/{template_name}")
async def get_template_info(template_name: str) -> dict:
    """
    Obtém informações de um template.

    Args:
        template_name: Nome do template.

    Returns:
        dict: Informações do template.

    Raises:
        HTTPException: Se template não existir.
    """
    try:
        template = get_template(template_name)
        return template
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_name}' não encontrado",
        )

