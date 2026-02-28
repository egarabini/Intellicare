

import os
from comunicacao.dispatchers.rocketchat_dispatcher import RocketChatDispatcher
from comunicacao.notifications.email_dispatcher import EmailDispatcher
from comunicacao.notifications.sms_dispatcher import SMSDispatcher
from comunicacao.notifications.whatsapp_dispatcher import WhatsAppDispatcher

class DispatcherManager:
    """
    Gerencia dispatchers concretos para cada canal (Rocket.Chat, Email, etc).
    """
    def __init__(self):
        # Configuração Rocket.Chat via env
        rc_url = os.getenv("ROCKETCHAT_URL", "http://localhost:3000")
        rc_token = os.getenv("ROCKETCHAT_ADMIN_AUTH_TOKEN", "dev-token")

        self.rocketchat_dispatcher = RocketChatDispatcher(rc_url, rc_token)
        # Configuração Email
        smtp_host = os.getenv("SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("SMTP_PORT", "465"))
        smtp_user = os.getenv("SMTP_USER", "test@example.com")
        smtp_pass = os.getenv("SMTP_PASS", "password")
        self.email_dispatcher = EmailDispatcher(smtp_host, smtp_port, smtp_user, smtp_pass)
        # Configuração SMS
        sms_url = os.getenv("SMS_API_URL", "https://sms.dev/api")
        sms_key = os.getenv("SMS_API_KEY", "dev-key")
        self.sms_dispatcher = SMSDispatcher(sms_url, sms_key)
        # Configuração WhatsApp
        wa_url = os.getenv("WA_API_URL", "https://wa.dev/api")
        wa_token = os.getenv("WA_API_TOKEN", "dev-token")
        self.whatsapp_dispatcher = WhatsAppDispatcher(wa_url, wa_token)
        self.dispatchers = {
            "rocketchat": self._send_rocketchat,
            "email": self._send_email,
            "sms": self._send_sms,
            "whatsapp": self._send_whatsapp
        }
    def _send_email(self, payload: dict) -> dict:
        return self.email_dispatcher.send_email(
            to=payload.get("recipient"),
            subject=payload.get("metadata", {}).get("subject", "Mensagem IntelliCare"),
            body=payload.get("content")
        )

    def _send_sms(self, payload: dict) -> dict:
        return self.sms_dispatcher.send_sms(
            to=payload.get("recipient"),
            text=payload.get("content")
        )

    def _send_whatsapp(self, payload: dict) -> dict:
        return self.whatsapp_dispatcher.send_whatsapp(
            to=payload.get("recipient"),
            text=payload.get("content")
        )

    def dispatch(self, channel: str, payload: dict) -> dict:
        if channel not in self.dispatchers:
            raise ValueError(f"Canal não suportado: {channel}")
        return self.dispatchers[channel](payload)

    def _send_rocketchat(self, payload: dict) -> dict:
        # Integra com RocketChatDispatcher real
        return self.rocketchat_dispatcher.send_message(
            channel=payload.get("channel"),
            text=payload.get("content"),
            recipient=payload.get("recipient")
        )
