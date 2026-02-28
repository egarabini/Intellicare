"""
API routes para Push Notifications (D4).

Endpoints para gerenciar subscriptions e enviar push notifications.
"""

import logging
from datetime import datetime, UTC
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.models import PushSubscription
from comunicacao.channels.push.config import PushConfig
from comunicacao.channels.push.dispatcher import PushDispatcher
from comunicacao.channels.push.models import (
    PushSubscriptionRequest,
    PushSubscriptionResponse,
    PushTestRequest,
    PushTestResponse,
    VAPIDPublicKeyResponse,
)
from comunicacao.storage.repository import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/push", tags=["push"])


# Dependency para obter config
def get_push_config() -> PushConfig:
    """Obtém configuração de push."""
    return PushConfig.from_env()


# Dependency para obter dispatcher
async def get_push_dispatcher(
    db: AsyncSession = Depends(get_db_session),
    config: PushConfig = Depends(get_push_config),
) -> PushDispatcher:
    """Obtém dispatcher de push."""
    return PushDispatcher(db=db, config=config)


@router.post("/subscribe", response_model=PushSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe_push(
    request: PushSubscriptionRequest,
    db: AsyncSession = Depends(get_db_session),
    # TODO: Adicionar autenticação Keycloak
    # current_user: User = Depends(get_current_user),
) -> PushSubscriptionResponse:
    """
    Registra subscription de push notification.

    Args:
        request: Dados da subscription.
        db: Sessão do banco.

    Returns:
        PushSubscriptionResponse: Subscription criada.
    """
    # TODO: Usar current_user.id quando autenticação estiver implementada
    user_id = "test-user"  # Placeholder

    # Criar subscription
    subscription = PushSubscription(
        user_id=user_id,
        subscription_type=request.subscription_type,
        endpoint=request.endpoint,
        p256dh_key=request.p256dh_key,
        auth_key=request.auth_key,
        fcm_token=request.fcm_token,
        device_name=request.device_name,
    )

    # Salvar no banco
    # TODO: Implementar persistência quando ORM estiver configurado
    logger.info("Subscription criada: user_id=%s, type=%s", user_id, request.subscription_type)

    return PushSubscriptionResponse(
        subscription_id=str(subscription.id),
        user_id=subscription.user_id,
        subscription_type=subscription.subscription_type,
        device_name=subscription.device_name,
        created_at=subscription.created_at.isoformat(),
    )


@router.delete("/subscribe/{subscription_id}", status_code=status.HTTP_200_OK)
async def unsubscribe_push(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    # TODO: Adicionar autenticação Keycloak
) -> dict:
    """
    Remove subscription de push.

    Args:
        subscription_id: ID da subscription.
        db: Sessão do banco.

    Returns:
        dict: Confirmação de remoção.
    """
    # TODO: Implementar remoção quando ORM estiver configurado
    logger.info("Subscription removida: %s", subscription_id)

    return {"deleted": True, "subscription_id": str(subscription_id)}


@router.get("/subscriptions", response_model=List[PushSubscriptionResponse])
async def list_subscriptions(
    db: AsyncSession = Depends(get_db_session),
    # TODO: Adicionar autenticação Keycloak
    # current_user: User = Depends(get_current_user),
) -> List[PushSubscriptionResponse]:
    """
    Lista subscriptions do usuário.

    Args:
        db: Sessão do banco.

    Returns:
        List[PushSubscriptionResponse]: Lista de subscriptions.
    """
    # TODO: Usar current_user.id quando autenticação estiver implementada
    user_id = "test-user"  # Placeholder

    # TODO: Implementar consulta quando ORM estiver configurado
    logger.info("Listando subscriptions: user_id=%s", user_id)

    return []


@router.get("/vapid-key", response_model=VAPIDPublicKeyResponse)
async def get_vapid_public_key(
    config: PushConfig = Depends(get_push_config),
) -> VAPIDPublicKeyResponse:
    """
    Retorna VAPID public key para o frontend.

    Este endpoint é público (sem autenticação) pois o frontend
    precisa da chave pública para criar subscriptions.

    Args:
        config: Configuração de push.

    Returns:
        VAPIDPublicKeyResponse: Chave pública VAPID.
    """
    return VAPIDPublicKeyResponse(public_key=config.vapid.public_key)


@router.post("/test", response_model=PushTestResponse)
async def test_push(
    request: PushTestRequest,
    dispatcher: PushDispatcher = Depends(get_push_dispatcher),
    # TODO: Adicionar autenticação Keycloak
    # current_user: User = Depends(get_current_user),
) -> PushTestResponse:
    """
    Envia push de teste para o usuário.

    Args:
        request: Dados do teste.
        dispatcher: Dispatcher de push.

    Returns:
        PushTestResponse: Resultado do teste.
    """
    # TODO: Usar current_user.id quando autenticação estiver implementada
    user_id = "test-user"  # Placeholder

    # TODO: Implementar envio de teste real
    logger.info("Enviando push de teste: user_id=%s", user_id)

    return PushTestResponse(
        sent_to=0,
        failed=0,
        details=[{"message": "Teste não implementado ainda"}],
    )

