"""Handler para webhooks recebidos do WAHA (WhatsApp HTTP API).

WAHA envia eventos via HTTP POST quando mensagens chegam ou o status
da sessão muda. Este handler processa esses eventos e:

  1. Persiste a mensagem recebida em ExternalMessageLog (direction=inbound)
  2. Publica evento Redis Stream ``whatsapp.message.received``
     para que a agente GERALDA possa processar a resposta do paciente.

Formato do evento WAHA (versão simplificada):

    {
      "event": "message",
      "session": "default",
      "payload": {
        "id": "true_5511999999999@c.us_XXXXX",
        "from": "5511999999999@c.us",
        "to": "55119@c.us",
        "body": "Tomei o remédio",
        "timestamp": 1700000000,
        "type": "chat"
      }
    }

Referência: https://waha.devlike.pro/docs/how-to/webhooks/
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, UTC
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from comunicacao.channels.models import (
    ExternalMessageLog,
    ExternalMessageDirection,
    ExternalMessageStatus,
)

logger = logging.getLogger(__name__)

# Nome do Redis Stream publicado para Geralda
_REDIS_STREAM = "intellicare:whatsapp.message.received"


def _extract_phone(chat_id: str) -> str:
    """Converte '5511999999999@c.us' → '+5511999999999'."""
    number = chat_id.split("@")[0]
    return f"+{number}" if not number.startswith("+") else number


class WAHAWebhookHandler:
    """Processa eventos de webhook enviados pelo WAHA.

    Args:
        db: Sessão assíncrona do banco de dados.
        redis_url: URL do Redis para publicação de eventos.
                   Se None, a publicação Redis é silenciosamente ignorada.
    """

    def __init__(self, db: AsyncSession, *, redis_url: Optional[str] = None) -> None:
        self._db = db
        self._redis_url = redis_url
        self._redis: Any = None

    # ── Redis ──────────────────────────────────────────────────────────────────

    async def _get_redis(self) -> Any:
        if self._redis_url is None:
            return None
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(self._redis_url)
            except ImportError:
                logger.warning("redis não instalado — eventos WAHA não serão publicados no Redis")
                return None
        return self._redis

    async def _publish_redis(self, event_data: dict[str, Any]) -> None:
        redis = await self._get_redis()
        if redis is None:
            return
        try:
            payload = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                       for k, v in event_data.items()}
            await redis.xadd(_REDIS_STREAM, payload, maxlen=1000)
            logger.info("WAHA: evento publicado no Redis Stream %s", _REDIS_STREAM)
        except Exception as exc:
            logger.warning("WAHA: falha ao publicar no Redis: %s", exc)

    # ── Event dispatch ─────────────────────────────────────────────────────────

    async def handle_event(self, payload: dict[str, Any]) -> None:
        """Ponto de entrada principal — roteamento por tipo de evento.

        WAHA emite vários tipos de evento. Processamos:
          • ``message``              — nova mensagem do paciente
          • ``message.reaction``     — reação emoji (ignorada, apenas logada)
          • ``session.status``       — mudança de status da sessão (logada)
          • outros                   — ignorados silenciosamente
        """
        event_type = payload.get("event", "")
        session = payload.get("session", "default")

        logger.debug("WAHA webhook recebido: event=%s session=%s", event_type, session)

        if event_type == "message":
            await self._handle_incoming_message(payload)
        elif event_type == "session.status":
            self._handle_session_status(payload)
        else:
            logger.debug("WAHA: evento ignorado: %s", event_type)

    # ── Incoming message ───────────────────────────────────────────────────────

    async def _handle_incoming_message(self, payload: dict[str, Any]) -> None:
        """Processa mensagem recebida do paciente via WAHA."""
        msg = payload.get("payload", {})
        message_id = msg.get("id", "")
        from_chat_id = msg.get("from", "")
        body = msg.get("body", "")
        msg_type = msg.get("type", "chat")
        timestamp_raw = msg.get("timestamp")
        session = payload.get("session", "default")

        if not from_chat_id:
            logger.warning("WAHA: mensagem recebida sem remetente — ignorando")
            return

        # Ignorar mensagens enviadas por nós (fromMe=True)
        if msg.get("fromMe", False):
            logger.debug("WAHA: mensagem própria ignorada: %s", message_id)
            return

        from_phone = _extract_phone(from_chat_id)
        received_at = (
            datetime.fromtimestamp(int(timestamp_raw), tz=UTC)
            if timestamp_raw else datetime.now(UTC)
        )

        logger.info(
            "WAHA: mensagem recebida — from=%s type=%s id=%s",
            from_phone, msg_type, message_id,
        )

        # ── 1. Persistir no ExternalMessageLog ────────────────────────────────
        # message_summary: texto truncado (LGPD — sem conteúdo completo no log)
        # provider_status: identifica backend + session + tipo para auditoria
        log = ExternalMessageLog(
            channel="whatsapp",
            direction=ExternalMessageDirection.INBOUND,
            recipient_id=from_phone,
            provider_message_id=message_id,
            provider_status=f"waha:{session}:{msg_type}",
            message_summary=(body[:120] + "…") if body and len(body) > 120 else (body or ""),
            status=ExternalMessageStatus.DELIVERED,
            delivered_at=received_at,
        )
        self._db.add(log)
        await self._db.commit()

        # ── 2. Publicar no Redis Stream para Geralda ───────────────────────────
        event_data = {
            "source": "waha",
            "session": session,
            "message_id": message_id,
            "from_phone": from_phone,
            "from_chat_id": from_chat_id,
            "body": body,
            "type": msg_type,
            "received_at": received_at.isoformat(),
        }
        await self._publish_redis(event_data)

    # ── Session status ─────────────────────────────────────────────────────────

    def _handle_session_status(self, payload: dict[str, Any]) -> None:
        """Loga mudanças de status da sessão WAHA (informativo)."""
        status = payload.get("payload", {}).get("status", "unknown")
        session = payload.get("session", "default")
        logger.info("WAHA: session '%s' mudou status → %s", session, status)
