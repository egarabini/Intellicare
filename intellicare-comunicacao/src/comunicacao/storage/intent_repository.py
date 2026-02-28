from typing import Dict, List

class CommunicationIntentRepository:
    """
    Repositório de intents de comunicação (stub, persistência real via DB).
    """
    def __init__(self):
        self._intents = []

    def save_intent(self, intent: Dict) -> str:
        intent_id = f"intent-{len(self._intents)+1}"
        intent["intent_id"] = intent_id
        self._intents.append(intent)
        return intent_id

    def list_intents(self) -> List[Dict]:
        return self._intents
