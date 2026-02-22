"""Cliente HTTP para API REST do Rocket.Chat v7.13.2."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from comunicacao.rocketchat.config import RocketChatConfig
from comunicacao.rocketchat.models import (
    RCAttachment,
    RCChannel,
    RCMessage,
    RCMessageResponse,
    RCUser,
)

logger = logging.getLogger(__name__)


class RocketChatAPIError(Exception):
    """Erro na API do Rocket.Chat."""
    
    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RocketChatClient:
    """Cliente para API REST do Rocket.Chat v7.13.2."""
    
    def __init__(self, config: RocketChatConfig | None = None):
        self.config = config or RocketChatConfig.from_env()
        self._client: httpx.AsyncClient | None = None
        self._user_id: str | None = None
        self._auth_token: str | None = None
        self._authenticated = False
        self._rate_limiter = asyncio.Semaphore(self.config.max_requests_per_second)
        
        logger.info("RocketChatClient inicializado - url=%s", self.config.url)
    
    async def __aenter__(self) -> RocketChatClient:
        """Context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    async def _ensure_client(self) -> None:
        """Garante que o cliente HTTP está inicializado."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.config.url,
                timeout=httpx.Timeout(
                    connect=self.config.connect_timeout,
                    read=self.config.request_timeout,
                    write=self.config.request_timeout,
                    pool=self.config.request_timeout,
                ),
                headers={
                    "Content-Type": "application/json",
                },
            )
            logger.debug("Cliente HTTP criado")
    
    async def close(self) -> None:
        """Fecha o cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.debug("Cliente HTTP fechado")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
        params: dict | None = None,
        require_auth: bool = True,
    ) -> dict:
        """Faz requisição HTTP com rate limiting e retry."""
        await self._ensure_client()
        
        if require_auth and not self._authenticated:
            await self.login()
        
        # Rate limiting
        async with self._rate_limiter:
            headers = {}
            if self._authenticated and require_auth:
                headers["X-User-Id"] = self._user_id
                headers["X-Auth-Token"] = self._auth_token
            
            try:
                response = await self._client.request(
                    method=method,
                    url=endpoint,
                    json=data,
                    params=params,
                    headers=headers,
                )
                
                response.raise_for_status()
                result = response.json()
                
                if not result.get("success", True):
                    error_msg = result.get("error", "Unknown error")
                    raise RocketChatAPIError(
                        f"API returned error: {error_msg}",
                        status_code=response.status_code,
                        response=result,
                    )
                
                return result
                
            except httpx.HTTPStatusError as e:
                logger.error("HTTP error: %s - %s", e.response.status_code, e.response.text)
                raise RocketChatAPIError(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    status_code=e.response.status_code,
                ) from e
            except httpx.RequestError as e:
                logger.error("Request error: %s", str(e))
                raise RocketChatAPIError(f"Request failed: {str(e)}") from e
    
    @retry(
        retry=retry_if_exception_type(RocketChatAPIError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def login(self) -> None:
        """Autentica o bot no Rocket.Chat."""
        logger.info("Autenticando bot: %s", self.config.bot_username)
        
        result = await self._request(
            "POST",
            "/api/v1/login",
            data={
                "user": self.config.bot_username,
                "password": self.config.bot_password,
            },
            require_auth=False,
        )
        
        self._user_id = result["data"]["userId"]
        self._auth_token = result["data"]["authToken"]
        self._authenticated = True

        logger.info("Bot autenticado com sucesso - user_id=%s", self._user_id)

    async def send_message(
        self,
        room_id: str,
        text: str,
        alias: str | None = None,
        emoji: str | None = None,
        avatar: str | None = None,
        attachments: list[RCAttachment] | None = None,
    ) -> RCMessageResponse:
        """
        Envia mensagem para um canal/room.

        Args:
            room_id: ID do canal, #channel, ou @username
            text: Texto da mensagem (Markdown)
            alias: Nome do remetente (override)
            emoji: Emoji avatar (ex: :robot:)
            avatar: URL do avatar
            attachments: Lista de attachments

        Returns:
            RCMessageResponse com message_id, channel_id, timestamp
        """
        logger.info("Enviando mensagem para room=%s", room_id)

        payload: dict[str, Any] = {
            "roomId": room_id,
            "text": text,
        }

        if alias:
            payload["alias"] = alias
        if emoji:
            payload["emoji"] = emoji
        if avatar:
            payload["avatar"] = avatar
        if attachments:
            payload["attachments"] = [att.model_dump(exclude_none=True) for att in attachments]

        result = await self._request("POST", "/api/v1/chat.postMessage", data=payload)

        msg_data = result.get("message", {})
        return RCMessageResponse(
            message_id=msg_data.get("_id", ""),
            channel_id=msg_data.get("rid", room_id),
            timestamp=msg_data.get("ts", datetime.now().isoformat()),
            success=True,
        )

    async def create_channel(
        self,
        name: str,
        members: list[str] | None = None,
        read_only: bool = False,
    ) -> RCChannel:
        """
        Cria canal público.

        Args:
            name: Nome do canal (sem #)
            members: Lista de usernames para adicionar
            read_only: Canal somente leitura?

        Returns:
            RCChannel criado
        """
        logger.info("Criando canal público: %s", name)

        payload: dict[str, Any] = {
            "name": name,
            "readOnly": read_only,
        }

        if members:
            payload["members"] = members

        result = await self._request("POST", "/api/v1/channels.create", data=payload)

        channel_data = result.get("channel", {})
        return RCChannel(
            id=channel_data.get("_id", ""),
            name=channel_data.get("name", name),
            type="c",
            topic=channel_data.get("topic"),
            description=channel_data.get("description"),
            members_count=channel_data.get("usersCount", 0),
            read_only=channel_data.get("ro", False),
            archived=channel_data.get("archived", False),
        )

    async def create_private_group(
        self,
        name: str,
        members: list[str] | None = None,
        read_only: bool = False,
    ) -> RCChannel:
        """
        Cria grupo privado.

        Args:
            name: Nome do grupo
            members: Lista de usernames para adicionar
            read_only: Grupo somente leitura?

        Returns:
            RCChannel criado
        """
        logger.info("Criando grupo privado: %s", name)

        payload: dict[str, Any] = {
            "name": name,
            "readOnly": read_only,
        }

        if members:
            payload["members"] = members

        result = await self._request("POST", "/api/v1/groups.create", data=payload)

        group_data = result.get("group", {})
        return RCChannel(
            id=group_data.get("_id", ""),
            name=group_data.get("name", name),
            type="p",
            topic=group_data.get("topic"),
            description=group_data.get("description"),
            members_count=group_data.get("usersCount", 0),
            read_only=group_data.get("ro", False),
            archived=group_data.get("archived", False),
        )

    async def invite_user_to_channel(self, room_id: str, user_id: str) -> bool:
        """
        Adiciona usuário a um canal público.

        Args:
            room_id: ID do canal
            user_id: ID do usuário

        Returns:
            True se sucesso
        """
        logger.info("Adicionando user=%s ao canal=%s", user_id, room_id)

        await self._request(
            "POST",
            "/api/v1/channels.invite",
            data={"roomId": room_id, "userId": user_id},
        )

        return True

    async def invite_user_to_group(self, room_id: str, user_id: str) -> bool:
        """
        Adiciona usuário a um grupo privado.

        Args:
            room_id: ID do grupo
            user_id: ID do usuário

        Returns:
            True se sucesso
        """
        logger.info("Adicionando user=%s ao grupo=%s", user_id, room_id)

        await self._request(
            "POST",
            "/api/v1/groups.invite",
            data={"roomId": room_id, "userId": user_id},
        )

        return True

    async def get_channel_info(self, room_id: str) -> RCChannel | None:
        """
        Obtém informações de um canal público.

        Args:
            room_id: ID do canal

        Returns:
            RCChannel ou None se não encontrado
        """
        try:
            result = await self._request(
                "GET",
                "/api/v1/channels.info",
                params={"roomId": room_id},
            )

            channel_data = result.get("channel", {})
            return RCChannel(
                id=channel_data.get("_id", ""),
                name=channel_data.get("name", ""),
                type="c",
                topic=channel_data.get("topic"),
                description=channel_data.get("description"),
                members_count=channel_data.get("usersCount", 0),
                read_only=channel_data.get("ro", False),
                archived=channel_data.get("archived", False),
            )
        except RocketChatAPIError:
            logger.warning("Canal não encontrado: %s", room_id)
            return None

    async def get_group_info(self, room_id: str) -> RCChannel | None:
        """
        Obtém informações de um grupo privado.

        Args:
            room_id: ID do grupo

        Returns:
            RCChannel ou None se não encontrado
        """
        try:
            result = await self._request(
                "GET",
                "/api/v1/groups.info",
                params={"roomId": room_id},
            )

            group_data = result.get("group", {})
            return RCChannel(
                id=group_data.get("_id", ""),
                name=group_data.get("name", ""),
                type="p",
                topic=group_data.get("topic"),
                description=group_data.get("description"),
                members_count=group_data.get("usersCount", 0),
                read_only=group_data.get("ro", False),
                archived=group_data.get("archived", False),
            )
        except RocketChatAPIError:
            logger.warning("Grupo não encontrado: %s", room_id)
            return None

    async def delete_message(self, message_id: str, room_id: str) -> bool:
        """
        Deleta uma mensagem.

        Args:
            message_id: ID da mensagem
            room_id: ID do canal/room

        Returns:
            True se sucesso
        """
        logger.info("Deletando mensagem: %s", message_id)

        try:
            await self._request(
                "POST",
                "/api/v1/chat.delete",
                data={"msgId": message_id, "roomId": room_id},
            )
            return True
        except RocketChatAPIError as e:
            logger.error("Erro ao deletar mensagem: %s", str(e))
            return False

    async def get_user_by_username(self, username: str) -> RCUser | None:
        """
        Busca usuário por username.

        Args:
            username: Username do usuário

        Returns:
            RCUser ou None se não encontrado
        """
        try:
            result = await self._request(
                "GET",
                "/api/v1/users.info",
                params={"username": username},
            )

            user_data = result.get("user", {})
            return RCUser(
                id=user_data.get("_id", ""),
                username=user_data.get("username", username),
                name=user_data.get("name"),
                email=user_data.get("emails", [{}])[0].get("address") if user_data.get("emails") else None,
                status=user_data.get("status", "offline"),
                active=user_data.get("active", True),
                roles=user_data.get("roles", []),
            )
        except RocketChatAPIError:
            logger.warning("Usuário não encontrado: %s", username)
            return None

    async def set_user_active_status(self, user_id: str, active: bool) -> bool:
        """
        Ativa/desativa usuário no Rocket.Chat.

        Args:
            user_id: ID do usuário no RC
            active: True para ativar, False para desativar

        Returns:
            True se operação foi aceita
        """
        try:
            await self._request(
                "POST",
                "/api/v1/users.setActiveStatus",
                data={"userId": user_id, "activeStatus": active},
            )
            return True
        except RocketChatAPIError as exc:
            logger.error("Falha ao atualizar status ativo do usuário %s: %s", user_id, exc)
            return False

    async def list_channels(self, count: int = 100, offset: int = 0) -> list[RCChannel]:
        """Lista canais públicos."""
        try:
            result = await self._request(
                "GET",
                "/api/v1/channels.list",
                params={"count": count, "offset": offset},
            )
            channels = result.get("channels", [])
            return [
                RCChannel(
                    id=item.get("_id", ""),
                    name=item.get("name", ""),
                    type="c",
                    topic=item.get("topic"),
                    description=item.get("description"),
                    members_count=item.get("usersCount", 0),
                    read_only=item.get("ro", False),
                    archived=item.get("archived", False),
                )
                for item in channels
            ]
        except RocketChatAPIError as exc:
            logger.warning("Falha ao listar canais públicos: %s", exc)
            return []

    async def list_groups(self, count: int = 100, offset: int = 0) -> list[RCChannel]:
        """Lista grupos privados."""
        try:
            result = await self._request(
                "GET",
                "/api/v1/groups.list",
                params={"count": count, "offset": offset},
            )
            groups = result.get("groups", [])
            return [
                RCChannel(
                    id=item.get("_id", ""),
                    name=item.get("name", ""),
                    type="p",
                    topic=item.get("topic"),
                    description=item.get("description"),
                    members_count=item.get("usersCount", 0),
                    read_only=item.get("ro", False),
                    archived=item.get("archived", False),
                )
                for item in groups
            ]
        except RocketChatAPIError as exc:
            logger.warning("Falha ao listar grupos privados: %s", exc)
            return []

    async def health_check_details(self) -> dict[str, Any]:
        """Retorna detalhes completos de saúde do servidor Rocket.Chat."""
        import time

        start = time.time()

        try:
            result = await self._request(
                "GET",
                "/api/info",
                require_auth=False,
            )

            latency_ms = int((time.time() - start) * 1000)

            return {
                "healthy": True,
                "version": result.get("version", "unknown"),
                "latency_ms": latency_ms,
                "details": {
                    "server": self.config.url,
                    "authenticated": self._authenticated,
                },
            }
        except Exception as e:
            logger.error("Health check falhou: %s", str(e))
            return {
                "healthy": False,
                "version": "unknown",
                "latency_ms": -1,
                "error": str(e),
            }

    async def health_check(self) -> bool:
        """Compat legado: retorna apenas estado saudável (bool)."""
        details = await self.health_check_details()
        return bool(details.get("healthy"))
