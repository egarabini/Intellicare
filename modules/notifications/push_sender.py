"""Integração com pywebpush para Web Push API."""
import json
import logging
from typing import Any

from pywebpush import webpush, WebPushException

from intellicare_core.config import settings

logger = logging.getLogger(__name__)

async def send_push(subscription_info: dict[str, Any], title: str, body: str, action_url: str) -> bool:
    """Remete uma notificação Web Push usando VAPID."""
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        logger.warning("VAPID Keys ausentes. Web Push skipado.")
        return False
        
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({"title": title, "body": body, "action_url": action_url}),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": getattr(settings, "VAPID_SUBJECT", "mailto:admin@intellicare.ia.br")}
        )
        return True
    except WebPushException as ex:
        if ex.response and ex.response.status_code == 410:
            logger.info(f"Subscription WebPush expirada nativamente: {subscription_info.get('endpoint')}")
            raise ex
        logger.error(f"Erro ao disparar WebPush: {ex}")
        return False
    except Exception as ex:
        logger.error(f"Falha generica de WebPush: {ex}")
        return False
