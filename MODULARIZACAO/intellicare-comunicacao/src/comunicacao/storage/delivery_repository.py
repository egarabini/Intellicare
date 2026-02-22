from typing import Dict, List

class DeliveryResultRepository:
    """
    Repositório de resultados de entrega (stub, persistência real via DB).
    """
    def __init__(self):
        self._results = []

    def save_result(self, result: Dict) -> str:
        result_id = f"delivery-{len(self._results)+1}"
        result["delivery_id"] = result_id
        self._results.append(result)
        return result_id

    def get_result(self, message_id: str) -> Dict:
        for r in self._results:
            if r.get("message_id") == message_id:
                return r
        return {"message_id": message_id, "status": "unknown"}
