"""
Webhook Handler para WhatsApp (D4).

Processa eventos recebidos via webhook da Meta.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.models import ExternalMessageLog, ExternalMessageStatus
from comunicacao.channels.whatsapp.models import (
    WhatsAppStatusUpdate,
    WhatsAppIncomingMessage,
)

logger = logging.getLogger(__name__)


class WhatsAppWebhookHandler:
    """Handler para webhooks WhatsApp."""

    def __init__(self, db: AsyncSession):
        """
        Inicializa handler.

        Args:
            db: Sessão do banco.
        """
        self._db = db

    async def handle_webhook(self, payload: Dict[str, Any]) -> None:
        """
        Processa evento de webhook.

        Args:
            payload: Payload do webhook.
        """
        logger.info("Processando webhook WhatsApp: %s", payload.get("object"))

        # Validar estrutura
        if payload.get("object") != "whatsapp_business_account":
            logger.warning("Webhook inválido: object=%s", payload.get("object"))
            return

        # Processar cada entry
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})

                # Processar status updates
                if "statuses" in value:
                    for status in value["statuses"]:
                        await self._handle_status_update(status)

                # Processar mensagens recebidas
                if "messages" in value:
                    for message in value["messages"]:
                        await self._handle_incoming_message(message, value.get("metadata", {}))

    async def _handle_status_update(self, status: Dict[str, Any]) -> None:
        """
        Processa atualização de status.

        Args:
            status: Dados do status.
        """
        message_id = status.get("id")
        status_value = status.get("status")  # sent, delivered, read, failed
        timestamp = datetime.fromtimestamp(int(status.get("timestamp", 0)), tz=UTC)

        logger.info("Status update: message_id=%s, status=%s", message_id, status_value)

        # Mapear status WhatsApp -> ExternalMessageStatus
        status_map = {
            "sent": ExternalMessageStatus.SENT,
            "delivered": ExternalMessageStatus.DELIVERED,
            "read": ExternalMessageStatus.READ,
            "failed": ExternalMessageStatus.FAILED,
        }

        new_status = status_map.get(status_value, ExternalMessageStatus.SENT)

        # Atualizar no banco
        stmt = (
            update(ExternalMessageLog)
            .where(ExternalMessageLog.provider_message_id == message_id)
            .values(
                status=new_status,
                delivered_at=timestamp if new_status == ExternalMessageStatus.DELIVERED else None,
                read_at=timestamp if new_status == ExternalMessageStatus.READ else None,
                failed_at=timestamp if new_status == ExternalMessageStatus.FAILED else None,
                error_code=status.get("errors", [{}])[0].get("code") if status_value == "failed" else None,
                error_message=status.get("errors", [{}])[0].get("title") if status_value == "failed" else None,
            )
        )

        await self._db.execute(stmt)
        await self._db.commit()

        logger.info("Status atualizado no banco: message_id=%s", message_id)

    async def _handle_incoming_message(
        self, message: Dict[str, Any], metadata: Dict[str, Any]
    ) -> None:
        """
        Processa mensagem recebida do paciente.

        Args:
            message: Dados da mensagem.
            metadata: Metadata do webhook.
        """
        message_id = message.get("id")
        from_number = message.get("from")
        message_type = message.get("type")
        timestamp = datetime.fromtimestamp(int(message.get("timestamp", 0)), tz=UTC)

        logger.info(
            "Mensagem recebida: from=%s, type=%s, message_id=%s",
            from_number,
            message_type,
            message_id,
        )

        # Extrair conteúdo baseado no tipo
        text = None
        button_payload = None
        interactive_reply = None

        if message_type == "text":
            text = message.get("text", {}).get("body")
        elif message_type == "button":
            button_payload = message.get("button", {}).get("payload")
        elif message_type == "interactive":
            interactive_reply = message.get("interactive")

        # Criar log de mensagem recebida
        log = ExternalMessageLog(
            channel="whatsapp",
            direction="inbound",
            recipient_id=from_number,
            provider_message_id=message_id,
            status=ExternalMessageStatus.DELIVERED,
            message_content={"text": text, "type": message_type},
            delivered_at=timestamp,
        )

        self._db.add(log)
        await self._db.commit()

        logger.info("Mensagem recebida salva: message_id=%s", message_id)

        # TODO: Processar resposta do paciente (ex: "Tomei" para lembrete de medicação)
        # Isso pode disparar eventos no Redis Streams para outros módulos

    def verify_webhook(self, mode: str, token: str, challenge: str, verify_token: str) -> Optional[str]:
        """
        Verifica webhook (GET request da Meta).

        Args:
            mode: Modo (deve ser "subscribe").
            token: Token recebido.
            challenge: Challenge da Meta.
            verify_token: Token configurado.

        Returns:
            Optional[str]: Challenge se válido, None caso contrário.
        """
        if mode == "subscribe" and token == verify_token:
            logger.info("Webhook verificado com sucesso")
            return challenge

        logger.warning("Webhook verification falhou: mode=%s, token_match=%s", mode, token == verify_token)
        return None

