class WhatsAppDispatcher:
    """
    Dispatcher para envio de mensagens WhatsApp (stub, integrar com API real).
    """
    def __init__(self, api_url: str, token: str):
        self.api_url = api_url
        self.token = token

    def send_whatsapp(self, to: str, text: str) -> dict:
        # TODO: integrar com API real
        return {"status": "queued", "to": to, "provider": self.api_url}
