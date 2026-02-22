"""Rotas da API para integração Rocket.Chat."""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from comunicacao.auth import get_current_user, requires_role
from comunicacao.bot import IntelliCareBot
from comunicacao.rocketchat import (
    RocketChatChannelService,
    RocketChatClient,
    RocketChatConfig,
    RocketChatWebhookHandler,
)
from comunicacao.sync import UserSyncService
from comunicacao.sync.models import KeycloakEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["rocketchat"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SendMessageRequest(BaseModel):
    """Request para enviar mensagem no RC."""
    
    room_id: str = Field(..., description="ID do canal/sala")
    text: str = Field(..., description="Texto da mensagem")
    alias: str | None = Field(None, description="Alias do remetente")
    emoji: str | None = Field(None, description="Emoji do remetente")
    
    class Config:
        json_schema_extra = {
            "example": {
                "room_id": "xyz789",
                "text": "**Alerta**: Novo resultado de laboratório disponível",
                "alias": "IntelliCare",
                "emoji": ":hospital:",
            }
        }


class SendMessageResponse(BaseModel):
    """Response de envio de mensagem."""
    
    success: bool = Field(..., description="Sucesso?")
    message_id: str | None = Field(None, description="ID da mensagem enviada")
    error: str | None = Field(None, description="Mensagem de erro")


class CreateChannelRequest(BaseModel):
    """Request para criar canal no RC."""
    
    channel_type: str = Field(..., description="Tipo do canal (case, team, alert, custom)")
    identifier: str | None = Field(None, description="Identificador (patient_id, team_id)")
    name: str | None = Field(None, description="Nome customizado (se type=custom)")
    members: list[str] = Field(default_factory=list, description="Usernames dos membros")
    read_only: bool = Field(False, description="Canal somente leitura?")
    
    class Config:
        json_schema_extra = {
            "example": {
                "channel_type": "case",
                "identifier": "patient-123",
                "members": ["dr.joao", "enf.ana"],
                "read_only": False,
            }
        }


class CreateChannelResponse(BaseModel):
    """Response de criação de canal."""
    
    success: bool = Field(..., description="Sucesso?")
    channel_id: str | None = Field(None, description="ID do canal criado")
    channel_name: str | None = Field(None, description="Nome do canal")
    error: str | None = Field(None, description="Mensagem de erro")


class InviteUserRequest(BaseModel):
    """Request para convidar usuário para canal."""
    
    user_id: str = Field(..., description="Username do usuário")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "dr.carlos",
            }
        }


class InviteUserResponse(BaseModel):
    """Response de convite de usuário."""
    
    success: bool = Field(..., description="Sucesso?")
    error: str | None = Field(None, description="Mensagem de erro")


class ChannelInfo(BaseModel):
    """Informações de um canal."""
    
    id: str = Field(..., description="ID do canal")
    name: str = Field(..., description="Nome do canal")
    type: str = Field(..., description="Tipo (c=public, p=private, d=direct)")
    members_count: int = Field(0, description="Número de membros")


class ListChannelsResponse(BaseModel):
    """Response de listagem de canais."""
    
    channels: list[ChannelInfo] = Field(default_factory=list, description="Lista de canais")
    total: int = Field(0, description="Total de canais")


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_rc_client() -> RocketChatClient:
    """Dependency para obter cliente RC."""
    config = RocketChatConfig.from_env()
    client = RocketChatClient(config)
    async with client:
        yield client


async def get_channel_service() -> RocketChatChannelService:
    """Dependency para obter channel service."""
    config = RocketChatConfig.from_env()
    client = RocketChatClient(config)
    return RocketChatChannelService(client=client, config=config)


async def get_user_sync_service() -> UserSyncService:
    """Dependency para obter user sync service."""
    return UserSyncService()


async def get_webhook_handler() -> RocketChatWebhookHandler:
    """Dependency para obter webhook handler."""
    import os
    webhook_token = os.getenv("ROCKETCHAT_WEBHOOK_TOKEN")
    return RocketChatWebhookHandler(webhook_token=webhook_token)


