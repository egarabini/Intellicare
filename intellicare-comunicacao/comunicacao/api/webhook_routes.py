"""
Webhook routes para canais externos (D4).

Endpoints para receber webhooks de WhatsApp, SMS, etc.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.whatsapp.config import WhatsAppConfig
from comunicacao.channels.whatsapp.webhook_handler import WhatsAppWebhookHandler
from comunicacao.storage.repository import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


# Dependency para obter config
def get_whatsapp_config() -> WhatsAppConfig:
    """Obtém configuração de WhatsApp."""
    return WhatsAppConfig.from_env()


# Dependency para obter webhook handler
async def get_whatsapp_webhook_handler(
    db: AsyncSession = Depends(get_db_session),
) -> WhatsAppWebhookHandler:
    """Obtém webhook handler de WhatsApp."""
    return WhatsAppWebhookHandler(db=db)


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge"),
    config: WhatsAppConfig = Depends(get_whatsapp_config),
    handler: WhatsAppWebhookHandler = Depends(get_whatsapp_webhook_handler),
) -> str:
    """
    Verifica webhook WhatsApp (GET request da Meta).

    A Meta envia um GET request para verificar o webhook quando configurado.

    Args:
        mode: Modo (deve ser "subscribe").
        token: Token de verificação.
        challenge: Challenge da Meta.
        config: Configuração WhatsApp.
        handler: Webhook handler.

    Returns:
        str: Challenge se válido.

    Raises:
        HTTPException: Se verificação falhar.
    """
    logger.info("Verificação de webhook WhatsApp: mode=%s", mode)

    result = handler.verify_webhook(
        mode=mode,
        token=token,
        challenge=challenge,
        verify_token=config.webhook_verify_token,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook verification failed",
        )

    return result


@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def receive_whatsapp_webhook(
    request: Request,
    handler: WhatsAppWebhookHandler = Depends(get_whatsapp_webhook_handler),
) -> Dict[str, str]:
    """
    Recebe eventos de webhook WhatsApp (POST request da Meta).

    A Meta envia eventos de status de mensagens e mensagens recebidas.

    Args:
        request: Request do FastAPI.
        handler: Webhook handler.

    Returns:
        Dict: Confirmação de recebimento.
    """
    # Obter payload
    payload = await request.json()

    logger.info("Webhook WhatsApp recebido: %s", payload.get("object"))

    # Processar webhook
    try:
        await handler.handle_webhook(payload)
    except Exception as exc:
        logger.error("Erro ao processar webhook WhatsApp: %s", exc, exc_info=True)
        # Retornar 200 mesmo com erro para não reenviar webhook
        # (Meta reenvia se não receber 200)

    return {"status": "ok"}

