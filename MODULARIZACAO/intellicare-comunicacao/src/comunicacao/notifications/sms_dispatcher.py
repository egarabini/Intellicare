class SMSDispatcher:
    """
    Dispatcher para envio de SMS (stub, integrar com gateway real).
    """
    def __init__(self, provider_url: str, api_key: str):
        self.provider_url = provider_url
        self.api_key = api_key

    def send_sms(self, to: str, text: str) -> dict:
        # TODO: integrar com gateway real
        return {"status": "queued", "to": to, "provider": self.provider_url}