async def get_bot() -> IntelliCareBot:
    """Dependency para obter bot."""
    config = RocketChatConfig.from_env()
    return IntelliCareBot(rc_config=config)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/rocketchat/message",
    response_model=SendMessageResponse,
    summary="Enviar mensagem no Rocket.Chat",
)
@requires_role("comunicacao_send")
async def send_message(
    request: SendMessageRequest,
    rc_client: RocketChatClient = Depends(get_rc_client),
    current_user: dict = Depends(get_current_user),
) -> SendMessageResponse:
    """
    Envia mensagem para um canal do Rocket.Chat.
    
    Requer role: `comunicacao_send`
    """
    logger.info(
        "Enviando mensagem RC - room=%s, user=%s",
        request.room_id,
        current_user.get("username", "unknown"),
    )
    
    try:
        result = await rc_client.send_message(
            room_id=request.room_id,
            text=request.text,
            alias=request.alias,
            emoji=request.emoji,
        )
        
        return SendMessageResponse(
            success=True,
            message_id=result.message_id,
        )
    
    except Exception as e:
        logger.error("Erro ao enviar mensagem RC: %s", str(e))
        return SendMessageResponse(
            success=False,
            error=str(e),
        )


@router.post(
    "/rocketchat/channel",
    response_model=CreateChannelResponse,
    summary="Criar canal no Rocket.Chat",
)
@requires_role("comunicacao_admin")
async def create_channel(
    request: CreateChannelRequest,
    channel_service: RocketChatChannelService = Depends(get_channel_service),
    current_user: dict = Depends(get_current_user),
) -> CreateChannelResponse:
    """
    Cria canal no Rocket.Chat.

    Requer role: `comunicacao_admin`
    """
    logger.info(
        "Criando canal RC - type=%s, identifier=%s, user=%s",
        request.channel_type,
        request.identifier,
        current_user.get("username", "unknown"),
    )

    try:
        # Criar canal baseado no tipo
        if request.channel_type == "case":
            if not request.identifier:
                raise ValueError("identifier (patient_id) é obrigatório para type=case")

            channel = await channel_service.create_case_channel(
                patient_id=request.identifier,
                patient_name=request.identifier,
                members=request.members,
                read_only=request.read_only,
            )

        elif request.channel_type == "team":
            if not request.identifier:
                raise ValueError("identifier (team_id) é obrigatório para type=team")

            channel = await channel_service.create_team_channel(
                team_id=request.identifier,
                team_name=request.identifier,
                members=request.members,
                read_only=request.read_only,
            )

        elif request.channel_type == "alert":
            channel = await channel_service.create_alert_channel(
                members=request.members,
                read_only=request.read_only,
            )

        elif request.channel_type == "custom":
            if not request.name:
                raise ValueError("name é obrigatório para type=custom")

            # Criar canal customizado (usar client diretamente)
            config = RocketChatConfig.from_env()
            rc_client = RocketChatClient(config)
            async with rc_client:
                channel = await rc_client.create_private_group(
                    name=request.name,
                    members=request.members,
                    read_only=request.read_only,
                )

        else:
            raise ValueError(f"Tipo de canal inválido: {request.channel_type}")

        return CreateChannelResponse(
            success=True,
            channel_id=channel.id,
            channel_name=channel.name,
        )

    except Exception as e:
        logger.error("Erro ao criar canal RC: %s", str(e))
        return CreateChannelResponse(
            success=False,
            error=str(e),
        )


@router.get(
    "/rocketchat/channels",
    response_model=ListChannelsResponse,
    summary="Listar canais do Rocket.Chat",
)
@requires_role("comunicacao_read")
async def list_channels(
    rc_client: RocketChatClient = Depends(get_rc_client),
    current_user: dict = Depends(get_current_user),
) -> ListChannelsResponse:
    """
    Lista canais do Rocket.Chat.

    Requer role: `comunicacao_read`

    Retorna canais públicos e grupos privados visíveis para o bot.
    """
    logger.info("Listando canais RC - user=%s", current_user.get("username", "unknown"))

    public_channels = await rc_client.list_channels()
    private_groups = await rc_client.list_groups()
    all_channels = public_channels + private_groups
    channels = [
        ChannelInfo(
            id=ch.id,
            name=ch.name,
            type=ch.type,
            members_count=ch.members_count,
        )
        for ch in all_channels
    ]

    return ListChannelsResponse(
        channels=channels,
        total=len(channels),
    )


