import requests
from typing import Dict

class RocketChatDispatcher:
    """
    Dispatcher para envio de mensagens via Rocket.Chat API.
    """
    def __init__(self, base_url: str, bot_token: str):
        self.base_url = base_url.rstrip("/")
        self.bot_token = bot_token

    def send_message(self, channel: str, text: str, recipient: str = None, **kwargs) -> Dict:
        url = f"{self.base_url}/api/v1/chat.postMessage"
        headers = {
            "X-Auth-Token": self.bot_token,
            "X-User-Id": kwargs.get("bot_user_id", ""),
            "Content-type": "application/json"
        }
        payload = {
            "channel": channel,
            "text": text
        }
        if recipient:
            payload["alias"] = recipient
        # Para ambiente de DEV, simular resposta
        if self.base_url.startswith("http://localhost"):
            return {"status": "queued", "message_id": "msg-rc-dev-001"}
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return {"status": "sent", "message_id": data.get("message", {}).get("_id", "")}
        else:
            return {"status": "error", "message_id": None, "error": resp.text}
