"""Handler para webhooks do Rocket.Chat."""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RCWebhookMessage(BaseModel):
    """Mensagem recebida via webhook do Rocket.Chat."""
    
    message_id: str = Field(..., alias="_id", description="ID da mensagem")
    token: str | None = Field(None, description="Token do webhook")
    channel_id: str = Field(..., description="ID do canal")
    channel_name: str = Field(..., description="Nome do canal")
    user_id: str = Field(..., description="ID do usuário remetente")
    user_name: str = Field(..., description="Username do remetente")
    text: str = Field(..., description="Texto da mensagem")
    timestamp: str = Field(..., alias="ts", description="Timestamp ISO")
    
    # Campos opcionais
    bot: bool = Field(False, description="Mensagem de bot?")
    edited: bool = Field(False, description="Mensagem editada?")
    alias: str | None = Field(None, description="Alias do remetente")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "msg123",
                "token": "webhook_token_here",
                "channel_id": "xyz789",
                "channel_name": "alertas-clinicos",
                "user_id": "user456",
                "user_name": "joao.silva",
                "text": "/paciente patient-123",
                "ts": "2026-02-17T10:30:00Z",
                "bot": False,
            }
        }


class WebhookValidationError(Exception):
    """Erro de validação de webhook."""
    pass


class RocketChatWebhookHandler:
    """
    Handler para webhooks do Rocket.Chat.
    
    Responsável por:
    - Validar token do webhook
    - Filtrar mensagens de bot (evitar loops)
    - Identificar comandos (começam com /)
    - Extrair comando e argumentos
    - Rotear para processador de comandos
    """
    
    def __init__(self, webhook_token: str | None = None):
        """
        Inicializa handler.
        
        Args:
            webhook_token: Token esperado do webhook (para validação)
        """
        self.webhook_token = webhook_token
        
        logger.info("RocketChatWebhookHandler inicializado - token_configured=%s", bool(webhook_token))
    
    def validate_token(self, received_token: str | None) -> bool:
        """
        Valida token do webhook.
        
        Args:
            received_token: Token recebido no webhook
        
        Returns:
            True se válido
        
        Raises:
            WebhookValidationError: Se token inválido
        """
        if not self.webhook_token:
            # Token não configurado, aceitar qualquer requisição (dev mode)
            logger.warning("Webhook token não configurado - aceitando todas as requisições")
            return True
        
        if not received_token:
            raise WebhookValidationError("Token não fornecido no webhook")
        
        # Comparação segura (constant-time)
        if not hmac.compare_digest(received_token, self.webhook_token):
            raise WebhookValidationError("Token inválido")
        
        return True
    
    def is_bot_message(self, message: RCWebhookMessage) -> bool:
        """
        Verifica se mensagem é de bot (para evitar loops).
        
        Args:
            message: Mensagem do webhook
        
        Returns:
            True se é mensagem de bot
        """
        # Verificar flag bot
        if message.bot:
            return True
        
        # Verificar se username é do bot
        if message.user_name in ["intellicare-bot", "intellicare"]:
            return True
        
        # Verificar se tem alias de bot
        if message.alias and "intellicare" in message.alias.lower():
            return True
        
        return False
    
    def is_command(self, text: str) -> bool:
        """
        Verifica se mensagem é um comando (começa com /).
        
        Args:
            text: Texto da mensagem
        
        Returns:
            True se é comando
        """
        return text.strip().startswith("/")
    
    def parse_command(self, text: str) -> tuple[str, list[str]]:
        """
        Extrai comando e argumentos da mensagem.
        
        Args:
            text: Texto da mensagem (ex: "/paciente patient-123")
        
        Returns:
            Tupla (comando, argumentos)
            Ex: ("paciente", ["patient-123"])
        """
        # Remover / inicial e dividir por espaços
        parts = text.strip()[1:].split()
        
        if not parts:
            return ("", [])
        
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        return (command, args)

    async def handle_webhook(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Processa webhook do Rocket.Chat.

        Args:
            payload: Payload do webhook

        Returns:
            Dict com resultado do processamento ou None se ignorado

        Raises:
            WebhookValidationError: Se validação falhar
        """
        logger.info("Processando webhook do Rocket.Chat")

        # Parsear mensagem
        try:
            message = RCWebhookMessage(**payload)
        except Exception as e:
            logger.error("Erro ao parsear webhook payload: %s", str(e))
            raise WebhookValidationError(f"Payload inválido: {str(e)}") from e

        # Validar token
        self.validate_token(message.token)

        # Ignorar mensagens de bot (evitar loops)
        if self.is_bot_message(message):
            logger.debug("Ignorando mensagem de bot: user=%s", message.user_name)
            return None

        # Verificar se é comando
        if not self.is_command(message.text):
            logger.debug("Mensagem não é comando, ignorando: %s", message.text[:50])
            return None

        # Parsear comando
        command, args = self.parse_command(message.text)

        logger.info(
            "Comando detectado: command=%s, args=%s, user=%s, channel=%s",
            command,
            args,
            message.user_name,
            message.channel_name,
        )

        # Retornar dados do comando para processamento
        return {
            "command": command,
            "args": args,
            "message_id": message.message_id,
            "channel_id": message.channel_id,
            "channel_name": message.channel_name,
            "user_id": message.user_id,
            "user_name": message.user_name,
            "timestamp": message.timestamp,
        }

    async def process_command(
        self,
        command_data: dict[str, Any],
        command_processor: Any,
    ) -> str | None:
        """
        Processa comando usando processador fornecido.

        Args:
            command_data: Dados do comando (retornado por handle_webhook)
            command_processor: Processador de comandos (ex: IntelliCareBot)

        Returns:
            Resposta do comando ou None
        """
        command = command_data["command"]
        args = command_data["args"]

        logger.info("Processando comando: %s %s", command, args)

        # Verificar se processador tem método para o comando
        handler_method = getattr(command_processor, f"handle_{command}", None)

        if not handler_method:
            logger.warning("Comando não suportado: %s", command)
            return f"❌ Comando não reconhecido: `/{command}`\n\nUse `/ajuda` para ver comandos disponíveis."

        # Executar handler
        try:
            response = await handler_method(args, command_data)
            return response
        except Exception as e:
            logger.error("Erro ao processar comando %s: %s", command, str(e))
            return f"❌ Erro ao processar comando: {str(e)}"

    def create_response_payload(
        self,
        text: str,
        channel_id: str | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Cria payload de resposta para enviar ao RC.

        Args:
            text: Texto da resposta
            channel_id: ID do canal (opcional)
            thread_id: ID da thread (para responder em thread)

        Returns:
            Dict com payload para RC API
        """
        payload: dict[str, Any] = {
            "text": text,
            "alias": "IntelliCare Bot",
            "emoji": ":robot:",
        }

        if channel_id:
            payload["roomId"] = channel_id

        if thread_id:
            payload["tmid"] = thread_id  # Thread message ID

        return payload