@router.post(
    "/rocketchat/channel/{channel_id}/invite",
    response_model=InviteUserResponse,
    summary="Convidar usuário para canal",
)
@requires_role("comunicacao_admin")
async def invite_user_to_channel(
    channel_id: str,
    request: InviteUserRequest,
    channel_service: RocketChatChannelService = Depends(get_channel_service),
    current_user: dict = Depends(get_current_user),
) -> InviteUserResponse:
    """
    Convida usuário para canal do Rocket.Chat.

    Requer role: `comunicacao_admin`
    """
    logger.info(
        "Convidando usuário para canal RC - channel=%s, user=%s, by=%s",
        channel_id,
        request.user_id,
        current_user.get("username", "unknown"),
    )

    try:
        # Adicionar membro ao canal (assumir private group por padrão)
        success = await channel_service.add_member(
            channel_id=channel_id,
            user_id=request.user_id,
            channel_type="p",  # private group
        )

        return InviteUserResponse(success=success)

    except Exception as e:
        logger.error("Erro ao convidar usuário: %s", str(e))
        return InviteUserResponse(
            success=False,
            error=str(e),
        )


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@router.post(
    "/sync/keycloak-event",
    summary="Webhook para eventos do Keycloak",
    status_code=status.HTTP_202_ACCEPTED,
)
async def handle_keycloak_event(
    event: KeycloakEvent,
    sync_service: UserSyncService = Depends(get_user_sync_service),
    x_keycloak_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """
    Recebe eventos do Keycloak e sincroniza usuários com Rocket.Chat.

    Eventos suportados:
    - REGISTER: Novo usuário criado
    - UPDATE: Usuário atualizado
    - DELETE: Usuário deletado

    Nota: endpoint público com proteção opcional por token em header `X-Keycloak-Token`.
    """
    logger.info(
        "Evento Keycloak recebido - type=%s, user_id=%s",
        event.type,
        event.user_id,
    )

    try:
        expected_token = os.getenv("KEYCLOAK_WEBHOOK_TOKEN", "").strip()
        if expected_token and x_keycloak_token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de webhook inválido",
            )

        # Processar evento
        sync_record = await sync_service.handle_keycloak_event(event)

        if sync_record:
            return {
                "status": "processed",
                "event_type": event.type,
                "user_id": event.user_id,
                "sync_status": sync_record.sync_status,
            }
        else:
            return {
                "status": "ignored",
                "event_type": event.type,
                "user_id": event.user_id,
            }

    except Exception as e:
        logger.error("Erro ao processar evento Keycloak: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar evento: {str(e)}",
        )


@router.post(
    "/webhooks/rocketchat",
    summary="Webhook para mensagens do Rocket.Chat",
    status_code=status.HTTP_200_OK,
)
async def handle_rocketchat_webhook(
    payload: dict[str, Any],
    webhook_handler: RocketChatWebhookHandler = Depends(get_webhook_handler),
    bot: IntelliCareBot = Depends(get_bot),
) -> dict[str, Any]:
    """
    Recebe webhooks do Rocket.Chat e processa comandos do bot.

    Fluxo:
    1. Validar token do webhook
    2. Filtrar mensagens de bot (evitar loops)
    3. Detectar comandos (começam com /)
    4. Processar comando com IntelliCareBot
    5. Enviar resposta ao canal

    Nota: Este endpoint não requer autenticação (webhook público com token).
    """
    logger.info("Webhook RC recebido")

    try:
        # 1. Processar webhook
        command_data = await webhook_handler.handle_webhook(payload)

        if not command_data:
            # Mensagem ignorada (não é comando ou é de bot)
            return {"status": "ignored"}

        # 2. Processar comando com bot
        response_text = await webhook_handler.process_command(
            command_data,
            command_processor=bot,
        )

        if not response_text:
            return {"status": "no_response"}

        # 3. Criar payload de resposta
        response_payload = webhook_handler.create_response_payload(
            text=response_text,
            channel_id=command_data["channel_id"],
            thread_id=command_data["message_id"],  # Responder em thread
        )

        # 4. Enviar resposta via RC API
        rc_config = RocketChatConfig.from_env()
        rc_client = RocketChatClient(rc_config)
        async with rc_client:
            await rc_client.send_message(
                room_id=response_payload.get("roomId", command_data["channel_id"]),
                text=response_payload["text"],
                alias=response_payload.get("alias"),
                emoji=response_payload.get("emoji"),
            )

        return {
            "status": "ok",
            "command": command_data["command"],
            "user": command_data["user_name"],
        }

    except Exception as e:
        logger.error("Erro ao processar webhook RC: %s", str(e))

        # Retornar erro mas não falhar (webhook deve sempre retornar 200)
        return {
            "status": "error",
            "error": str(e),
        }
